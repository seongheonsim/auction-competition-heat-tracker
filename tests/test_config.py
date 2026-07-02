from auction_tracker.config import Settings


def test_settings_reads_database_url_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h:5432/db")
    settings = Settings()
    assert settings.database_url == "postgresql+psycopg://u:p@h:5432/db"


def test_settings_defaults():
    settings = Settings(database_url="sqlite://")
    assert settings.imminent_days == 5
    assert settings.session_secret == "dev-secret"
