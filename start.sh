#!/bin/sh
exec gunicorn -w 2 -b :10000 app:dick
#exec python rest_api.py
