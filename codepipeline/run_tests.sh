#!/usr/bin/env bash

. $(dirname "$0")/errorcheck.function

docker compose exec api python manage.py test
errorcheck "${?}"
docker compose down

docker compose -f docker-compose-e2e.yml build
errorcheck "${?}"

docker compose -f docker-compose-e2e.yml up -d
errorcheck "${?}"

sleep 60

docker compose -f docker-compose-e2e.yml exec e2e npm install
errorcheck "${?}"

docker compose -f docker-compose-e2e.yml exec api python manage.py migrate --settings=genomecentral.settings_e2e
errorcheck "${?}"

docker compose -f docker-compose-e2e.yml exec api python manage.py flush --settings=genomecentral.settings_e2e --no-input
errorcheck "${?}"

docker compose -f docker-compose-e2e.yml exec api python manage.py loaddata --settings=genomecentral.settings_e2e initial_dev initial_data bcl_sequencing_samples dry_1 dry_2 dry_3
errorcheck "${?}"

docker compose -f docker-compose-e2e.yml exec e2e bash -c "PLAYWRIGHT_HTML_OPEN=never npx playwright test"
errorcheck "${?}"

docker compose -f docker-compose-e2e.yml down

exit 0
