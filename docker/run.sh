#!/bin/bash
set -e

echo "Building data for Flatisfy..."
cd /home/user/app
python -m flatisfy build-data -v --config /flatisfy/config.json

echo "Fetching new housing posts..."
cd /home/user/app
python -m flatisfy import -v --config /flatisfy/config.json

echo "Starting web UI..."
python -m flatisfy serve -v --config /flatisfy/config.json
