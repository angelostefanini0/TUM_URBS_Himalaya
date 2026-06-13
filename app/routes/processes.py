from flask import Blueprint, current_app, request

from app.utils.responses import api_error, api_success


processes = Blueprint('processes', __name__)


def add_technology(technology):
    payload = request.get_json(silent=True) or {}
    if payload.get('action') != technology:
        return api_error('Invalid technology action.', 400)
    try:
        name = current_app.extensions['process_service'].add_template(technology)
        return api_success(process=name)
    except (ValueError, FileNotFoundError, IndexError) as exc:
        return api_error(str(exc), 400)
    except Exception as exc:
        current_app.logger.exception('Technology selection failed')
        return api_error(str(exc), 500)


@processes.post('/process_hydro')
def hydro():
    return add_technology('hydro')


@processes.post('/process_solar')
def solar():
    return add_technology('solar')


@processes.post('/process_wind')
def wind():
    return add_technology('wind')


@processes.post('/process_gasplant')
def gas():
    return add_technology('gasplant')


@processes.post('/process_ligniteplant')
def lignite():
    return add_technology('ligniteplant')


@processes.post('/save_process_data')
def custom():
    try:
        payload = request.get_json(silent=True) or request.form
        name = current_app.extensions['process_service'].add_custom(payload)
        return api_success(process=name)
    except ValueError as exc:
        return api_error(str(exc), 400)
    except Exception as exc:
        current_app.logger.exception('Custom process creation failed')
        return api_error(str(exc), 500)


@processes.post('/move_files')
def prepare():
    try:
        names = current_app.extensions['process_service'].prepare()
        return api_success(processes=names)
    except (FileNotFoundError, ValueError) as exc:
        return api_error(str(exc), 400)
    except Exception as exc:
        current_app.logger.exception('URBS process preparation failed')
        return api_error(str(exc), 500)

