#!/bin/bash

nohup python3 -u schedule.py >> scheduler.log &
nohup uvicorn main:app --host 0.0.0.0 --port 5000 >> api.log &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?