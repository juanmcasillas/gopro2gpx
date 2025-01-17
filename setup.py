import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(here, "gopro2gpx", "__init__.py"), "r") as f:
    exec(f.read(), about)

setup(
    name = 'gopro2gpx',
    author = 'Juan M. Casillas',
    url = 'https://github.com/juanmcasillas/gopro2gpx',
    version=about["VERSION"],
    packages = ['gopro2gpx'],
    entry_points = {
        'console_scripts': ['gopro2gpx = gopro2gpx.gopro2gpx:main']
    }
)
