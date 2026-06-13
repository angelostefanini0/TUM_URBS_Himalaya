import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import requests

from app.utils.files import load_json, write_json


class RenewableService:
    API_BASE = 'https://www.renewables.ninja/api/data'

    def __init__(self, token, json_dir, hydro_service, image_dir=None):
        self.token = token
        self.json_dir = Path(json_dir)
        self.hydro_service = hydro_service
        self.image_dir = Path(image_dir) if image_dir else None

    @staticmethod
    def validate_coordinates(latitude, longitude):
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError) as exc:
            raise ValueError('Latitude and longitude must be numbers.') from exc
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError('Coordinates are outside the valid range.')
        return latitude, longitude

    def _request(self, resource, params):
        if not self.token:
            raise RuntimeError('RENEWABLES_NINJA_TOKEN is not configured.')
        response = requests.get(
            f'{self.API_BASE}/{resource}',
            params=params,
            headers={'Authorization': f'Token {self.token}'},
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        if 'data' not in payload:
            raise RuntimeError(f'Renewables Ninja returned no {resource} data.')
        return payload['data']

    def fetch(self, latitude, longitude):
        latitude, longitude = self.validate_coordinates(latitude, longitude)
        warning = None
        try:
            average, discharge = self.hydro_service.estimate(latitude, longitude)
        except Exception:
            average = 0.0
            discharge = self.hydro_service.discharge_series(0)
            warning = 'River data is unavailable; hydro availability was set to zero.'

        discharge_json = discharge.to_json(orient='split', date_format='iso')
        write_json(self.json_dir / 'avg_q.json', {
            'DIS_AV_CMS': average,
            'discharge_timeseries': discharge_json,
        })
        if self.image_dir:
            self.image_dir.mkdir(parents=True, exist_ok=True)
            plt.figure(figsize=(13, 5))
            plt.plot(discharge.index, discharge['discharge'], color='#1457d9')
            plt.fill_between(
                discharge.index,
                discharge['discharge'],
                color='#21c5d9',
                alpha=0.18,
            )
            plt.xlabel('Date')
            plt.ylabel('Discharge (m³/s)')
            plt.title('Estimated hourly river discharge')
            plt.grid(alpha=0.2)
            plt.tight_layout()
            plt.savefig(self.image_dir / 'discharge_timeseries_plot.png', dpi=140)
            plt.close()

        common = {
            'lat': latitude,
            'lon': longitude,
            'date_from': '2023-01-01',
            'date_to': '2023-12-31',
            'capacity': 1.0,
            'format': 'json',
        }
        pv = self._request('pv', {
            **common, 'dataset': 'merra2', 'system_loss': 0.1,
            'tracking': 0, 'tilt': 35, 'azim': 180,
        })
        wind = self._request('wind', {
            **common, 'height': 100, 'turbine': 'Vestas V80 2000',
        })
        pd.DataFrame.from_dict(pv).to_json(self.json_dir / 'pv_data.json')
        pd.DataFrame.from_dict(wind).to_json(self.json_dir / 'wind_data.json')
        return warning

    def transform(self):
        wind = load_json(self.json_dir / 'wind_data.json')
        pv = load_json(self.json_dir / 'pv_data.json')
        average = load_json(self.json_dir / 'avg_q.json')
        discharge_payload = json.loads(average['discharge_timeseries'])
        discharge = pd.DataFrame(
            discharge_payload['data'],
            columns=discharge_payload['columns'],
            index=discharge_payload['index'],
        )
        timestamps = list(wind)
        if not timestamps or set(timestamps) != set(pv):
            raise ValueError('Solar and wind profiles are empty or misaligned.')
        if len(discharge) < len(timestamps):
            raise ValueError('Hydro profile is shorter than renewable profiles.')

        maximum = float(discharge['discharge'].max())
        rows = []
        for index, timestamp in enumerate(timestamps):
            hydro = float(discharge.iloc[index]['discharge'])
            hydro = hydro / maximum * 0.1 if maximum > 0 else 0.0
            rows.append({
                'support_timeframe': 2020,
                't': index,
                'Mid': {
                    'Wind': float(wind[timestamp]['electricity']),
                    'Solar': float(pv[timestamp]['electricity']),
                    'Hydro': hydro,
                },
            })
        write_json(self.json_dir / 'supim.json', rows)
        return len(rows)
