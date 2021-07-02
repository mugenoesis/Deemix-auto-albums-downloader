#!/bin/bash

mkdir deemix_db
# printenv arl > /app/.arl
#python3 ./app.py --host=0.0.0.0
python3 -m flask run --host=0.0.0.0