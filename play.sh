#!/bin/bash
# Starts MySQL in the background and, when run in a terminal, opens the client
# once the database is loaded.
docker-entrypoint.sh mysqld > /var/log/mysqld.log 2>&1 &
server=$!
echo "Laddar databasen, vänta..."
# The temporary init server runs with --skip-networking, so TCP only answers
# once yrgo_mystery.sql is fully loaded and the real server is up.
until mysqladmin --defaults-extra-file=/etc/yrgo-client.cnf ping >/dev/null 2>&1; do
  if ! kill -0 "$server" 2>/dev/null; then
    echo "MySQL kunde inte starta:"
    cat /var/log/mysqld.log
    exit 1
  fi
  sleep 1
done
# Without a terminal (docker run -d) just keep the server running for
# external clients such as MySQL Workbench.
if [ -t 0 ]; then
  exec mysql --defaults-extra-file=/etc/yrgo-client.cnf yrgo_mystery
fi
echo "Databasen är redo på port 3306 (användare root, lösenord $MYSQL_ROOT_PASSWORD)."
wait "$server"
