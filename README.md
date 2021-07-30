<p align="center">
  <img src="https://github.com/nitrictech/python-sdk/raw/main/docs/assets/dot-matrix-logo-python.png" alt="Nitric Python SDK Logo"/>
</p>

![test status](https://github.com/nitrictech/python-sdk/actions/workflows/test.yaml/badge.svg?branch=main)
[![codecov](https://codecov.io/gh/nitrictech/python-sdk/branch/main/graph/badge.svg?token=SBFRNSZ4ZF)](https://codecov.io/gh/nitrictech/python-sdk)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=nitrictech_python-sdk&metric=alert_status)](https://sonarcloud.io/dashboard?id=nitrictech_python-sdk)

# Nitric Python SDK

The Python SDK supports the use of the cloud-portable [Nitric](https://nitric.io) framework with Python 3.7+.

> The Nitric Python SDK is currently in Preview, API changes are likely prior to v1.x release.

Read full documentation [here](https://nitrictech.github.io/python-sdk/).

## Usage

### Nitric Functions (FaaS):

 - Install Python 3.7+
 - Install the [Nitric CLI](https://nitric.io/docs/installation?lang=python)
 - Create / Open a Nitric Project
 - Make a Python37 function
 
 ```bash
# Create a new project
nitric make:project example-python
cd example-python

# Create a python37 Nitric Function
nitric make:service function/python37 example-function
```

> note: The SDK will be included in the requirements.txt of a new Python function by default.

### Standard Python Project

 - Install Python 3.7+

```bash
# Install the Nitric SDK
pip3 install nitric
```

```python
# import classes/modules as required
from nitric.api import Events, KeyValueClient
```