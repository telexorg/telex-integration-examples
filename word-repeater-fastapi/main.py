from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Union, Optional
import json
import os
import uvicorn

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


class Setting(BaseModel):
    label: Optional[str]
    type: Optional[str]
    required: Optional[bool]
    default: Optional[Union[str, int, float, bool, None]]


class Message(BaseModel):
    settings: Optional[List[Setting]]
    message: Optional[str]
    channel_id: Optional[str]
    user_type: Optional[str]


def process_message(msg_req: Message) -> str:
    max_message_length = 500
    repeat_words = []
    no_of_repetitions = 1

    for setting in msg_req.settings:
        if setting.label == "maxMessageLength":
            if isinstance(setting.default, (int, float)):
                max_message_length = int(setting.default)
        elif setting.label == "repeatWords":
            if isinstance(setting.default, str):
                repeat_words = [word.strip()
                                for word in setting.default.split(",")]
        elif setting.label == "noOfRepetitions":
            if isinstance(setting.default, (int, float)):
                no_of_repetitions = int(setting.default)

    formatted_message = msg_req.message

    for word in repeat_words:
        formatted_message = formatted_message.replace(
            word, (word + " ") * no_of_repetitions
        )

    if len(formatted_message) > max_message_length:
        formatted_message = formatted_message[:max_message_length]

    return formatted_message


@app.post("/format-message")
async def format_message(request: Request):
    try:
        body = await request.json()
        msg_req = Message(**body)
        formatted = process_message(msg_req)

        return {
            "event_name": "message_formatted",
            "message": formatted,
            "status": "success",
            "username": "message-formatter-bot"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@app.get("/formatter-json")
def get_formatter_json(request: Request):
    try:
        base = str(request.url).split("formatter-json")[0]

        with open("formatter.json", "r", encoding="utf-8") as f:
            filecontent = f.read().replace("%", base)

        return json.loads(filecontent)

    except FileNotFoundError:
        raise HTTPException(
            status_code=500, detail="formatter.json file not found")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
