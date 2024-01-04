#!/bin/bash
set -euo pipefail
ENVIRON=${ENVIRONMENT:="production"}

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

mkdir -p /code/app/data_sources/
TEMPFILE=$(mktemp)
envsubst < /code/app/WorkflowDS_template.json > $TEMPFILE
mv $TEMPFILE /code/app/data_sources/WorkflowDS.json

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
