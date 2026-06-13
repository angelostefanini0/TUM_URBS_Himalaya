from pathlib import Path

from flask import Blueprint, current_app, jsonify, redirect, request, session, url_for
from werkzeug.utils import secure_filename

from app.utils.responses import api_error, api_success


demand = Blueprint('demand', __name__)
ALLOWED_UPLOADS = {'.xlsx', '.xls'}


@demand.get('/get_chart_data')
def chart_data():
    try:
        return jsonify(current_app.extensions['demand_service'].chart_data())
    except Exception as exc:
        current_app.logger.exception('Could not load demand chart data')
        return api_error(str(exc), 500)


@demand.post('/calculate')
def calculate():
    service = current_app.extensions['demand_service']
    category = request.form.get('commodity', '').strip()
    try:
        quantity = int(request.form.get('quantity', ''))
        if category not in service.categories:
            raise ValueError('Select a valid community category.')
        if not 1 <= quantity <= 10000:
            raise ValueError('Quantity must be between 1 and 10,000.')
        quantities = dict(session.get('commodities', {}))
        quantities[category] = quantities.get(category, 0) + quantity
        session['commodities'] = quantities
        total = service.calculate(quantities)
        session['total_demand'] = total
        return api_success(total_demand=total, selections=quantities)
    except (TypeError, ValueError, FileNotFoundError) as exc:
        return api_error(str(exc), 400)
    except Exception as exc:
        current_app.logger.exception('Demand calculation failed')
        return api_error(str(exc), 500)


@demand.post('/upload_and_sum')
def upload_and_sum():
    upload = request.files.get('file')
    if upload is None or not upload.filename:
        return api_error('Choose an Excel file to upload.', 400)
    filename = secure_filename(upload.filename)
    if Path(filename).suffix.lower() not in ALLOWED_UPLOADS:
        return api_error('Only .xlsx and .xls files are supported.', 400)
    destination = current_app.config['JSON_DIR'] / filename
    try:
        upload.save(destination)
        total = current_app.extensions['demand_service'].sum_upload(destination)
        return redirect(url_for('main.demand_page', sum_result=total))
    except Exception as exc:
        current_app.logger.exception('Demand upload failed')
        return api_error(f'Could not read the uploaded workbook: {exc}', 400)


@demand.route('/generate_json', methods=['GET', 'POST'])
def generate_json():
    try:
        destination = current_app.config['JSON_DIR'] / 'demand.json'
        count = current_app.extensions['demand_service'].generate_json(destination)
        current_app.extensions['process_service'].reset()
        if request.method == 'GET':
            return redirect(url_for('main.process_page'))
        return api_success(rows=count, next_url=url_for('main.process_page'))
    except Exception as exc:
        current_app.logger.exception('Demand JSON generation failed')
        return api_error(str(exc), 400)


@demand.post('/reset_total_series')
def reset():
    try:
        session['commodities'] = {}
        current_app.extensions['demand_service'].reset()
        return api_success()
    except Exception as exc:
        current_app.logger.exception('Demand reset failed')
        return api_error(str(exc), 500)

