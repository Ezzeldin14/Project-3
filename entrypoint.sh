#!/bin/sh
set -o errexit
set -o pipefail

# Decode Google OAuth token if present
if [ -n "$GOOGLE_OAUTH2_TOKEN_B64" ]; then
    TOKEN_PATH=${GOOGLE_OAUTH2_TOKEN_STORAGE:-/app/users/oauth/token.pkl}
    mkdir -p "$(dirname "$TOKEN_PATH")"
    echo "$GOOGLE_OAUTH2_TOKEN_B64" | base64 -d > "$TOKEN_PATH"
fi

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn using Railway PORT
# --timeout 300: HF Space may need up to 5 min to wake up + process images
exec gunicorn API.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 300
