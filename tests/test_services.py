import json

import pandas as pd
import pytest
import pyomo.environ as pyomo

from app.services.demand import DemandService
from app.services.hydro import HydroService
from app.services.processes import ProcessService
from app.services.renewables import RenewableService
from app.utils.files import load_json, write_json
from urbs_master.urbs.model import res_env_step_rule, res_env_total_rule


def test_coordinate_validation():
    assert RenewableService.validate_coordinates('28.5', '83.1') == (28.5, 83.1)
    with pytest.raises(ValueError):
        RenewableService.validate_coordinates(95, 83)
    with pytest.raises(ValueError):
        RenewableService.validate_coordinates('north', 83)


def test_zero_discharge_profile_is_hourly_and_deterministic():
    profile = HydroService.discharge_series(0)
    assert len(profile) == 8760
    assert profile['discharge'].sum() == 0


def test_json_round_trip(tmp_path):
    path = tmp_path / 'data.json'
    write_json(path, [{'value': 3}])
    assert load_json(path) == [{'value': 3}]


def test_demand_calculation_combines_profiles(tmp_path, monkeypatch):
    data_dir = tmp_path / 'demand'
    data_dir.mkdir()
    output = tmp_path / 'total.xlsx'
    service = DemandService(data_dir, output)
    monkeypatch.setattr(service, 'validate_files', lambda: None)
    monkeypatch.setattr(
        service,
        'profile',
        lambda category: pd.Series([1.0, 2.0, 3.0]),
    )
    total = service.calculate({'School': 2, 'Low-income Household': 1})
    assert total == 18
    assert pd.read_excel(output)['Total'].tolist() == [3, 6, 9]


def test_renewable_transform_preserves_urbs_json_shape(tmp_path):
    hydro = HydroService(tmp_path / 'unused.shp')
    service = RenewableService('token', tmp_path, hydro)
    write_json(tmp_path / 'wind_data.json', {
        '0': {'electricity': 0.2},
        '1': {'electricity': 0.3},
    })
    write_json(tmp_path / 'pv_data.json', {
        '0': {'electricity': 0.1},
        '1': {'electricity': 0.4},
    })
    discharge = pd.DataFrame({'discharge': [2.0, 4.0]})
    write_json(tmp_path / 'avg_q.json', {
        'DIS_AV_CMS': 4,
        'discharge_timeseries': discharge.to_json(orient='split'),
    })
    assert service.transform() == 2
    rows = json.loads((tmp_path / 'supim.json').read_text())
    assert rows[0] == {
        'support_timeframe': 2020,
        't': 0,
        'Mid': {'Wind': 0.2, 'Solar': 0.1, 'Hydro': 0.05},
    }


def test_process_prepare_repairs_gas_and_adds_co2_commodity(
        tmp_path, monkeypatch):
    json_dir = tmp_path / 'json'
    json_dir.mkdir()
    process_selection = tmp_path / 'process.json'
    relation_selection = tmp_path / 'relations.json'
    write_json(process_selection, [{
        'support_timeframe': 2020, 'Site': 'Mid', 'Process': 'Gas plant',
        'cap-up': 0,
    }])
    write_json(relation_selection, [
        {'support_timeframe': 2020, 'Process': 'Gas plant',
         'Commodity': 'Gas', 'Direction': 'In', 'ratio': 1},
        {'support_timeframe': 2020, 'Process': 'Gas plant',
         'Commodity': 'CO2', 'Direction': 'Out', 'ratio': 0.2},
    ])
    write_json(json_dir / 'standard.json', [{
        'support_timeframe': 2020, 'Site': 'Mid', 'Process': 'Gas plant',
        'cap-up': 80000,
    }])
    write_json(json_dir / 'commodity.json', [
        {'support_timeframe': 2020, 'Site': 'Mid', 'Commodity': 'Gas',
         'Type': 'Stock'},
        {'support_timeframe': 2020, 'Site': 'Mid', 'Commodity': 'Slack',
         'Type': 'Stock'},
        {'support_timeframe': 2020, 'Site': 'Mid', 'Commodity': 'Elec',
         'Type': 'Demand'},
    ])
    process_templates = pd.DataFrame([
        {'Process': 'unused'} for _ in range(9)
    ] + [{
        'support_timeframe': 2020, 'Site': 'Mid',
        'Process': 'Slack powerplant',
    }])
    relation_templates = pd.DataFrame([
        {'Process': 'unused', 'Commodity': 'unused', 'Direction': 'In'}
        for _ in range(12)
    ] + [
        {'Process': 'Slack powerplant', 'Commodity': 'Slack',
         'Direction': 'In'},
        {'Process': 'Slack powerplant', 'Commodity': 'Elec',
         'Direction': 'Out'},
    ])
    monkeypatch.setattr(
        'app.services.processes.read_excel',
        lambda path: (
            process_templates if str(path).endswith('process.xlsx')
            else relation_templates
        ),
    )
    service = ProcessService(
        tmp_path / 'process.xlsx', tmp_path / 'relations.xlsx',
        process_selection, relation_selection, json_dir,
    )

    service.prepare()

    processes = load_json(json_dir / 'process.json')
    commodities = load_json(json_dir / 'commodity.json')
    assert next(row for row in processes if row['Process'] == 'Gas plant')[
        'cap-up'
    ] == 80000
    assert any(
        row['Commodity'] == 'CO2' and row['Type'] == 'Env'
        for row in commodities
    )


def test_unlimited_environmental_commodity_skips_constraints():
    class Model:
        com_env = {'CO2'}
        commodity_dict = {
            'maxperhour': {(2020, 'Mid', 'CO2', 'Env'): float('inf')},
            'max': {(2020, 'Mid', 'CO2', 'Env'): float('inf')},
        }

    model = Model()
    assert res_env_step_rule(
        model, 1, 2020, 'Mid', 'CO2', 'Env'
    ) is pyomo.Constraint.Skip
    assert res_env_total_rule(
        model, 2020, 'Mid', 'CO2', 'Env'
    ) is pyomo.Constraint.Skip
