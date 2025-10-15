#!/usr/bin/env bash
set -euo pipefail

/app/scripts/wait_for_db.py

python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:8000
