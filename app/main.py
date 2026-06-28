from fastapi import FastAPI

from app.api import routes_health, routes_item

app = FastAPI(title="uv_recruit sample API")

app.include_router(routes_health.router)
app.include_router(routes_item.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "ok"}
