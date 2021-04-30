import setuptools

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name="nitric",
    version="0.0.dev23",
    author="Nitric",
    author_email="team@nitric.io",
    description="The Nitric SDK for Python 3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nitrictech/python-sdk",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "flask==1.1.2",
        "waitress==1.4.4",
        "grpcio==1.33.2",
        "six==1.15.0",
        "protobuf==3.13.0",
    ],
    extras_require={
        "dev": [
            "grpcio-tools==1.33.2",
            "tox==3.20.1",
            "twine==3.2.0",
            "pytest==6.0.1",
            "pytest-cov==2.10.1",
            "pre-commit==2.12.0",
            "pip-licenses",
        ]
    },
    python_requires=">=3.7",
)
