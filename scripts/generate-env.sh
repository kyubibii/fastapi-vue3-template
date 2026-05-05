#!/usr/bin/env bash
# Generate a .env file from .env.example with a random SECRET_KEY.
set -euo pipefail

if [ -f ".env" ]; then
  echo ".env already exists. Skipping."
  exit 0
fi

SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")

sed "s/^SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" .env.example > .env

echo ".env generated successfully."
echo "  SECRET_KEY has been randomized."
echo "  Edit .env to set your database credentials and other settings."
