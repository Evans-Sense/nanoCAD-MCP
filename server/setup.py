"""Minimal setup.py for editable installs.

pyproject.toml handles the main configuration.
This file ensures setuptools discovers the src.* namespace packages
correctly during editable (pip install -e) installations.
"""

from setuptools import find_namespace_packages, setup

setup(
    packages=find_namespace_packages(include=["src", "src.*"]),
)
