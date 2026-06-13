import logging

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

from app.utils.files import read_geodata, validate_shapefile


logger = logging.getLogger(__name__)


class HydroService:
    def __init__(self, shapefile_path):
        self.shapefile_path = shapefile_path
        self._data = None

    def load(self):
        if self._data is None:
            validate_shapefile(self.shapefile_path)
            data = read_geodata(self.shapefile_path)
            if 'DIS_AV_CMS' not in data.columns:
                raise ValueError('HydroRIVERS is missing the DIS_AV_CMS column.')
            if data.crs is None:
                raise ValueError('HydroRIVERS has no coordinate reference system.')
            if data.crs.is_geographic:
                data = data.to_crs(epsg=32644)
            self._data = data
        return self._data

    @staticmethod
    def discharge_series(yearly_average, year=2023):
        index = pd.date_range(
            start=f'{year}-01-01',
            end=f'{year + 1}-01-01',
            freq='h',
            inclusive='left',
        )
        if yearly_average <= 0:
            return pd.DataFrame({'discharge': np.zeros(len(index))}, index=index)
        daily = np.sin(2 * np.pi * (np.arange(1, 366) - 200) / 365) * 0.5 + 1
        hourly = np.repeat(daily, 24)
        rng = np.random.default_rng(42)
        discharge = hourly + 0.1 * rng.standard_normal(len(index))
        discharge = discharge / discharge.mean() * yearly_average
        return pd.DataFrame({'discharge': discharge}, index=index)

    def estimate(self, latitude, longitude, distance_km=5):
        data = self.load()
        point = Point(longitude, latitude)
        projected = gpd.GeoSeries([point], crs='EPSG:4326').to_crs(data.crs).iloc[0]
        nearby = data[data.intersects(projected.buffer(distance_km * 1000))]
        average = 0.0 if nearby.empty else float(nearby['DIS_AV_CMS'].max())
        return average, self.discharge_series(average)

