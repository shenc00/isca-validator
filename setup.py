from setuptools import setup, find_packages

setup(
    name="isca-validator",
    version="1.0.0",
    description="Validates Databricks SQL/PySpark notebooks against ISCA Data Engineering Standards",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[],
    extras_require={"dev": ["pytest>=7.0"]},
    entry_points={
        "console_scripts": [
            "isca-validate=isca_validator.cli:main",
        ]
    },
)
