#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectsatic --no-inpt
python manage.py migrate