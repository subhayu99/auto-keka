#!/bin/bash

nohup python3 schedule.py >> scheduler.logs &
nohup uvicorn main:app --host 0.0.0.0 --port 5000 >> api.logs &

# Wait for any process to exit
wait -n
  
# Exit with status of process that exited first
exit $?