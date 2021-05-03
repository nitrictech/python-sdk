install:
	@echo Installing Project Dependencies
	@pip3 install -e .[dev]
	@pre-commit install

OUTPUT="./nitric/proto"
CONTRACTS="./contracts/proto"

.PHONY: docs clean license

grpc-client:
	@echo Generating Proto Sources
	@echo $(OUTPUT)
	@mkdir -p $(OUTPUT)
	@python3 -m grpc_tools.protoc -I $(CONTRACTS)  --python_out=$(OUTPUT) --grpc_python_out=$(OUTPUT) ./contracts/proto/**/**/*.proto
	@python3 ./tools/fix_grpc_imports.py
	@find $(OUTPUT) -type d -exec touch {}/__init__.py \;

docs: license
	@echo Generating SDK Documentation
	@pdoc3 -f --html -o docs nitric

clean:
	@echo Cleaning Build Artefacts
	@rm -rf ./.eggs
	@rm -rf ./build
	@rm -rf ./dist

license:
	@echo Applying Apache 2 header to source files
	@licenseheaders -t tools/apache-2.tmpl -o "Nitric Technologies Pty Ltd" -y 2021 -n "Nitric Python 3 SDK" -u "https://github.com/nitrictech/python-sdk" -d nitric
	@licenseheaders -t tools/apache-2.tmpl -o "Nitric Technologies Pty Ltd" -y 2021 -n "Nitric Python 3 SDK" -u "https://github.com/nitrictech/python-sdk" -d tests
	@licenseheaders -t tools/apache-2.tmpl -o "Nitric Technologies Pty Ltd" -y 2021 -n "Nitric Python 3 SDK" -u "https://github.com/nitrictech/python-sdk" -d tools

build: clean install grpc-client apply-license
	@echo Building sdist and wheel
	@python3 setup.py sdist bdist_wheel

distribute: build
	@echo Uploading to pypi
	@python3 -m twine upload --repository pypi dist/*

distribute-test: build
	@echo Uploading to testpypi
	@python3 -m twine upload --repository testpypi dist/*