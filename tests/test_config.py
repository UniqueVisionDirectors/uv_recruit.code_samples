from app.core.config import Settings


def test_settings_reads_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h:5432/d")
    settings = Settings()
    assert settings.database_url == "postgresql+psycopg://u:p@h:5432/d"
