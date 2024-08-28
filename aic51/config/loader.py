import logging
import sys
from pathlib import Path

from yaml import safe_load


def static_init(cls):
    if hasattr(cls, "__static_init__"):
        cls.__static_init__()
    return cls


@static_init
class GlobalConfig:
    CONFIG_FILE = "config.yaml"

    @classmethod
    def __static_init__(cls):
        work_dir = Path.cwd()
        config_path = work_dir / cls.CONFIG_FILE
        if not config_path.exists():
            cls.__config = None
            return

        with open(work_dir / cls.CONFIG_FILE, "r") as f:
            cls.__config = safe_load(f)

    @classmethod
    def get(cls, attr):
        logger = logging.getLogger(
            f'{".".join(__name__.split(".")[:-1])}.{cls.__name__}'
        )
        if cls.__config is None:
            logger.warning(
                f"{cls.CONFIG_FILE} not found. Are you in AIC51 directory?"
            )
            return None

        try:
            return cls.__config[attr]
        except KeyError:
            return None
