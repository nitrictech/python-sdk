install:
	@echo Installing Project Dependencies
	@pip3 install -e .[dev]
	@pre-commit install

OUTPUT="./nitric/proto"
CONTRACTS="./contracts/proto"

generate-proto:
	@echo Generating Proto Sources
	@echo $(OUTPUT)
	@mkdir -p $(OUTPUT)
	@python3 -m grpc_tools.protoc -I $(CONTRACTS)  --python_out=$(OUTPUT) --grpc_python_out=$(OUTPUT) ./contracts/proto/**/**/*.proto
	@python3 ./tools/fix_grpc_imports.py
	@find $(OUTPUT) -type d -exec touch {}/__init__.py \;

clean:
	@rm -rf ./build
	@rm -rf ./dist

build: clean install generate-proto
	@echo Building sdist and wheel
	@python3 setup.py sdist bdist_wheel

distribute: build
	@echo Uploading to pypi
	@python3 -m twine upload --repository pypi dist/*

distribute-test: build
	@echo Uploading to testpypi
	@python3 -m twine upload --repository testpypi dist/*