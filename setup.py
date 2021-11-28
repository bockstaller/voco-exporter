import os
from distutils.command.build import build

from django.core import management
from setuptools import find_packages, setup

from voco_exporter import __version__


try:
    with open(
        os.path.join(os.path.dirname(__file__), "README.rst"), encoding="utf-8"
    ) as f:
        long_description = f.read()
except Exception:
    long_description = ""


class CustomBuild(build):
    def run(self):
        management.call_command("compilemessages", verbosity=1)
        build.run(self)


cmdclass = {"build": CustomBuild}


setup(
    name="voco-exporter",
    version=__version__,
    description="Short description",
    long_description=long_description,
    url="github.com/bockstaller/voco-exporter",
    author="Lukas Bockstaller",
    author_email="lukas.bockstaller@gmail",
    license="Apache",
    install_requires=[],
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    cmdclass=cmdclass,
    entry_points="""
[pretix.plugin]
voco_exporter=voco_exporter:PretixPluginMeta
""",
)
