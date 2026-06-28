from fastapi import FastAPI

app = FastAPI(title="uv_recruit sample API")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "ok"}
