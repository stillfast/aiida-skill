#!/usr/bin/env bash
# Create the AiiDA profile declared in install/config.env.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/config.env"

if verdi profile list 2>/dev/null | grep -qx "\* $PROFILE_NAME\|\s*$PROFILE_NAME" ; then
  echo "[02-profile] profile '$PROFILE_NAME' already exists"; exit 0
fi

case "$PROFILE_BACKEND" in
  sqlite)
    mkdir -p "$PROFILE_FILEPATH"
    verdi profile setup core.sqlite_dos -n \
      -p "$PROFILE_NAME" --set-as-default \
      --email "$AIIDA_EMAIL" --first-name "$AIIDA_FIRST_NAME" \
      --last-name "$AIIDA_LAST_NAME" --institution "$AIIDA_INSTITUTION" \
      --broker zmq --filepath "$PROFILE_FILEPATH"
    ;;
  psql)
    verdi profile setup core.psql_dos -n \
      --profile-name "$PROFILE_NAME" --set-as-default \
      --email "$AIIDA_EMAIL" --first-name "$AIIDA_FIRST_NAME" \
      --last-name "$AIIDA_LAST_NAME" --institution "$AIIDA_INSTITUTION" \
      --use-rabbitmq \
      --database-username "$DB_USERNAME" --database-password "$DB_PASSWORD" \
      --database-name "$DB_NAME" --database-engine postgresql_psycopg \
      --database-hostname "$DB_HOST" --database-port "$DB_PORT" \
      --repository-uri "$REPOSITORY_URI"
    ;;
  *) echo "PROFILE_BACKEND must be sqlite or psql" >&2; exit 1 ;;
esac

verdi daemon start || true
verdi status || true
