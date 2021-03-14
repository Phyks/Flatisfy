#!/bin/sh -ev

function clean_up {

    # Perform program exit housekeeping
    kill $SERVE_PID $YARN_PID
    exit
}

python -m flatisfy serve --config config.json -v &
SERVE_PID=$!

yarn watch:dev &
YARN_PID=$!

trap clean_up SIGHUP SIGINT SIGTERM

wait $SERVE_PID $YARN_PID
