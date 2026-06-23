"""Helper de conexão com MySQL."""
from sqlalchemy import create_engine
from urllib.parse import quote_plus

from src.config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE,
)

def get_engine(database: str | None = None):
    """Retorna um engine SQLAlchemy. Se database=None, conecta sem schema."""
    db = database if database is not None else MYSQL_DATABASE
    # quote_plus para senhas com caracteres especiais (@, /, etc.)
    pwd = quote_plus(MYSQL_PASSWORD)
    if db:
        url = f"mysql+pymysql://{MYSQL_USER}:{pwd}@{MYSQL_HOST}:{MYSQL_PORT}/{db}"
    else:
        url = f"mysql+pymysql://{MYSQL_USER}:{pwd}@{MYSQL_HOST}:{MYSQL_PORT}"
    return create_engine(url, pool_pre_ping=True)