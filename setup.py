from setuptools import setup

setup(
    name = 'gopro2gpx',
    author = 'Juan M. Casillas',
    url = 'https://github.com/juanmcasillas/gopro2gpx',
    version = "0.1",
    packages = ['gopro2gpx'],
    entry_points = {
        'console_scripts': ['gopro2gpx = gopro2gpx.__main__:main']
    }
)
