from fastapi import FastAPI

from app.api import routes_health
from app.core.config import get_settings
from app.idgen.base import IdIssuer
from app.idgen.factory import build_issuer


def create_app(issuer: IdIssuer) -> FastAPI:
    application = FastAPI(title="uv_recruit user-id API")
    application.state.issuer = issuer
    application.include_router(routes_health.router)

    @application.get("/")
    async def root() -> dict[str, str]:
        return {"message": "ok"}

    return application


app = create_app(build_issuer(get_settings()))
