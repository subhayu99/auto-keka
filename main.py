import config
import uvicorn
from src import helpers
from src.models import *
from src.user import User
from src.keka import Keka
from fastapi import FastAPI
from datetime import datetime, date
from fastapi.responses import PlainTextResponse

app = FastAPI(title="Auto Keka", description="Automation API for Keka", version="0.0.1")

user = User()
keka = Keka(user)


@app.get("/punch/", description="`Punch In` or `Punch Out` based on last punch status")
def punch_with_opposite_type(force: bool = False):
    status_code, message = keka.punch(force=force)
    return PlainTextResponse(message, status_code=status_code)


@app.get("/punch/{punch_type}/", description="**0** for `Punch In`, **1** for `Punch Out`")
def punch_with_given_type(punch_type: config.AllowedPunchType, force: bool = False):
    punch_type = config.PunchType(punch_type.value)
    status_code, message = keka.punch(punch_type, force=force)
    return PlainTextResponse(message, status_code=status_code)


@app.get("/get_work_time_for_date", description="Gives total working time for a given date. Date format: `YYYY-MM-DD`")
def get_work_time_for_date(for_date: str):
    work_time = keka.get_work_time_for_date(for_date:=date.fromisoformat(for_date))
    return {
        "total_seconds": work_time.total_seconds(),
        "formatted_time": helpers.format_time_delta(td=work_time),
        "day_of_week": for_date.strftime('%A').lower(),
    }


@app.get("/get_token_age/")
def get_token_age():
    token_age, timestamp = keka.get_token_age(auto_load=True)
    return {
        "email": user.email,
        "token_age": token_age.total_seconds(),
        "timestamp": timestamp,
        "message": helpers.format_time_delta("Token is ", token_age, " old"),
    }


@app.get("/retrieve_state/")
def retrieve_state():
    punch_status, timestamp = keka.retrieve_state()
    punch_message = config.punch_message_map[punch_status.value]
    return {
        "punch_status": punch_message,
        "timestamp": timestamp,
        "message": helpers.format_time_delta(
            f"{punch_message} ", datetime.now(user.timezone) - timestamp, " ago"
        ),
    }


@app.get("/retrieve_user/", response_model=ReturnUser)
def retrieve_user():
    return user.get_user()


@app.get("/get_keka_profile/")
def get_keka_profile():
    return keka.get_keka_profile()


@app.get("/refresh_token/")
async def refresh_token():
    keka.refresh_token(headless=True)
    return get_token_age()


if __name__ == "__main__":
    # get run_server from sys.argv
    import sys
    run_server = sys.argv[1] if len(sys.argv) > 1 else "dont run"

    # run server if run_server arg is passed as yes or true
    if run_server.lower() == "run":
        uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
