from flask import Blueprint, current_app, redirect, render_template, url_for

from app.utils.responses import api_error


urbs = Blueprint('urbs', __name__)


@urbs.post('/runurbs')
def run():
    try:
        current_app.extensions['process_service'].prepare()
        result = current_app.extensions['urbs_service'].run()
        return redirect(url_for(
            'main.results_ready',
            message=f'Optimization completed: {result.name}',
        ))
    except (FileNotFoundError, ValueError) as exc:
        return render_template('runurbs.html', error=str(exc), active_step=4), 400
    except Exception as exc:
        current_app.logger.exception('URBS execution failed')
        message = str(exc)
        if 'feasible solution was not found' in message.lower():
            message = (
                'The selected technologies cannot satisfy demand for every '
                'modeled hour. Review capacities and commodity relationships.'
            )
        return render_template('runurbs.html', error=message[-1800:], active_step=4), 500


@urbs.post('/urbsresults')
def show_results():
    try:
        archive = current_app.extensions['urbs_service'].create_zip()
        return render_template(
            'results.html',
            image_filename='elec_in_mid.png',
            zip_filename=archive.name,
            active_step=5,
        )
    except Exception as exc:
        current_app.logger.exception('Result packaging failed')
        return api_error(str(exc), 500)
