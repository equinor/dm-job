#!/usr/bin/env bash

# DMSS must be running locally on port 5000
# Must be run from repository root, and will create folder 'dmss-api' under ./src

# !NOTE!
# The generated code is not correctly scoped. Need to do a search and replace "from dmss_api" -> "from dm_cli.dmss_api"

echo "Creating DMSS Python package version $PACKAGE_VERSION"
docker run --rm \
--network="host" \
-v ${PWD}/src/dmss_api:/local/dm-job/dmss_api/ \
openapitools/openapi-generator-cli:v5.2.1 generate \
-i http://localhost:5000/openapi.json  \
-g python \
-o /local/dm-job \
--additional-properties=packageName=dmss_api