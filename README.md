# Nitric Python SDK

The Python SDK supports the use of the cloud-portable [Nitric](http://nitric.io) framework with Python 3.7+.

> The Nitric Python SDK is in early stage development and is currently only available on test.pypi.org.

Read full documentation [here](https://nitrictech.github.io/python-sdk/).

## Usage

### Nitric Functions (FaaS):

 - Install Python 3.7+
 - Install the [Nitric CLI](#)
 - Create / Open a Nitric Project
 - Make a Python37 function
 
 ```bash
# Create a new project
nitric make:project example-python
cd example-python

# Create a python37 Nitric Function
nitric make:function python37 example-function
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
from nitric.api import EventClient, KeyValueClient
```