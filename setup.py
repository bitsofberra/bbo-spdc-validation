from setuptools import find_packages, setup


setup(
    name="bbo-spdc-validation",
    version="0.1.0",
    description="Type-I SPDC simulations for BBO crystals and experimental comparison.",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24",
        "matplotlib>=3.7",
    ],
    extras_require={
        "dev": ["pytest>=7"],
    },
    entry_points={
        "console_scripts": [
            "bbo-spdc=bbo_spdc.cli:main",
        ],
    },
)
