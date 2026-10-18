from fastapi import FastAPI


app = FastAPI(title="商品推荐助手")

@app.get("/health")
def health():
    return {"status": "ok"}