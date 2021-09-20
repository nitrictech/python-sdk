install:
	@echo Installing Project Dependencies
	@pip3 install -e .[dev]
	@pre-commit install

.PHONY: docs clean license

docs:
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

build: clean install license docs
	@echo Building sdist and wheel
	@python3 setup.py sdist bdist_wheel

distribute: build
	@echo Uploading to pypi
	@python3 -m twine upload --repository pypi dist/*

distribute-test: build
	@echo Uploading to testpypi
	@python3 -m twine upload --repository testpypi dist/*