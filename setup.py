import setuptools

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name="nitric",
    version="0.0.dev14",
    author="Nitric",
    author_email="team@nitric.io",
    description="The Nitric SDK, used to communicate with native cloud services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nitric-dev/python-sdk",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=["grpcio==1.33.2", "six==1.15.0", "protobuf==3.13.0"],
    python_requires=">=3.7",
)
