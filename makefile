install:
	@echo Installing Project Dependencies
	@python3 -m pip install -e .[dev]
	@pre-commit install
	@rm -rf ./.tox

.PHONY: docs clean license

docs:
	@echo Generating SDK Documentation
	@rm -rf docs/nitric
	@pdoc3 -f --html -o docs nitric

clean:
	@echo Cleaning Build Artefacts
	@rm -rf ./.eggs
	@rm -rf ./build
	@rm -rf ./dist

test:
	@echo Running Tox tests
	@tox -e py

NITRIC_VERSION="v1.0.0"

download:
	@curl -L https://github.com/nitrictech/nitric/releases/download/${NITRIC_VERSION}/contracts.tgz -o contracts.tgz
	@tar xvzf contracts.tgz
	@rm contracts.tgz

OUTPUT="./nitric/proto"
CONTRACTS="./contracts"

grpc-client: install download generate-proto

generate-proto:
	@echo Generating Proto Sources
	@echo $(OUTPUT)
	@mkdir -p $(OUTPUT)
    # protoc doesn't create the __init__.py for the nitric module, so we need to create it.
	@mkdir -p $(OUTPUT)/nitric/
	@touch $(OUTPUT)/nitric/__init__.py
	@python3 -m grpc_tools.protoc -I $(CONTRACTS) --python_betterproto_out=$(OUTPUT) ./contracts/proto/*/*/*.proto

license:
	@echo Applying Apache 2 header to source files
	@licenseheaders -t tools/apache-2.tmpl -o "Nitric Technologies Pty Ltd" -y 2021 -n "Nitric Python 3 SDK" -u "https://github.com/nitrictech/python-sdk" -d nitric
	@licenseheaders -t tools/apache-2.tmpl -o "Nitric Technologies Pty Ltd" -y 2021 -n "Nitric Python 3 SDK" -u "https://github.com/nitrictech/python-sdk" -d tests
	@licenseheaders -t tools/apache-2.tmpl -o "Nitric Technologies Pty Ltd" -y 2021 -n "Nitric Python 3 SDK" -u "https://github.com/nitrictech/python-sdk" -d tools

build: clean grpc-client license docs
	@echo Building sdist and wheel
	@python3 setup.py sdist bdist_wheel

distribute: build
	@echo Uploading to pypi
	@python3 -m twine upload --repository pypi dist/*

distribute-test: build
	@echo Uploading to testpypi
	@python3 -m twine upload --repository testpypi dist/*