import setuptools
import re
from subprocess import Popen, PIPE


def get_current_version_tag():
    process = Popen(["git", "describe", "--tags", "--match", "v[0-9]*"], stdout=PIPE)
    (output, err) = process.communicate()
    process.wait()

    tags = str(output, "utf-8").strip().split("\n")

    version_tags = [tag for tag in tags if re.match(r"^v?(\d*\.){2}\d$", tag)]
    rc_tags = [tag for tag in tags if re.match(r"^v?(\d*\.){2}\d*-rc\.\d*$", tag)]

    if len(version_tags) == 1:
        return version_tags.pop()[1:]
    elif len(rc_tags) == 1:
        base_tag, num_commits = rc_tags.pop().split("-rc.")[:2]
        return "{}.dev{}".format(base_tag, num_commits)[1:]
    else:
        return "0.0.0.dev0"


with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name="nitric",
    version=get_current_version_tag(),
    author="Nitric",
    author_email="team@nitric.io",
    description="The Nitric SDK for Python 3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nitrictech/python-sdk",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    license_files=("LICENSE.txt",),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    setup_requires=["wheel"],
    install_requires=[
        "nitric-api==0.12.0rc7",
        "protobuf==3.13.0",
        "asyncio",
    ],
    extras_require={
        "dev": [
            "tox==3.20.1",
            "twine==3.2.0",
            "pytest==6.0.1",
            "pytest-cov==2.10.1",
            "pre-commit==2.12.0",
            "black==21.4b2",
            "flake8==3.9.1",
            "flake8",
            "flake8-bugbear",
            "flake8-comprehensions",
            "flake8-string-format",
            "pydocstyle==6.0.0",
            "pip-licenses==3.3.1",
            "licenseheaders==0.8.8",
            "pdoc3==0.9.2",
        ]
    },
    python_requires=">=3.7",
)
