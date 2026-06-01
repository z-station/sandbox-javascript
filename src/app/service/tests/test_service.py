# Тесты запускать только в контейнере!
import subprocess
from pathlib import Path

from app import config
from app.entities import RunData
from app.service import messages
from app.service.entities import ExecuteResult, JavaScriptFile
from app.service.main import JavaScriptService


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
