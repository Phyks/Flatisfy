#!/bin/bash
set -e

echo "Fetching new housing posts..."
cd /home/user/app
python -m flatisfy import -v --config /flatisfy/config.json

