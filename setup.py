"""Setup file for prompt-rewrite."""
from setuptools import setup, find_packages

setup(
    name="prompt-rewrite",
    version="0.1.0",
    description="基于 Prompt Engineering 最佳实践的 Prompt Rewrite System",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pyyaml>=6.0",
        "click>=8.0",
        "requests>=2.25",
    ],
    entry_points={
        "console_scripts": [
            "prompt-rewrite=prompt_rewrite.cli:main",
        ],
    },
    python_requires=">=3.8",
)
