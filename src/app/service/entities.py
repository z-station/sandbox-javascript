import os
import uuid
from collections import namedtuple

from app import config


ExecuteResult = namedtuple("ExecuteResult", ("stdout", "stderr", "exit_code"))


class JavaScriptFile:
    """Описывает файл, необходимый для запуска JavaScript-программы."""

    def __init__(self, code: str):
        file_id = uuid.uuid4()
        self.directory = os.path.join(config.SANDBOX_DIR, str(file_id))
        self.public_name = "main.js"
        self.filepath = os.path.join(self.directory, self.public_name)
        os.makedirs(self.directory, exist_ok=False)
        with open(self.filepath, "w", encoding="utf-8") as file:
            file.write(code)

    def remove(self):
        try:
            os.remove(self.filepath)
            os.rmdir(self.directory)
        except OSError:
            pass
