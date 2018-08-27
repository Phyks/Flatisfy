#!/bin/bash
set -e

echo "Updating Weboob..."
cd /home/user/weboob
git pull && pip install --upgrade . || echo "Couldn't upgrade Weboob; maybe the server is unreachable?"
