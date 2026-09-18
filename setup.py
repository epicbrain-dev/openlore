from setuptools import setup, find_packages

setup(
    name="openlore",
    version="2.0.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={
        "console_scripts": [
            "openlore=openlore.cli.main:main",
        ],
    },
)
