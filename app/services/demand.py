from pathlib import Path

import pandas as pd

from app.utils.files import read_excel, write_json


PROFILE_FILES = {
    'Low-income Household': 'poor_household.xlsx',
    'Average-income Household': 'average_household.xlsx',
    'High-income Household': 'rich_household.xlsx',
    'Primary Health-Care Center': 'hospital.xlsx',
    'School': 'school.xlsx',
}


class DemandService:
    def __init__(self, data_dir, total_file):
        self.data_dir = Path(data_dir)
        self.total_file = Path(total_file)
        self._profiles = {}

    @property
    def categories(self):
        return list(PROFILE_FILES)

    def validate_files(self):
        missing = [
            filename for filename in PROFILE_FILES.values()
            if not (self.data_dir / filename).exists()
        ]
        if missing:
            raise FileNotFoundError(
                'Demand profile files are missing: ' + ', '.join(missing)
            )

    def profile(self, category):
        if category not in PROFILE_FILES:
            raise ValueError(f'Unknown demand category: {category}')
        if category not in self._profiles:
            path = self.data_dir / PROFILE_FILES[category]
            self._profiles[category] = read_excel(path).iloc[:, 0].fillna(0)
        return self._profiles[category]

    def calculate(self, quantities):
        self.validate_files()
        lengths = [len(self.profile(category)) for category in PROFILE_FILES]
        row_count = max(lengths)
        total = pd.Series(0.0, index=range(row_count))
        for category, quantity in quantities.items():
            series = self.profile(category).reset_index(drop=True)
            total = total.add(series * int(quantity), fill_value=0)
        frame = pd.DataFrame({'Total': total.fillna(0)})
        frame.to_excel(self.total_file, index=False)
        return float(frame['Total'].sum())

    def reset(self):
        pd.DataFrame(columns=['Total']).to_excel(self.total_file, index=False)

    def chart_data(self):
        frame = read_excel(self.total_file)
        if 'Total' not in frame:
            return {'labels': [], 'values': []}
        return {
            'labels': [f't{i}' for i in range(len(frame))],
            'values': frame['Total'].fillna(0).tolist(),
        }

    def sum_upload(self, path):
        return float(read_excel(path).iloc[:, 0].sum())

    def generate_json(self, destination):
        frame = read_excel(self.total_file)
        if 'Total' not in frame:
            raise ValueError('The demand workbook has no Total column.')
        rows = [
            {
                'support_timeframe': 2020,
                't': index,
                'Mid': {'Elec': float(total) if pd.notna(total) else 0.0},
            }
            for index, total in enumerate(frame['Total'])
        ]
        write_json(destination, rows)
        return len(rows)

