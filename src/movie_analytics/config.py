"""Environment-backed configuration shared by pipeline components."""

import os


def env_int(name: str, default: int) -> int:
    """Read an integer environment variable, using ``default`` when unset."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def configure_dlt_postgres_from_env() -> None:
    """Map the project's PostgreSQL variables to dlt's expected variables."""
    mappings = {
        "DESTINATION__POSTGRES__CREDENTIALS__HOST": "POSTGRES_HOST",
        "DESTINATION__POSTGRES__CREDENTIALS__PORT": "POSTGRES_PORT",
        "DESTINATION__POSTGRES__CREDENTIALS__DATABASE": "POSTGRES_DB",
        "DESTINATION__POSTGRES__CREDENTIALS__USERNAME": "POSTGRES_USER",
        "DESTINATION__POSTGRES__CREDENTIALS__PASSWORD": "POSTGRES_PASSWORD",
    }
    defaults = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "movies",
        "POSTGRES_USER": "itc6050",
        "POSTGRES_PASSWORD": "itc6050",
    }

    for dlt_key, app_key in mappings.items():
        os.environ.setdefault(dlt_key, os.getenv(app_key, defaults[app_key]))
