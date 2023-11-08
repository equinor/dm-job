#! /usr/bin/env bash
# Get the available docker-compose command
docker compose &> /dev/null
if [[ $? == 0 ]]; then
  compose="docker compose"
else
  compose="docker-compose"
fi

set -e

DMSS_URL=localhost:5000

# Wait until the storage services is ready before continuing.
# This is to ensure that the services is initialized before the API tries to connect.
service_is_ready() {
  ATTEMPT_COUNTER=1
  MAX_ATTEMPTS=100
  echo "Testing availability of DMSS: $DMSS_URL"
  until $(curl --silent --output /dev/null --fail "$DMSS_URL/api/healthcheck"); do
    if [ ${ATTEMPT_COUNTER} -eq ${MAX_ATTEMPTS} ];then
      echo "ERROR: Max attempts reached. Data Modelling Storage API($DMSS_URL) did not respond. Exiting..."
      exit 1
    fi
    echo "Waiting for $DMSS_URL... (${ATTEMPT_COUNTER})"
    ATTEMPT_COUNTER=$((ATTEMPT_COUNTER+1))
    sleep 5
  done
  echo "DMSS is ready!"
}
service_is_ready

echo "Upload Job API blueprints to DMSS"
eval $compose run --rm job-api dm --url http://dmss:5000 reset ../app