# Тесты запускать только в контейнере!
import pytest
import subprocess
from pathlib import Path
from unittest.mock import call

from app import config
from app.entities import DebugData, RunData, TestData, TestsData
from app.service import exceptions
from app.service import messages
from app.service.exceptions import CheckerException
from app.service.entities import ExecuteResult, JavaScriptFile
from app.service.main import JavaScriptService


def test_execute__number_result__ok():
    code = 'console.log(17.9 % 1)'
    file = JavaScriptFile(code)

    exec_result = JavaScriptService._execute(file=file)

    assert round(float(exec_result.stdout), 1) == 0.9
    assert exec_result.stderr == ''
    assert exec_result.exit_code == 0
    file.remove()


def test_execute__data_in_is_integer__ok():
    data_in = (
        '6\n'
        '50'
    )
    code = (
        'const fs = require("fs");\n'
        'const [n, k] = fs.readFileSync(0, "utf8").trim().split(/\\s+/).map(Number);\n'
        'console.log(Math.floor(k / n));\n'
        'console.log(k % n);'
    )
    file = JavaScriptFile(code)

    exec_result = JavaScriptService._execute(file=file, data_in=data_in)

    assert exec_result.stdout == (
        '8\n'
        '2'
    )
    assert exec_result.stderr == ''
    assert exec_result.exit_code == 0
    file.remove()


def test_execute__data_in_is_string__ok():
    data_in = 'Abrakadabra'
    code = (
        'const fs = require("fs");\n'
        'const s = fs.readFileSync(0, "utf8").trim();\n'
        'console.log(s.split("").reverse().filter((_, index) => index % 2 === 0).join(""));'
    )
    file = JavaScriptFile(code)

    exec_result = JavaScriptService._execute(
        data_in=data_in,
        file=file,
    )

    assert exec_result.stdout == 'abdkrA'
    assert exec_result.stderr == ''
    assert exec_result.exit_code == 0
    file.remove()


def test_execute__empty_result__return_empty_string():
    code = 'const test = 1'
    file = JavaScriptFile(code)

    exec_result = JavaScriptService._execute(file=file)

    assert exec_result.stdout == ''
    assert exec_result.stderr == ''
    assert exec_result.exit_code == 0
    file.remove()


def test_execute__timeout__return_error(mocker):
    code = 'while (true) {}'
    file = JavaScriptFile(code)
    mocker.patch('app.config.TIMEOUT', 1)

    execute_result = JavaScriptService._execute(file=file)

    assert execute_result.stdout == ''
    assert execute_result.stderr == messages.MSG_1
    assert execute_result.exit_code == 124
    file.remove()


def test_execute__write_access__error():
    """Тест работает только в контейнере, где ограничены права на запись."""
    code = (
        'const fs = require("fs");\n'
        'fs.writeFileSync("test.txt", "test");'
    )
    file = JavaScriptFile(code)

    exec_result = JavaScriptService._execute(file=file)

    assert 'EACCES' in exec_result.stderr or 'permission denied' in exec_result.stderr.lower()
    assert exec_result.stdout == ''
    assert exec_result.exit_code != 0
    file.remove()


def test_execute__clear_error_message__ok(mocker):
    code = 'abnabra'
    raw_error_message = (
        'ReferenceError: abnabra is not defined\n'
        '    at Object.<anonymous> (/sandbox/b7124ae0-2639-4372-a3b4-ed5752635499/main.js:1:1)\n'
        '    at Module._compile (node:internal/modules/cjs/loader:1358:14)'
    )
    clear_error_message = (
        'ReferenceError: abnabra is not defined\n'
        '    at Object.<anonymous> (main.js:1:1)\n'
        '    at Module._compile (node:internal/modules/cjs/loader:1358:14)'
    )
    file = JavaScriptFile(code)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=('', raw_error_message)
    )

    exec_result = JavaScriptService._execute(file=file)

    communicate_mock.assert_called_once_with(
        input=None,
        timeout=config.TIMEOUT,
    )
    assert exec_result.stdout == ''
    assert exec_result.stderr == clear_error_message
    file.remove()


def test_execute__proc_exception__raise_exception(mocker):
    code = 'Some code'
    data_in = 'Some data in'
    file = JavaScriptFile(code)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=Exception()
    )

    with pytest.raises(exceptions.ExecutionException) as ex:
        JavaScriptService._execute(file=file, data_in=data_in)

    assert ex.value.message == messages.MSG_6
    communicate_mock.assert_called_once_with(
        input=data_in,
        timeout=config.TIMEOUT,
    )
    file.remove()


def test_check__true__ok():
    value = 'some value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    check_result = JavaScriptService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value,
    )

    assert check_result is True


def test_check__false__ok():
    value = 'invalid value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    check_result = JavaScriptService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value,
    )

    assert check_result is False


def test_check__invalid_checker_func__raise_exception():
    checker_func = (
        'def my_checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    with pytest.raises(CheckerException) as ex:
        JavaScriptService._check(
            checker_func=checker_func,
            right_value='value',
            value='value',
        )

    assert ex.value.message == messages.MSG_2


def test_check__checker_func_no_return_instruction__raise_exception():
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  result = right_value == value'
    )

    with pytest.raises(CheckerException) as ex:
        JavaScriptService._check(
            checker_func=checker_func,
            right_value='value',
            value='value',
        )

    assert ex.value.message == messages.MSG_3


def test_check__checker_func_return_not_bool__raise_exception():
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return None'
    )

    with pytest.raises(CheckerException) as ex:
        JavaScriptService._check(
            checker_func=checker_func,
            right_value='value',
            value='value',
        )

    assert ex.value.message == messages.MSG_4


def test_check__checker_func__invalid_syntax__raise_exception():
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  include(invalid syntax here)'
        '  return True'
    )

    with pytest.raises(CheckerException) as ex:
        JavaScriptService._check(
            checker_func=checker_func,
            right_value='value',
            value='value',
    )

    assert ex.value.message == messages.MSG_5
    assert 'invalid syntax' in ex.value.details
    assert '(<string>, line 1)' in ex.value.details


def test_run__ok(mocker, tmp_path):
    mocker.patch.object(config, 'SANDBOX_DIR', str(tmp_path))
    mocker.patch(
        'app.service.main.JavaScriptService._execute',
        return_value=ExecuteResult(
            stdout='Hello from JS',
            stderr='',
            exit_code=0
        )
    )

    data = JavaScriptService.run(
        RunData(code='console.log("Hello from JS")')
    )

    assert data.stdout == 'Hello from JS'
    assert data.stderr == ''
    assert data.exit_code == 0
    assert list(tmp_path.iterdir()) == []


def test_javascript_file__creates_main_js(mocker, tmp_path):
    mocker.patch.object(config, 'SANDBOX_DIR', str(tmp_path))

    file = JavaScriptFile('console.log("ok")')

    assert file.filepath.endswith('main.js')
    assert file.public_name == 'main.js'
    assert Path(file.directory).parent == tmp_path
    assert open(file.filepath, encoding='utf-8').read() == 'console.log("ok")'
    file.remove()
    assert not Path(file.directory).exists()


def test_execute__timeout(mocker, tmp_path):
    mocker.patch.object(config, 'SANDBOX_DIR', str(tmp_path))
    mocker.patch(
        'app.service.main.JavaScriptService._preexec_fn',
        return_value=None
    )

    class FakeProc:
        returncode = None

        def communicate(self, input=None, timeout=None):
            raise subprocess.TimeoutExpired(cmd=['node'], timeout=timeout)

        def kill(self):
            pass

    mocker.patch('subprocess.Popen', return_value=FakeProc())

    file = JavaScriptFile('while (true) {}')
    result = JavaScriptService._execute(file=file)

    assert result.stdout == ''
    assert result.stderr == messages.MSG_1
    assert result.exit_code == 124
    file.remove()


def test_debug__ok(mocker):
    execute_result = ExecuteResult(
        stdout='some execute code result',
        stderr='some runtime error',
        exit_code=1,
    )
    execute_mock = mocker.patch(
        'app.service.main.JavaScriptService._execute',
        return_value=execute_result
    )
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(JavaScriptFile, '__new__', return_value=file_mock)
    data = DebugData(
        code='some code',
        data_in='some data_in',
    )

    debug_result = JavaScriptService.debug(data)

    assert debug_result.result == execute_result.stdout
    assert debug_result.error == execute_result.stderr
    assert debug_result.exit_code == execute_result.exit_code
    file_mock.remove.assert_called_once()
    execute_mock.assert_called_once_with(
        file=file_mock,
        data_in=data.data_in,
    )


def test_testing__ok(mocker):
    execute_result = ExecuteResult(
        stdout='some execute code result',
        stderr='',
        exit_code=0,
    )
    execute_mock = mocker.patch(
        'app.service.main.JavaScriptService._execute',
        return_value=execute_result
    )
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(JavaScriptFile, '__new__', return_value=file_mock)
    check_result = mocker.Mock()
    check_mock = mocker.patch(
        'app.service.main.JavaScriptService._check',
        return_value=check_result
    )
    test_1 = TestData(
        data_in='some test input 1',
        data_out='some test out 1',
    )
    test_2 = TestData(
        data_in='some test input 2',
        data_out='some test out 2',
    )
    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2],
    )

    testing_result = JavaScriptService.testing(data)

    tests_result = testing_result.tests
    assert len(tests_result) == 2
    assert tests_result[0].result == execute_result.stdout
    assert tests_result[0].error is None
    assert tests_result[0].exit_code == execute_result.exit_code
    assert tests_result[0].ok == check_result
    assert tests_result[1].result == execute_result.stdout
    assert tests_result[1].error is None
    assert tests_result[1].exit_code == execute_result.exit_code
    assert tests_result[1].ok == check_result
    assert execute_mock.call_args_list == [
        call(
            file=file_mock,
            data_in=test_1.data_in,
        ),
        call(
            file=file_mock,
            data_in=test_2.data_in,
        ),
    ]
    assert check_mock.call_args_list == [
        call(
            checker_func=data.checker,
            right_value=test_1.data_out,
            value=execute_result.stdout,
        ),
        call(
            checker_func=data.checker,
            right_value=test_2.data_out,
            value=execute_result.stdout,
        ),
    ]
    file_mock.remove.assert_called_once()