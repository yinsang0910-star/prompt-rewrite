"""Setup file for prompt-rewrite.
Metadata is defined in pyproject.toml — this file is kept for pip install -e . compatibility.
"""
from setuptools import setup, find_packages

setup(
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "prompt_rewrite": ["templates/*.yaml"],
    },
)
