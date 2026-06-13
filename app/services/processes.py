from pathlib import Path

from app.utils.files import append_json, load_json, read_excel, write_json


PROCESS_ROWS = {
    'hydro': (0, (0, 1)),
    'solar': (1, (4, 5)),
    'wind': (8, (2, 3)),
    'gasplant': (3, (6, 7, 8)),
    'ligniteplant': (9, (12, 13)),
}


class ProcessService:
    def __init__(self, process_template, relation_template, process_selection,
                 relation_selection, json_dir):
        self.process_template = Path(process_template)
        self.relation_template = Path(relation_template)
        self.process_selection = Path(process_selection)
        self.relation_selection = Path(relation_selection)
        self.json_dir = Path(json_dir)
        self.standard_processes = self.json_dir / 'standard.json'
        self.commodities = self.json_dir / 'commodity.json'

    def reset(self):
        self.process_selection.unlink(missing_ok=True)
        self.relation_selection.unlink(missing_ok=True)

    def add_template(self, technology):
        if technology not in PROCESS_ROWS:
            raise ValueError(f'Unknown technology: {technology}')
        processes = read_excel(self.process_template)
        relations = read_excel(self.relation_template)
        process_index, relation_indices = PROCESS_ROWS[technology]
        process = processes.iloc[process_index].to_dict()
        process = self._canonical_process(process)
        append_json(self.process_selection, process)
        for index in relation_indices:
            relation = relations.iloc[index].to_dict()
            relation['support_timeframe'] = 2020
            append_json(self.relation_selection, relation)
        return process['Process']

    def _canonical_process(self, process):
        """Replace malformed spreadsheet rows with canonical URBS definitions."""
        if not self.standard_processes.exists():
            return process
        canonical = {
            row['Process']: row
            for row in load_json(self.standard_processes)
        }
        return canonical.get(process.get('Process'), process).copy()

    def _validate_commodities(self, processes, relations):
        commodity_rows = load_json(self.commodities)
        process_sites = {
            row['Process']: (
                int(row.get('support_timeframe', 2020)),
                row['Site'],
            )
            for row in processes
        }
        commodity_keys = {
            (
                int(row.get('support_timeframe', 2020)),
                row['Site'],
                row['Commodity'],
            )
            for row in commodity_rows
        }
        missing = set()
        for relation in relations:
            process = relation['Process']
            if process not in process_sites:
                raise ValueError(
                    f'Process relation references unknown process: {process}.'
                )
            timeframe, site = process_sites[process]
            key = (timeframe, site, relation['Commodity'])
            if key not in commodity_keys:
                missing.add(key)

        unresolved = []
        for timeframe, site, commodity in sorted(missing):
            if commodity == 'CO2':
                commodity_rows.append({
                    'support_timeframe': timeframe,
                    'Site': site,
                    'Commodity': 'CO2',
                    'Type': 'Env',
                    'price': 0,
                    'max': float('inf'),
                    'maxperhour': float('inf'),
                })
            else:
                unresolved.append(f'{site}/{commodity}')
        if unresolved:
            raise ValueError(
                'Missing commodity definitions: ' + ', '.join(unresolved)
            )
        if missing:
            write_json(self.commodities, commodity_rows)

    def add_custom(self, payload):
        if not payload.get('site') or not payload.get('process'):
            raise ValueError('Site and process name are required.')

        def number(name, default=0.0):
            value = payload.get(name)
            return default if value in (None, '') else float(value)

        process = {
            'Site': payload['site'],
            'Process': payload['process'],
            'inst-cap': number('inst-cap'),
            'cap-lo': number('cap-lo'),
            'cap-up': number('cap-up'),
            'max-grad': float('inf') if payload.get('max-grad') == 'Infinity'
                        else number('max-grad'),
            'min-fraction': number('min-fraction'),
            'inv-cost': number('inv-cost'),
            'fix-cost': number('fix-cost'),
            'var-cost': number('var-cost'),
            'wacc': number('wacc'),
            'depreciation': number('depreciation'),
            'area-per-cap': number('area-per-cap', float('nan')),
            'support_timeframe': int(payload.get('support_timeframe') or 2020),
        }
        append_json(self.process_selection, process)
        return process['Process']

    def prepare(self):
        if not self.process_selection.exists() or not self.relation_selection.exists():
            raise FileNotFoundError(
                'Select at least one generation technology before continuing.'
            )
        selected_processes = load_json(self.process_selection)
        selected_relations = load_json(self.relation_selection)
        if not selected_processes:
            raise ValueError('No generation technologies were selected.')

        processes = read_excel(self.process_template)
        relations = read_excel(self.relation_template)
        slack = processes.iloc[9].to_dict()
        slack_relations = relations.iloc[[12, 13]].to_dict('records')
        for relation in slack_relations:
            relation['support_timeframe'] = 2020
        selected_processes = [
            self._canonical_process(process) for process in selected_processes
        ]
        for process in selected_processes:
            if process.get('Process') in {'Photovoltaics', 'Wind park', 'Hydro plant'}:
                process['cap-lo'] = 0

        process_rows = {
            row['Process']: row for row in [*selected_processes, slack]
        }
        relation_rows = {
            (row['Process'], row['Commodity'], row['Direction']): row
            for row in [*selected_relations, *slack_relations]
        }
        final_processes = list(process_rows.values())
        final_relations = list(relation_rows.values())
        self._validate_commodities(final_processes, final_relations)
        write_json(self.json_dir / 'process.json', final_processes)
        write_json(
            self.json_dir / 'process_commodity.json',
            final_relations,
        )
        return sorted(process_rows)
