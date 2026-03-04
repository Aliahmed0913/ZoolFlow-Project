#!/bin/sh 
# called shebang first two bytes,declare the script should run with (POSIX shell=>universal unix shell)(ex.dash,busybox shell)

# this line ensure if any command fail the entire script stop => (prevent starting the server if there is error)
set -e

# sh command to check connectivity to postgres port. (netcat(nc)=>--check TCP open, connect to socket, send data) . -z scan without send data
until nc -z db 5432;do
    sleep 0.5
done
echo "DB ready!"

# noinput to not ask the user anything
python manage.py migrate --noinput

# collectstatic depends on STATIC_ROOT
python manage.py collectstatic --noinput

# wait for redis to be ready
until nc -z redis 6379; do sleep 0.5; done
echo "redis ready!"

# $@ => replace the shell we are in now with (gunicorn process or CMD command process)
exec "$@"