"""MariaDB connection settings for the API."""

import os
from typing import Mapping, Optional

from sqlalchemy.engine import URL

# SQLAlchemy registers the mysqlclient package (``import MySQLdb``) as the
# ``mysqldb`` driver. ``mysql+mysqlclient`` is not a valid driver name.
DRIVERNAME = "mysql+mysqldb"

DEFAULTS = {
    "DB_USER": "mlops",
    "DB_PASSWORD": "mlops123",
    "DB_HOST": "mariadb",
    "DB_PORT": "3306",
    "DB_NAME": "depression_db",
}


def build_db_url(env: Optional[Mapping[str, str]] = None) -> URL:
    """Build the MariaDB URL from ``DB_*`` environment variables.

    Credentials are passed to ``URL.create`` rather than formatted into a
    string, so passwords containing ``@``, ``/`` or ``:`` are escaped.
    """
    env = os.environ if env is None else env
    cfg = {key: env.get(key) or default for key, default in DEFAULTS.items()}

    try:
        port = int(cfg["DB_PORT"])
    except ValueError:
        raise ValueError(f"DB_PORT must be an integer, got {cfg['DB_PORT']!r}") from None

    return URL.create(
        drivername=DRIVERNAME,
        username=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        host=cfg["DB_HOST"],
        port=port,
        database=cfg["DB_NAME"],
    )
