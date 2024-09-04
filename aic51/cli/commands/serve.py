import os
import sys
import subprocess
from pathlib import Path

import uvicorn

from .command import BaseCommand
from ...config import GlobalConfig
from ...packages.index import MilvusDatabase


class ServeCommand(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(ServeCommand, self).__init__(*args, **kwargs)

    def add_args(self, subparser):
        parser = subparser.add_parser("serve", help="Start RestAPI and WebUI")

        parser.add_argument(
            "-d",
            "--dev",
            dest="dev_mode",
            action="store_true",
            help="Use dev mode",
        )
        parser.add_argument(
            "-w",
            "--workers",
            dest="workers",
            type=int,
            default=1,
            help="Number of workers to serve in uvicorn",
        )

        parser.set_defaults(func=self)

    def __call__(self, dev_mode, workers, *args, **kwargs):
        MilvusDatabase.start_server()
        if len(GlobalConfig.get("webui", "features") or []) == 0:
            self._logger.error(
                f'No models found in "{GlobalConfig.CONFIG_FILE}". Check your "{GlobalConfig.CONFIG_FILE}"'
            )
            sys.exit(1)

        os.environ["AIC51_WORK_DIR"] = str(self._work_dir)
        dev_params = dict(
            reload=True,
            reload_dirs=[str(Path(__file__).parent / "../../packages")],
        )
        params = {}
        if dev_mode:
            params = {**params, **dev_params}

        uvicorn.run(
            f"aic51.packages.webui.backend.app:app",
            port=5000,
            log_level="info",
            workers=workers,
            **params,
        )
