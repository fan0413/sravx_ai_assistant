import os
import pathlib

from dotenv import load_dotenv
env_path=pathlib.Path(__file__).resolve().parent/".env"
load_dotenv(dotenv_path=env_path)
from langchain.chat_models import init_chat_model
model=init_chat_model(
    model="deepseek-v4-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    timeout=15,
    max_retries=2,
    extra_body={
        "thinking": {"type": "disabled"}
    }
)
