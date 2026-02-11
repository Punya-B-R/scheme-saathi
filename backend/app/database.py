import re
from urllib.parse import urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _is_ipv4(host: str) -> bool:
    parts = host.split(".")
    return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def _database_url() -> str:
    """Normalize DATABASE_URL and force host to 127.0.0.1 when not an IP (avoids getaddrinfo failures on Windows)."""
    url = (settings.DATABASE_URL or "").strip().replace("\r", "").replace("\n", "")
    if url.startswith(('"', "'")) and len(url) >= 2 and url[0] == url[-1]:
        url = url[1:-1].strip()
    if not url.startswith("postgresql+"):
        raise ValueError(
            "DATABASE_URL must start with postgresql+asyncpg:// (e.g. postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/scheme_saathi)"
        )
    parsed = urlparse(url)
    netloc = parsed.netloc
    if "@" in netloc:
        auth, hostport = netloc.rsplit("@", 1)
        if ":" in hostport:
            host, port = hostport.rsplit(":", 1)
        else:
            host, port = hostport, "5432"
        if host and host != "127.0.0.1" and not _is_ipv4(host):
            hostport = f"127.0.0.1:{port}" if port else "127.0.0.1"
            netloc = f"{auth}@{hostport}"
            url = urlunparse(parsed._replace(netloc=netloc))
    return url


try:
    _url = _database_url()
    engine = create_async_engine(
        _url,
        echo=settings.DEBUG,
    )
except Exception as e:
    raise ValueError(
        "Invalid DATABASE_URL in backend/.env. Use: postgresql+asyncpg://USER:PASSWORD@127.0.0.1:5432/scheme_saathi "
        "(no quotes, no spaces; if PASSWORD has special chars, URL-encode them)."
    ) from e

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables. Call once on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
