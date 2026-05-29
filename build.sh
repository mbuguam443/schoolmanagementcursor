#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --clear --no-input
python manage.py migrate --no-input

if [ "$LOAD_DEMO_DATA" = "true" ]; then
  python manage.py setup_demo
fi
