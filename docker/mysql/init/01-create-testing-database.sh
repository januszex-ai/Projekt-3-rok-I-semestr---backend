#!/bin/bash
set -e

mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" <<-EOSQL
    CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}_testing\`;
    GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}_testing\`.* TO '${MYSQL_USER}'@'%';
EOSQL
