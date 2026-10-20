import os
import pathlib

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
env_path=pathlib.Path(__file__).resolve().parent/".env"
load_dotenv(dotenv_path=env_path)
model=init_chat_model(
    model="deepseek-v4-flash",
    extra_body={
        "thinking": {"type": "disabled"}
    }
)
