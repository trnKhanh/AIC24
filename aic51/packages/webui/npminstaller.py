from pathlib import Path
from setuptools.command.build import build


class NPMInstaller(build):
    def run(self):
        self.run_command(
            f"npm install --prefix {Path(__file__).parent / 'frontend'}",
        )
        build.run(self)
