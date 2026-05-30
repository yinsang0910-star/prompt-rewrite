"""Setup file for prompt-rewrite."""
from setuptools import setup, find_packages

setup(
    name="prompt-rewrite",
    version="0.2.0",
    description="Prompt Rewrite System — Smart prompt optimization engine with AI enhancement",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "prompt_rewrite": ["templates/*.yaml"],
    },
    install_requires=[
        "pyyaml>=6.0",
        "click>=8.0",
        "requests>=2.25",
        "fastapi>=0.100",
        "uvicorn>=0.23",
    ],
    entry_points={
        "console_scripts": [
            "prompt-rewrite=prompt_rewrite.cli:main",
        ],
    },
    python_requires=">=3.8",
)
