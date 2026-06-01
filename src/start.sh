#!/bin/bash
gunicorn --pythonpath '/app/src' --bind 0:9003 app.main:app --reload -w 1

