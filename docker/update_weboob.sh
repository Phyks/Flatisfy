#!/bin/bash
set -e

echo "Updating Weboob..."
cd /home/user/weboob
git pull
pip install --upgrade .
