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

NITRIC_VERSION := 1.1.0

download-local:
	@rm -r ./proto/nitric
	@mkdir ./proto/nitric
	@cp -r ${NITRIC_CORE_HOME}/nitric/proto ./proto/nitric

download:
	@mkdir -p ./proto/
	@curl -L https://github.com/nitrictech/nitric/releases/download/v${NITRIC_VERSION}/proto.tgz -o ./proto/nitric.tgz
	@cd ./proto && tar xvzf nitric.tgz
	@cd ../
	@rm ./proto/nitric.tgz

OUTPUT="."
CONTRACTS="./proto"

grpc-client: install download generate-proto
	@mv ./nitric/proto/KeyValue ./nitric/proto/keyvalue

generate-proto:
	@echo Generating Proto Sources
	@ rm -rf $(OUTPUT)/nitric/proto
	@echo $(OUTPUT)
	@mkdir -p $(OUTPUT)
	@python3 -m grpc_tools.protoc -I $(CONTRACTS) --python_betterproto_out=$(OUTPUT) ./$(CONTRACTS)/nitric/proto/*/*/*.proto

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