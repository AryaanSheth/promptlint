from setuptools import find_packages, setup

setup(
    name="promptlint",
    version="0.1.0",
    description="Lint prompts for cost, quality, and security issues.",
    packages=find_packages(),
    install_requires=[
        "typer[all]==0.9.0",
        "pyyaml==6.0.1",
        "tiktoken==0.5.2",
        "rich==13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "promptlint=promptlint.cli:main",
        ]
    },
)
