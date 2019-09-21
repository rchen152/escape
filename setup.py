"""Setup file."""

from setuptools import find_packages
from setuptools import setup

setup(
    name='kitty-escape',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': ['kitty-escape = escape.main:main'],
    },
    install_requires=['pygame==1.9.6'],
)
