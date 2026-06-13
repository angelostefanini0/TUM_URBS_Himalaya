import logging
import os

import matplotlib
matplotlib.use('Agg')
from flask import Flask

from app.config import Config
from app.routes import BLUEPRINTS
from app.services import (
    DemandService,
    HydroService,
    ProcessService,
    RenewableService,
    UrbsService,
)
from app.utils.files import ensure_directories


def create_app(config_object=Config):
    os.environ.setdefault('SHAPE_RESTORE_SHX', 'YES')
    app = Flask(__name__)
    app.config.from_object(config_object)

    logging.basicConfig(
        level=logging.DEBUG if app.config.get('DEBUG') else logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    ensure_directories(
        app.config['JSON_DIR'],
        app.config['RESULTS_DIR'],
        app.config['STATIC_IMAGES_DIR'],
        app.config['LEGACY_STATIC_IMAGES_DIR'],
    )

    demand_service = DemandService(
        app.config['DEMAND_DATA_DIR'],
        app.config['TOTAL_DEMAND_FILE'],
    )
    hydro_service = HydroService(app.config['HYDRORIVERS_PATH'])
    process_service = ProcessService(
        app.config['PROCESS_TEMPLATE_FILE'],
        app.config['PROCESS_RELATION_FILE'],
        app.config['SELECTION_PROCESS_FILE'],
        app.config['SELECTION_RELATION_FILE'],
        app.config['JSON_DIR'],
    )
    app.extensions.update({
        'demand_service': demand_service,
        'hydro_service': hydro_service,
        'renewable_service': RenewableService(
            app.config['RENEWABLES_NINJA_TOKEN'],
            app.config['JSON_DIR'],
            hydro_service,
            app.config['STATIC_IMAGES_DIR'],
        ),
        'process_service': process_service,
        'urbs_service': UrbsService(
            app.config['PROJECT_ROOT'],
            app.config['URBS_DIR'],
            app.config['RESULTS_DIR'],
            app.config['STATIC_IMAGES_DIR'],
            app.config['LEGACY_STATIC_IMAGES_DIR'],
            app.config['VENV_PYTHON'],
            app.config['URBS_SOLVER'],
        ),
    })

    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
    return app
