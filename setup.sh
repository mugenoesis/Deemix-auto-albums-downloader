#!/bin/bash

mkdir deemix_db
printenv arl > /app/.arl
python3 ./main.py --host=0.0.0.0