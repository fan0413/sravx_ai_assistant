import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
load_dotenv(override=True)
model=init_chat_model(
    model="deepseek-v4-flash",
    extra_body={
        "thinking": {"type": "disabled"}
    }
)
