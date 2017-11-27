#!/bin/bash
set -e

echo "Setting fake values for git config..."
git config --global user.email flatisfy@example.com
git config --global user.name "Flatisfy Root"

echo "Building data for Flatisfy..."
cd /home/user/app
python -m flatisfy build-data -v --config /flatisfy/config.json

echo "Fetching new housing posts..."
/home/user/fetch.sh

echo "Starting web UI..."
python -m flatisfy serve -v --config /flatisfy/config.json
