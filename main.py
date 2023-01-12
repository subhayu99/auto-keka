import config
import uvicorn
from src import helpers
from src.user import User
from src.keka import Keka
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Auto Keka", description="Automation API for Keka", version="0.0.1")

user = User()
x = Keka(user)


@app.get(
    "/punch/{punch_type}/", 
    description="**0** for `Punch In`, **1** for `Punch Out`, **2** for `No Punch`"
)
def punch(punch_type: config.PunchType, force: bool = False):
    return x.punch(punch_type, force=force)


@app.get("/get_token_age/")
def get_token_age():
    token_age, timestamp = x.get_token_age(auto_load=True)
    return {
        "token_age": token_age.total_seconds(),
        "timestamp": timestamp,
        "message": helpers.format_time_delta("Token is ", token_age, " old"),
    }


@app.get("/retrieve_state/")
def retrieve_state():
    punch_status, timestamp = x.retrieve_state()
    punch_message = config.punch_message_map[punch_status.value]
    return {
        "punch_status": punch_message,
        "timestamp": timestamp,
        "message": helpers.format_time_delta(
            f"{punch_message} ", datetime.now(user.timezone) - timestamp, " ago"
        ),
    }


@app.get("/refresh_token/")
async def refresh_token():
    x.refresh_token(headless=True)
    return get_token_age()


@app.get("/help/")
def api_help():
    return {"punch_types": config.PunchType.__members__}



if __name__ == "__main__":
    # get run_server from sys.argv
    import sys
    run_server = sys.argv[1] if len(sys.argv) > 1 else "dont run"
    
    # run server if run_server arg is passed as yes or true
    if run_server.lower() == "run":
        uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
