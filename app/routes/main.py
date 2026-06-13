from flask import Blueprint, current_app, render_template, request, send_from_directory


main = Blueprint('main', __name__)


@main.get('/')
def index():
    return render_template('index.html')


@main.get('/map')
def map_page():
    return render_template('map.html', active_step=1)


@main.get('/demand')
def demand_page():
    return render_template(
        'demand.html',
        categories=current_app.extensions['demand_service'].categories,
        sum_result=request.args.get('sum_result', type=float),
        active_step=2,
    )


@main.get('/process')
def process_page():
    return render_template('process.html', active_step=3)


@main.get('/runurbs')
def run_page():
    return render_template('runurbs.html', active_step=4)


@main.get('/urbsresults')
def results_ready():
    return render_template(
        'urbsresult.html',
        message=request.args.get('message'),
        active_step=5,
    )


@main.get('/downloads/<path:filename>')
def download_input(filename):
    return send_from_directory(
        current_app.config['JSON_DIR'],
        filename,
        as_attachment=True,
    )


@main.get('/download/<path:filename>')
def download_result(filename):
    return send_from_directory(
        current_app.config['RESULTS_DIR'],
        filename,
        as_attachment=True,
    )

