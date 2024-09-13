import setuptools
from aic51.packages.webui.npminstaller import NPMInstaller

if __name__ == "__main__":
    setuptools.setup(cmdclass={"npm_install": NPMInstaller})
