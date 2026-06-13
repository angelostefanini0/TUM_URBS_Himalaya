import requests
from flask import Blueprint, current_app, request

from app.utils.responses import api_error, api_success


renewables = Blueprint('renewables', __name__)


@renewables.post('/api/renewables')
def fetch_renewables():
    payload = request.get_json(silent=True) or {}
    try:
        warning = current_app.extensions['renewable_service'].fetch(
            payload.get('lat'),
            payload.get('lon'),
        )
        return api_success(
            message='Renewable profiles downloaded.',
            pv_json_file='pv_data.json',
            wind_json_file='wind_data.json',
            warning=warning,
        )
    except ValueError as exc:
        return api_error(str(exc), 400)
    except RuntimeError as exc:
        return api_error(str(exc), 503)
    except requests.RequestException as exc:
        current_app.logger.warning('Renewables Ninja request failed: %s', exc)
        return api_error(f'Renewables Ninja request failed: {exc}', 502)
    except Exception as exc:
        current_app.logger.exception('Renewable profile generation failed')
        return api_error(str(exc), 500)


@renewables.post('/transform_files')
def transform_files():
    try:
        rows = current_app.extensions['renewable_service'].transform()
        return api_success(rows=rows)
    except FileNotFoundError:
        return api_error(
            'Renewable files are missing. Select a location and fetch data first.',
            400,
        )
    except Exception as exc:
        current_app.logger.exception('Renewable transformation failed')
        return api_error(str(exc), 400)

