#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Collecting static assets with WhiteNoise..."
python manage.py collectstatic --no-input

echo "Applying database migrations..."
python manage.py migrate

echo "Seeding initial demo data (Curriculum, Sample Students, Certificates, NOC)..."
python manage.py seed_data

echo "Build process completed successfully!"
