#!/bin/bash
set -e

echo "Updating Weboob..."
cd /home/user/weboob
git pull
pip install .

echo "Fetching housing posts..."
cd /home/user/app
python -m flatisfy import -v --config /flatisfy/config.json
