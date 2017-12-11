#!/bin/bash
set -e

echo "Update Weboob..."
/home/user/update_weboob.sh

echo "Building data for Flatisfy..."
cd /home/user/app
su user -c "python -m flatisfy build-data -v --config /flatisfy/config.json"

echo "Fetching new housing posts..."
cd /home/user/app
su user -c "python -m flatisfy import -v --config /flatisfy/config.json"

echo "Starting web UI..."
exec su user -c "python -m flatisfy serve -v --config /flatisfy/config.json"
