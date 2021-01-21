#!/bin/sh -ev
python -m flatisfy import --config config.json --new-only -v "$@"
