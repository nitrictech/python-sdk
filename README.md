<p align="center">
  <a href="https://nitric.io">
    <img src="docs/assets/nitric-logo.svg" width="120" alt="Nitric Logo"/>
  </a>
</p>

<h2 align="center">
  Build <a href="https://nitric.io">nitric</a> applications with Python
</h2>

<p align="center">
  <a href="https://actions-badge.atrox.dev/nitrictech/python-sdk/goto?ref=main"><img alt="Build Status" src="https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fnitrictech%2Fpython-sdk%2Fbadge%3Fref%3Dmain&style=for-the-badge" /></a>
  <a href="https://codecov.io/gh/nitrictech/python-sdk">
    <img alt="Codecov" src="https://img.shields.io/codecov/c/gh/nitrictech/python-sdk?style=for-the-badge&token=SBFRNSZ4ZF">
  </a>
  <a href="https://pypi.org/project/nitric">
    <img alt="Version" src="https://img.shields.io/pypi/v/nitric?style=for-the-badge">
  </a>
  <a href="https://pypi.org/project/nitric">
    <img alt="Downloads/week" src="https://img.shields.io/pypi/dw/nitric?style=for-the-badge">
  </a>
  <a href="https://nitric.io/chat"><img alt="Discord" src="https://img.shields.io/discord/955259353043173427?label=discord&style=for-the-badge"></a>
</p>

The Python SDK supports the use of the [Nitric](https://nitric.io) framework with Python 3.11+. For more information check out the main [Nitric repo](https://github.com/nitrictech/nitric).

Python SDKs provide an infrastructure-from-code style that lets you define resources in code. You can also write the functions that support the logic behind APIs, subscribers and schedules.

You can request the type of access you need to resources such as publishing for topics, without dealing directly with IAM or policy documents.

- Reference Documentation: https://nitric.io/docs/reference/python
- Guides: https://nitric.io/docs/guides/python

## Usage

### Starting a new project

Install the [Nitric CLI](https://nitric.io/docs/getting-started/installation), then generate your project:

```bash
nitric new hello-world py-starter
```

### Add to an existing project

First of all, you need to install the library:

**pip**

```bash
pip3 install nitric
```

**pipenv**

```
pipenv install nitric
```

Then you're able to import the library and create cloud resources:

```python
from nitric.resources import api, bucket
from nitric.application import Nitric
from nitric.context import HttpContext

publicApi = api("public")
uploads = bucket("uploads").allow("write")

@publicApi.get("/upload")
async def upload(ctx: HttpContext):
    photo = uploads.file("images/photo.jpg")

    url = await photo.upload_url()

    ctx.res.body = {"url": url}

Nitric.run()
```

## Learn more

Learn more by checking out the [Nitric documentation](https://nitric.io/docs).

## Get in touch:

- Join us on [Discord](https://nitric.io/chat)

- Ask questions in [GitHub discussions](https://github.com/nitrictech/nitric/discussions)

- Find us on [Twitter](https://twitter.com/nitric_io)

- Send us an [email](mailto:maintainers@nitric.io)
