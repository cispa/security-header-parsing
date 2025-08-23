#!/bin/bash
set -e

# Wait for Postgres to be ready
echo "Waiting for Postgres..."
until pg_isready -h $DB_HOST -U $DB_USER -d $DB_NAME; do
  sleep 2
done

# Run DB migrations / model setup
echo "Initializing database schema..."
poetry run python _hp/hp/tools/models.py
cd _hp/hp/tools && poetry run python create_responses.py
# Start server
exec "$@"
