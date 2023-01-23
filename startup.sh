nohup python3 schedule.py >> scheduler.logs &
nohup uvicorn main:app --host 0.0.0.0 --port 5000 >> api.logs &
