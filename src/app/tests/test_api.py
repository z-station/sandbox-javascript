from app.entities import DebugData, RunData, TestData, TestsData
from app.service.exceptions import ServiceException


def test_health__ok(client):
    response = client.get('/health')

    assert response.status_code == 200
    assert response.json == {'status': 'ok'}


def test_run__ok(client, mocker):
    request_data = {
        'code': 'console.log("Hello from JS")'
    }
    serialized_data = RunData(
        code='console.log("Hello from JS")'
    )
    run_result = RunData(
        code='console.log("Hello from JS")',
        stdout='Hello from JS\n',
        stderr='',
        exit_code=0
    )
    run_mock = mocker.patch(
        'app.service.main.JavaScriptService.run',
        return_value=run_result
    )

    response = client.post('/run', json=request_data)

    assert response.status_code == 200
    assert response.json['stdout'] == run_result.stdout
    assert response.json['stderr'] == run_result.stderr
    assert response.json['exit_code'] == run_result.exit_code
    run_mock.assert_called_once_with(serialized_data)


def test_run__validation_error__bad_request(client, mocker):
    request_data = {}
    service_mock = mocker.patch('app.service.main.JavaScriptService.run')

    response = client.post('/run', json=request_data)

    assert response.status_code == 400
    assert response.json['error'] == 'Validation error'
    assert response.json['details'] == {
        'code': ['Missing data for required field.']
    }
    service_mock.assert_not_called()


def test_debug__ok(client, mocker):
    request_data = {
        'code': 'console.log("some result")',
        'data_in': 'some input'
    }
    serialized_data = DebugData(
        code='console.log("some result")',
        data_in='some input'
    )
    debug_result = DebugData(
        result='some result',
        error=None,
        exit_code=0
    )
    debug_mock = mocker.patch(
        'app.service.main.JavaScriptService.debug',
        return_value=debug_result
    )

    response = client.post('/debug/', json=request_data)

    assert response.status_code == 200
    assert response.json['result'] == debug_result.result
    assert response.json['error'] is None
    assert response.json['exit_code'] == debug_result.exit_code
    debug_mock.assert_called_once_with(serialized_data)


def test_debug__service_exception__internal_error(client, mocker):
    request_data = {
        'code': 'some code',
        'data_in': 'some input'
    }
    service_ex = ServiceException(
        message='some message',
        details='some details'
    )
    mocker.patch(
        'app.service.main.JavaScriptService.debug',
        side_effect=service_ex
    )

    response = client.post('/debug/', json=request_data)

    assert response.status_code == 500
    assert response.json['error'] == service_ex.message
    assert response.json['details'] == service_ex.details


def test_debug__validation_error__bad_request(client, mocker):
    request_data = {
        'data_in': 'some input'
    }
    service_mock = mocker.patch('app.service.main.JavaScriptService.debug')

    response = client.post('/debug/', json=request_data)

    assert response.status_code == 400
    assert response.json['error'] == 'Validation error'
    assert response.json['details'] == {
        'code': ['Missing data for required field.']
    }
    service_mock.assert_not_called()


def test_testing__ok(client, mocker):
    request_data = {
        'code': 'some code',
        'checker': 'some func',
        'tests': [
            {
                'data_in': 'some test input',
                'data_out': 'some test out'
            }
        ]
    }
    serialized_data = TestsData(
        code='some code',
        checker='some func',
        tests=[
            TestData(
                data_in='some test input',
                data_out='some test out'
            )
        ]
    )
    testing_result = TestsData(
        ok=True,
        num=1,
        num_ok=1,
        tests=[
            TestData(
                result='some result',
                error=None,
                exit_code=0,
                ok=True
            )
        ]
    )
    testing_mock = mocker.patch(
        'app.service.main.JavaScriptService.testing',
        return_value=testing_result
    )

    response = client.post('/testing/', json=request_data)

    assert response.status_code == 200
    assert response.json['ok'] == testing_result.ok
    assert response.json['num'] == testing_result.num
    assert response.json['num_ok'] == testing_result.num_ok
    assert response.json['tests'][0]['result'] == 'some result'
    assert response.json['tests'][0]['error'] is None
    assert response.json['tests'][0]['exit_code'] == 0
    assert response.json['tests'][0]['ok'] is True
    testing_mock.assert_called_once_with(serialized_data)


def test_testing__validation_error__bad_request(client, mocker):
    request_data = {
        'code': 'some code',
        'tests': [
            {
                'data_in': 'some test input',
                'data_out': 'some test out'
            }
        ]
    }
    service_mock = mocker.patch('app.service.main.JavaScriptService.testing')

    response = client.post('/testing/', json=request_data)

    assert response.status_code == 400
    assert response.json['error'] == 'Validation error'
    assert response.json['details'] == {
        'checker': ['Missing data for required field.']
    }
    service_mock.assert_not_called()

