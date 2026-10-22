import os
import pathlib

from dotenv import load_dotenv
env_path=pathlib.Path(__file__).resolve().parent/".env"
load_dotenv(dotenv_path=env_path)
from langchain.chat_models import init_chat_model
model=init_chat_model(
    model="deepseek-v4-flash",
    extra_body={
        "thinking": {"type": "disabled"}
    }
)
