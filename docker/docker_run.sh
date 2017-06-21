#!/bin/bash

cd /home/user/app

python -m flatisfy build-data -v --config /flatisfy/config.json

# Run the server in the background.
python -m flatisfy serve --config /flatisfy/config.json &

while true;
do
    cd /home/user/weboob
    git pull

    cd /home/user/app
    python -m flatisfy import -v --config /flatisfy/config.json

    echo "Done, sleeping for 30 minutes."
    sleep 1800
done
