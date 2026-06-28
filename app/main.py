from fastapi import FastAPI

from app.api import routes_health, routes_user
from app.core.config import get_settings
from app.idgen.base import IdIssuer
from app.idgen.factory import build_issuer


def create_app(issuer: IdIssuer) -> FastAPI:
    application = FastAPI(
        title="ユーザーID発行API（サンプル）",
        description=(
            "発行順ソート可能な base62 10文字 ID を払い出すサンプル API。"
            "/docs の Try it out から実際に発行できる。"
        ),
        version="0.2.0",
    )
    application.state.issuer = issuer
    application.include_router(routes_health.router)
    application.include_router(routes_user.router)

    @application.get("/")
    async def root() -> dict[str, str]:
        return {"message": "ok"}

    return application


app = create_app(build_issuer(get_settings()))
