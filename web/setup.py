from setuptools import setup

setup(
    name="eon-web",
    version="2.2.0",
    description="Eón Project: Web Server Layer",
    author="Jeremy Sud",
    url="https://github.com/jeremy-sud/Eon-AI-Project",
    py_modules=[
        "server",
        "learning",
        "egregore_art",
    ],
    python_requires=">=3.9",
)
