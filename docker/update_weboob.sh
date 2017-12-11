#!/bin/bash
set -e

echo "Setting fake values for git config..."
git config --global user.email flatisfy@example.com
git config --global user.name "Flatisfy Root"

echo "Updating Weboob..."
cd /home/user/weboob
git pull
pip install --upgrade .
