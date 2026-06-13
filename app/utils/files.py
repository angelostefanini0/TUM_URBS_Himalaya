import json
import shutil
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd


SHAPEFILE_SIDECARS = ('.shp', '.shx', '.dbf', '.prj')


def ensure_directories(*directories):
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def read_excel(path, **kwargs):
    path = Path(path)
    try:
        return pd.read_excel(path, **kwargs)
    except OSError as exc:
        if getattr(exc, 'errno', None) != 22:
            raise
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / path.name
            shutil.copy2(path, temp_path)
            return pd.read_excel(temp_path, **kwargs)


def read_geodata(path):
    path = Path(path)
    try:
        return gpd.read_file(path)
    except OSError:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            for sidecar in path.parent.glob(f'{path.stem}.*'):
                shutil.copy2(sidecar, temp_dir / sidecar.name)
            return gpd.read_file(temp_dir / path.name)


def validate_shapefile(path):
    path = Path(path)
    missing = [
        path.with_suffix(extension).name
        for extension in SHAPEFILE_SIDECARS
        if not path.with_suffix(extension).exists()
    ]
    if missing:
        raise FileNotFoundError(
            'HydroRIVERS is incomplete. Missing: ' + ', '.join(missing)
        )


def load_json(path, default=None):
    path = Path(path)
    if not path.exists() and default is not None:
        return default
    with path.open('r', encoding='utf-8') as file:
        return json.load(file)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4, allow_nan=True)


def append_json(path, data):
    rows = load_json(path, default=[])
    rows.append(data)
    write_json(path, rows)

