import os
import sys
import logging
from argparse import ArgumentParser
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from rich.logging import RichHandler
from rich.traceback import install

from . import commands

                

def main():
    dev_mode = os.getenv("AIC51_DEV", "false").lower() == "true"
    # Setup loggers
    FORMAT = "%(message)s"
    DATE_FORMAT = "[%X]"
    logging.basicConfig(
        level=logging.DEBUG if dev_mode else logging.INFO,
        format=FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    logger = logging.getLogger(__name__)

    install(show_locals=dev_mode)

    work_dir = Path.cwd()

    parser = ArgumentParser(description="Command Line Interface of AIC51.")
    parser.add_argument(
        "-q",
        "--quiet",
        dest="verbose",
        action="store_false",
    )
    subparser = parser.add_subparsers(help="command", dest="command")

    for command_cls in commands.available_commands:
        command = command_cls(work_dir)

        command.add_args(subparser)

    args = parser.parse_args()

    args = vars(args)
    command = args.pop("command")

    func = args.pop("func")

    func(**args)


if __name__ == "__main__":
    main()
