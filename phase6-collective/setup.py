from setuptools import setup

setup(
    name="eon-collective",
    version="2.2.0",
    description="Eón Project: Collective Intelligence Layer",
    author="Jeremy Sud",
    url="https://github.com/jeremy-sud/Eon-AI-Project",
    py_modules=[
        "collective_mind",
        "egregore",
        "mqtt_client",
        "quantum_sync",
        "ws_bridge",
    ],
    python_requires=">=3.9",
)
