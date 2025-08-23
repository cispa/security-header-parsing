#!/bin/bash
set -e

echo "Waiting for Postgres at $DB_HOST:$DB_PORT..."
until pg_isready -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME"; do
  sleep 2
done

# Does not work on arm emulation
if grep -qi "VirtualApple" /proc/cpuinfo; then
  echo "Running under Rosetta emulation – skipping Xvfb"
else
  echo "Starting Xvfb and x11vnc available at port 5900 with passwd abc"
  rm -f /tmp/.X99-lock
  Xvfb :99 -screen 0 1920x1080x24 &
  # Wait until Xvfb is listening
  for i in $(seq 1 20); do
      if xdpyinfo -display :99 >/dev/null 2>&1; then
          echo "Xvfb is ready on :99"
          break
      fi
      echo "Waiting for Xvfb..."
      sleep 0.5
  done
  x11vnc -display :99 -bg -shared -forever -passwd abc -xkb -rfbport 5900
  export DISPLAY=:99 && fluxbox -log fluxbox.log &
fi

echo "Initializing database schema..."
cd _hp/hp/tools
poetry run python models.py
echo "Creating basic responses..."
poetry run python create_responses.py
echo "Creating parsing responses..."
poetry run python response_header_generation.py
cd -

echo "Starting server: $@"
exec "$@"
