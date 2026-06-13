import logging
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from app.utils.files import read_excel


logger = logging.getLogger(__name__)


class UrbsService:
    def __init__(self, project_root, urbs_dir, results_dir, static_images_dir,
                 legacy_images_dir, venv_python, solver):
        self.project_root = Path(project_root)
        self.urbs_dir = Path(urbs_dir)
        self.results_dir = Path(results_dir)
        self.static_images_dir = Path(static_images_dir)
        self.legacy_images_dir = Path(legacy_images_dir)
        self.venv_python = Path(venv_python)
        self.solver = solver

    def latest_result(self):
        folders = [
            path for path in self.results_dir.iterdir()
            if path.is_dir() and path.name.startswith('single-year')
        ]
        return max(folders, key=lambda path: path.stat().st_mtime, default=None)

    def run(self):
        executable = self.venv_python if self.venv_python.exists() else Path(sys.executable)
        environment = dict(__import__('os').environ)
        environment['URBS_SOLVER'] = self.solver
        completed = subprocess.run(
            [str(executable), str(self.urbs_dir / 'run_single_year.py')],
            cwd=self.project_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=900,
        )
        if completed.returncode:
            details = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(details[-6000:] or 'URBS exited without an error message.')
        logger.info('URBS completed: %s', completed.stdout[-1000:])
        self.copy_plots()
        self.create_summary_plot()
        return self.latest_result()

    def copy_plots(self):
        result = self.latest_result()
        if result is None:
            raise FileNotFoundError('No URBS result folder was generated.')
        self.static_images_dir.mkdir(parents=True, exist_ok=True)
        self.legacy_images_dir.mkdir(parents=True, exist_ok=True)
        for source in result.glob('*Mid*.png'):
            shutil.copy2(source, self.static_images_dir / source.name)
            shutil.copy2(source, self.legacy_images_dir / source.name)

    def create_summary_plot(self):
        result = self.latest_result()
        file_path = result / 'scenario_base.xlsx'
        sheet = '2020.Mid.Elec timeseries'
        header = read_excel(file_path, sheet_name=sheet, header=None, nrows=2)
        frame = read_excel(file_path, sheet_name=sheet, header=None, skiprows=3)
        frame.columns = header.iloc[1].tolist()
        frame.set_index(frame.columns[0], inplace=True)
        columns = [
            name for name in (
                'Photovoltaics', 'Wind park', 'Hydro plant', 'Slack powerplant'
            ) if name in frame.columns
        ]
        technology_colors = {
            'Photovoltaics': '#f3ae00',
            'Wind park': '#38bdf8',
            'Hydro plant': '#2563eb',
            'Slack powerplant': '#64748b',
        }
        plt.figure(figsize=(14, 8))
        if columns:
            plt.stackplot(
                frame.index,
                *[frame[column] for column in columns],
                labels=columns,
                colors=[technology_colors[column] for column in columns],
            )
        if 'Demand' in frame.columns:
            plt.plot(frame.index, frame['Demand'], color='#0f172a', label='Demand')
        plt.xlabel('Time in hours')
        plt.ylabel('Power (kW)')
        plt.title('Electricity supply and demand at Mid')
        plt.legend(loc='upper right')
        plt.grid(alpha=0.2)
        plt.tight_layout()
        for directory in (self.static_images_dir, self.legacy_images_dir):
            directory.mkdir(parents=True, exist_ok=True)
            plt.savefig(directory / 'elec_in_mid.png', dpi=150)
        plt.close()

    def create_zip(self):
        destination = self.results_dir / 'results.zip'
        with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in self.results_dir.rglob('*'):
                if path.is_file() and path != destination:
                    archive.write(path, path.relative_to(self.results_dir))
        return destination
