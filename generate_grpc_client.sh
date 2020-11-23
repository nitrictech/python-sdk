#!/bin/bash

# python3 -m grpc_tools.protoc --js_out=import_style=commonjs,binary:./src/interfaces --grpc_out=./src/interfaces --plugin=protoc-gen-v1=`which grpc_tools_node_protoc_plugin` -I ./contracts ./contracts/**/*.proto
CONTRACTS=./contracts/proto
OUTPUT=./nitric/proto
mkdir -p ${OUTPUT}
python3 -m grpc_tools.protoc -I ${CONTRACTS}  --python_out=${OUTPUT} --grpc_python_out=${OUTPUT} ./contracts/proto/**/*.proto
python3 ./tools/fix_grpc_imports.py