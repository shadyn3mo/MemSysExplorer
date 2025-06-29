#!/usr/bin/env bash
cmake -DDynamoRIO_DIR="$DYNAMORIO_HOME"/cmake ./client
make memcount
