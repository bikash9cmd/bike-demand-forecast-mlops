import re
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url

from db import DRIVERNAME, build_db_url

REPO_ROOT = Path(__file__).resolve().parents[1]
URL_PATTERN = re.compile(r"\b(mysql\+\w+)://")


def test_defaults_match_docker_compose():
    url = build_db_url({})
    assert url.drivername == "mysql+mysqldb"
    assert url.username == "mlops"
    assert url.password == "mlops123"
    assert url.host == "mariadb"
    assert url.port == 3306
    assert url.database == "depression_db"


def test_env_overrides_defaults():
    url = build_db_url({
        "DB_USER": "svc",
        "DB_PASSWORD": "pw",
        "DB_HOST": "db.internal",
        "DB_PORT": "3307",
        "DB_NAME": "analytics",
    })
    assert (url.username, url.password, url.host, url.port, url.database) == (
        "svc", "pw", "db.internal", 3307, "analytics",
    )


def test_empty_values_fall_back_to_defaults():
    url = build_db_url({"DB_HOST": "", "DB_PORT": ""})
    assert url.host == "mariadb"
    assert url.port == 3306


def test_reads_process_environment(monkeypatch):
    monkeypatch.setenv("DB_HOST", "from-env")
    assert build_db_url().host == "from-env"


def test_special_characters_in_password_survive_round_trip():
    password = "p@ss/w:rd#1"
    url = build_db_url({"DB_PASSWORD": password})
    rendered = url.render_as_string(hide_password=False)
    parsed = make_url(rendered)
    assert parsed.password == password
    assert parsed.host == "mariadb"
    assert parsed.database == "depression_db"


def test_non_numeric_port_is_rejected_with_clear_message():
    with pytest.raises(ValueError, match="DB_PORT must be an integer"):
        build_db_url({"DB_PORT": "abc"})


def test_driver_resolves_to_a_real_sqlalchemy_dialect():
    dialect = build_db_url({}).get_dialect()
    assert dialect.driver == "mysqldb"
    assert DRIVERNAME == "mysql+mysqldb"


def _connection_strings():
    found = []
    for path in sorted(REPO_ROOT.rglob("*")):
        if path.suffix not in {".py", ".yml", ".yaml"} or ".git" in path.parts:
            continue
        if path.parent.name == "tests":
            continue
        for match in URL_PATTERN.finditer(path.read_text(encoding="utf-8")):
            found.append((path.relative_to(REPO_ROOT).as_posix(), match.group(1)))
    return found


CONNECTION_STRINGS = _connection_strings()


def test_scan_finds_the_dag_connection_strings():
    files = {path for path, _ in CONNECTION_STRINGS}
    assert "dags/dag_ingestion.py" in files
    assert "dags/dag_monitoring.py" in files


@pytest.mark.parametrize("path,driver", CONNECTION_STRINGS)
def test_every_hardcoded_driver_name_is_known_to_sqlalchemy(path, driver):
    # get_dialect() only loads the dialect class, so the DB driver packages
    # do not need to be installed for this check.
    make_url(f"{driver}://u:p@h/db").get_dialect()
