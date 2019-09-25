"""Setup file."""

from setuptools import find_packages, setup

setup(
    name='kitty-escape',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    entry_points={
        'console_scripts': ['kitty-escape = escape.main:main'],
    },
    install_requires=['pygame==1.9.6'],
)
