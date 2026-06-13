from flask import jsonify


def api_error(message, status=400, **details):
    payload = {'status': 'failure', 'error': message}
    payload.update(details)
    return jsonify(payload), status


def api_success(**payload):
    return jsonify({'status': 'success', **payload})

