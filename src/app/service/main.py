import os
import subprocess
from typing import Optional

from app import config
from app.entities import DebugData, RunData, TestsData
from app.service import exceptions
from app.service import messages
from app.service.entities import ExecuteResult, JavaScriptFile
from app.utils import clean_error, clean_str


class JavaScriptService:
    @classmethod
    def _preexec_fn(cls):
        def change_process_user():
            os.setgid(config.SANDBOX_USER_UID)
            os.setuid(config.SANDBOX_USER_UID)

        return change_process_user()

    @classmethod
    def _execute(
        cls,
        file: JavaScriptFile,
        data_in: Optional[str] = None,
    ) -> ExecuteResult:
        proc = subprocess.Popen(
            args=["node", file.filepath],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=cls._preexec_fn,
            text=True,
        )
        try:
            stdout, stderr = proc.communicate(
                input=data_in,
                timeout=config.TIMEOUT,
            )
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            stdout, stderr, exit_code = "", messages.MSG_1, 124
        except Exception as ex:
            raise exceptions.ExecutionException(details=str(ex))
        finally:
            proc.kill()

        return ExecuteResult(
            stdout=clean_str(stdout) or "",
            stderr=clean_error(stderr) or "",
            exit_code=exit_code,
        )

    @classmethod
    def _validate_checker_func(cls, checker_func: str):
        if not checker_func.startswith(
            "def checker(right_value: str, value: str) -> bool:"
        ):
            raise exceptions.CheckerException(messages.MSG_2)
        if checker_func.find("return") < 0:
            raise exceptions.CheckerException(messages.MSG_3)

    @classmethod
    def _check(cls, checker_func: str, **checker_func_vars) -> bool:
        cls._validate_checker_func(checker_func)
        try:
            exec(
                checker_func + "\nresult = checker(right_value, value)",
                globals(),
                checker_func_vars,
            )
        except Exception as ex:
            raise exceptions.CheckerException(
                message=messages.MSG_5,
                details=str(ex),
            )
        else:
            result = checker_func_vars["result"]
            if not isinstance(result, bool):
                raise exceptions.CheckerException(messages.MSG_4)
            return result

    @classmethod
    def run(cls, data: RunData) -> RunData:
        file = JavaScriptFile(data.code)
        exec_result = cls._execute(file=file)
        file.remove()
        data.stdout = exec_result.stdout
        data.stderr = exec_result.stderr
        data.exit_code = exec_result.exit_code
        return data

    @classmethod
    def debug(cls, data: DebugData) -> DebugData:
        file = JavaScriptFile(data.code)
        exec_result = cls._execute(file=file, data_in=data.data_in)
        file.remove()
        data.result = exec_result.stdout or None
        data.error = exec_result.stderr or None
        data.exit_code = exec_result.exit_code
        return data

    @classmethod
    def testing(cls, data: TestsData) -> TestsData:
        file = JavaScriptFile(data.code)
        for test in data.tests:
            exec_result = cls._execute(file=file, data_in=test.data_in)
            test.result = exec_result.stdout or None
            test.error = exec_result.stderr or None
            test.exit_code = exec_result.exit_code
            test.ok = (
                exec_result.exit_code == 0
                and cls._check(
                    checker_func=data.checker,
                    right_value=test.data_out,
                    value=test.result,
                )
            )
        file.remove()
        return data
