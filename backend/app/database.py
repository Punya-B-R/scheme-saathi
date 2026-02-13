import logging
import ssl
from urllib.parse import urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)


def _database_url() -> str:
    """
    Normalize DATABASE_URL.
    Supports postgresql:// (auto-upgraded to asyncpg) and postgresql+asyncpg://.
    Normalizes localhost → 127.0.0.1 for Windows; leaves remote hosts untouched.
    """
    url = (settings.DATABASE_URL or "").strip().replace("\r", "").replace("\n", "")
    if url.startswith(('"', "'")) and len(url) >= 2 and url[0] == url[-1]:
        url = url[1:-1].strip()

    # Allow standard postgresql:// URLs (e.g. Supabase) and upgrade to asyncpg.
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    if not url.startswith("postgresql+asyncpg://"):
        raise ValueError(
            "DATABASE_URL must start with postgresql+asyncpg:// or postgresql:// "
            "(e.g. postgresql+asyncpg://postgres:password@127.0.0.1:5432/scheme_saathi "
            "or postgresql://postgres:password@db.<project>.supabase.co:5432/postgres)"
        )

    parsed = urlparse(url)
    netloc = parsed.netloc
    if "@" in netloc:
        auth, hostport = netloc.rsplit("@", 1)
    else:
        auth, hostport = "", netloc

    # Normalize localhost → 127.0.0.1 for Windows, keep remote hosts as-is.
    host = hostport
    port = ""
    if ":" in hostport:
        host, port = hostport.rsplit(":", 1)

    if host in ("localhost", ""):
        hostport = f"127.0.0.1:{port}" if port else "127.0.0.1"
        netloc = f"{auth}@{hostport}" if auth else hostport
        url = urlunparse(parsed._replace(netloc=netloc))

    return url


def _is_remote_url(url: str) -> bool:
    """Return True if the DB URL points to a remote host (not localhost/127.0.0.1)."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return host not in ("localhost", "127.0.0.1", "")


def _is_pooler_url(url: str) -> bool:
    """Detect Supabase connection pooler (pgbouncer) URLs (port 6543 or 'pooler' in host)."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    port = parsed.port
    return port == 6543 or "pooler" in host


try:
    _url = _database_url()

    # Build connect_args for asyncpg
    _connect_args: dict = {}

    # Supabase pooler (pgbouncer) does not support prepared statements.
    if _is_pooler_url(_url):
        _connect_args["statement_cache_size"] = 0
        _connect_args["prepared_statement_cache_size"] = 0
        logger.info("Detected Supabase pooler URL; disabled prepared statement cache.")

    # Remote databases (Supabase, etc.) require SSL.
    if _is_remote_url(_url):
        _ssl_ctx = ssl.create_default_context()
        _ssl_ctx.check_hostname = False
        _ssl_ctx.verify_mode = ssl.CERT_NONE
        _connect_args["ssl"] = _ssl_ctx
        logger.info("Remote database detected; SSL enabled.")

    engine = create_async_engine(
        _url,
        echo=settings.DEBUG,
        connect_args=_connect_args,
        pool_pre_ping=True,
    )
except Exception as e:
    raise ValueError(
        "Invalid DATABASE_URL in backend/.env. Use: postgresql+asyncpg://USER:PASSWORD@127.0.0.1:5432/scheme_saathi "
        "or postgresql://USER:PASSWORD@db.<project>.supabase.co:5432/postgres"
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
    
    import app.db_models  

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
