from setuptools import setup, find_packages


with open("requirements.txt", "r") as f:
    required = f.read().split("\n")

setup(
    name="metaform",
    entry_points={"console_scripts": ["mf=metaform.cli:main"]},
    version="0.1.0",
    author="Shane Stephenson [stephenson.shane.a@gmail.com]",
    packages=find_packages(),
    package_dir={"metaform": "metaform"},
    install_requires=required,
    python_requires=">=3.10",
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
)
