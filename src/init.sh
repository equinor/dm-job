#!/bin/bash
set -eu
ENVIRON=${ENVIRONMENT:="production"}
API_ENV=${API_ENV:="production"}

# Wait until the storage services is ready before continuing.
# This is to ensure that the services is initialized before the API tries to connect.
service_is_ready() {
  ATTEMPT_COUNTER=1
  MAX_ATTEMPTS=100
  echo "Testing availability of DMSS: $DMSS_API"
  until $(curl --silent --output /dev/null --fail "$DMSS_API/api/healthcheck"); do
    if [ ${ATTEMPT_COUNTER} -eq ${MAX_ATTEMPTS} ];then
      echo "ERROR: Max attempts reached. Data Modelling Storage API($DMSS_API) did not respond. Exiting..."
      exit 1
    fi

    echo "Waiting for $DMSS_API... (${ATTEMPT_COUNTER})"
    ATTEMPT_COUNTER=$((ATTEMPT_COUNTER+1))
    sleep 5
  done
  echo "DMSS is ready!"
}

install_dmss_package() {
  if [ ! -e /dmss_api/setup.py ]; then
    echo "WARNING: Tried to install local version of the DMSS-API, but it could not be found. Continuing with version from Pypi..."
  else
    echo "Installing DMSS-API from local..."
    pip uninstall dmss-api -y -q
    pip install -e /dmss_api/ -q
  fi
}

# Try to install the local version of the DMSS-API pypi package. Soft fail.
if [ "$ENVIRON" = 'local' ] && [ "$API_ENV" = 'development' ]; then
  install_dmss_package
fi

if [ "${DATA_SOURCE_FILES:-""}" != "" ]; then
  cat /code/app/data_sources/WorkflowDS.json
  echo "$DATA_SOURCE_FILES" > /code/app/data_sources/WorkflowDS.json
fi

if [ "$1" = 'api' ]; then
  service_is_ready

  if [ "$ENVIRON" != "local" ]; then
    cat version.txt || true
    gunicorn app:create_app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000
  else
    python ./app.py run
  fi
else
  exec "$@"
fi
