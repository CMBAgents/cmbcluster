#!/usr/bin/env bash

. $(dirname "$0")/errorcheck.function

docker compose up -d
errorcheck "${?}"
docker compose exec api python manage.py collectstatic
errorcheck "${?}"

exit 0
