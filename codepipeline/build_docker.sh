#!/usr/bin/env bash

. $(dirname "$0")/errorcheck.function

docker build --pull -t denario-be -f ./backend/Dockerfile ./backend/
errorcheck "${?}"
docker build --pull --target runner -t  denario-fe -f ./nextjs-frontend/Dockerfile  ./nextjs-frontend/
exit "${?}"
