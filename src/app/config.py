import os
from os import environ as env
from tempfile import gettempdir


TIMEOUT = int(env.get("SANDBOX_TIMEOUT", "5"))
SANDBOX_USER_UID = int(env.get("SANDBOX_USER_UID", getattr(os, "getuid", lambda: 999)()))
SANDBOX_DIR = env.get("SANDBOX_DIR", gettempdir())
