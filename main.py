import base64
import json
import os
import uuid
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Body, UploadFile
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


def get_text_response(query, chat_id):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": query,
             "name": chat_id
             },

        ]
    )

    return completion.choices[0].message


def get_response_for_text_image(message, chat_id, base64_image):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        },
                    },
                ],
                "name": chat_id
            }
        ],
        max_tokens=300,
    )

    return response.choices[0].message.content


def get_videos(query):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&q={query}&type=video&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    json_res = response.json()
    video_id = json_res["items"][0]["id"]["videoId"]
    return f"www.youtube.com/watch?v={video_id}"


class ReqBody(BaseModel):
    query: str = ""
    chat_id: Optional[str] = ""
    need_yt_video: bool = False


@app.post("/")
def _query(file: UploadFile = None, query=Body(...)):
    data: ReqBody = json.loads(query)
    if not data.chat_id:
        data.chat_id = str(uuid.uuid4())
    yt_link = None
    if file:
        base_64_file = base64.b64encode(file.file.read()).decode('utf-8')
        chat_response = get_response_for_text_image(data.query, data.chat_id, base_64_file)
    else:
        chat_response = get_text_response(data.query, data.chat_id)
    if data.need_yt_video:
        yt_link = get_videos(chat_response)

    response = {
        "chat_response": chat_response,
        "chat_id": data.chat_id,
        "yt_link": yt_link
    }
    return response
