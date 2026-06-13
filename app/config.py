import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'development-only-secret-key')
    JSON_SORT_KEYS = False

    PROJECT_ROOT = PROJECT_ROOT
    URBS_DIR = PROJECT_ROOT / 'urbs_master'
    URBS_INPUT_DIR = URBS_DIR / 'Input'
    JSON_DIR = URBS_INPUT_DIR / 'json'
    RESULTS_DIR = PROJECT_ROOT / 'result'
    DEMAND_DATA_DIR = PROJECT_ROOT / 'demand_data'
    TOTAL_DEMAND_FILE = PROJECT_ROOT / 'new_total_demand.xlsx'
    PROCESS_TEMPLATE_FILE = PROJECT_ROOT / 'process.xlsx'
    PROCESS_RELATION_FILE = PROJECT_ROOT / 'processdemand.xlsx'
    SELECTION_PROCESS_FILE = PROJECT_ROOT / 'process.json'
    SELECTION_RELATION_FILE = PROJECT_ROOT / 'processdemand.json'
    LEGACY_STATIC_IMAGES_DIR = PROJECT_ROOT / 'static' / 'images'
    STATIC_IMAGES_DIR = PROJECT_ROOT / 'app' / 'static' / 'images'
    HYDRORIVERS_PATH = Path(
        os.environ.get('HYDRORIVERS_PATH')
        or PROJECT_ROOT / 'static' / 'hydrorivers' / 'HydroRIVERS_v10_as_clipped2_rpj.shp'
    )
    RENEWABLES_NINJA_TOKEN = os.environ.get('RENEWABLES_NINJA_TOKEN')
    URBS_SOLVER = os.environ.get('URBS_SOLVER', 'appsi_highs')
    VENV_PYTHON = PROJECT_ROOT / '.venv' / 'Scripts' / 'python.exe'
