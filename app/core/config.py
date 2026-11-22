from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """All configuration comes from environment variables in .env."""

    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "")

    # Comma-separated list of allowed CORS origins.
    allowed_origins: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:19000,http://localhost:19001,http://localhost:19002,http://localhost:8081,http://localhost:3000",
        ).split(",")
        if origin.strip()
    ]

    api_port: int = int(os.getenv("API_PORT", "8000"))

    @classmethod
    def validate(cls) -> None:
        missing = [
            name
            for name in (
                "SUPABASE_URL",
                "SUPABASE_ANON_KEY",
                "SUPABASE_SERVICE_ROLE_KEY",
                "SUPABASE_JWT_SECRET",
            )
            if not getattr(cls, name.lower())
        ]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Copy .env.example to .env and fill in the values."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
