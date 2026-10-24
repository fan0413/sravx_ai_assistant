import os
from dotenv import load_dotenv
import pathlib
env_path = pathlib.Path(__file__).resolve().parent/".env"
load_dotenv(dotenv_path=env_path)
from langchain_openai import OpenAIEmbeddings
def create_embedding_model():
    return OpenAIEmbeddings(
        model=os.environ["EMBEDDING_MODEL"],
        api_key=os.environ["EMBEDDING_API_KEY"],
        base_url=os.environ["EMBEDDING_BASE_URL"],
        dimensions=1024,
        chunk_size=10,
        check_embedding_ctx_length=False,
        request_timeout=15,
        max_retries=2,
    )


if __name__ == "__main__":
    embedding=create_embedding_model()
    vector=embedding.embed_query("使用的是什么钢材")
    print("向量维度",len(vector))
    print("前五个数值",vector[:5])