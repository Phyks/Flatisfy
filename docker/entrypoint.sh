#!/bin/bash
set -e

# Add local user
# Either use the LOCAL_USER_ID if passed in at runtime or
# fallback
USER_ID=${LOCAL_USER_ID:-9001}

echo "[ENTRYPOINT] Starting with UID : $USER_ID"
usermod -u $USER_ID -o user
export HOME=/home/user

echo "[ENTRYPOINT] Setting fake values for git config..."
git config --global user.email flatisfy@example.com
git config --global user.name "Flatisfy Root"

echo "Update Weboob..."
/home/user/update_weboob.sh

exec su user -c "$@"
