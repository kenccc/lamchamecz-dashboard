#!/usr/bin/env bash
set -e

echo "[entrypoint] applying migrations"
python manage.py migrate --noinput

echo "[entrypoint] compiling messages"
python manage.py compilemessages

echo "[entrypoint] collecting static"
python manage.py collectstatic --noinput

if [ "${CREATE_SUPERUSER:-0}" = "1" ]; then
  echo "[entrypoint] ensuring superuser"
  python manage.py ensure_admin
fi

if [ "${DJANGO_DEBUG:-0}" = "1" ]; then
  echo "[entrypoint] dev runserver"
  exec python manage.py runserver 0.0.0.0:8000
else
  echo "[entrypoint] gunicorn"
  exec gunicorn lcm_dashboard.wsgi:application --bind 0.0.0.0:8000 --workers 3
fi
