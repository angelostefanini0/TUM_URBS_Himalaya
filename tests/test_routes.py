from run import app


def test_primary_pages_render():
    client = app.test_client()
    for path in ('/', '/map', '/demand', '/process', '/runurbs', '/urbsresults'):
        assert client.get(path).status_code == 200


def test_invalid_coordinates_return_json_error():
    response = app.test_client().post(
        '/api/renewables',
        json={'lat': 'invalid', 'lon': 80},
    )
    assert response.status_code == 400
    assert response.get_json()['status'] == 'failure'


def test_missing_demand_fields_return_json_error():
    response = app.test_client().post('/calculate', data={})
    assert response.status_code == 400
    assert response.get_json()['status'] == 'failure'
