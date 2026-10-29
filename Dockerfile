FROM mysql:8.4
ENV MYSQL_ROOT_PASSWORD=yrgo \
    LANG=C.UTF-8
COPY yrgo_mystery.sql /docker-entrypoint-initdb.d/
COPY play.sh /usr/local/bin/play.sh
RUN chmod +x /usr/local/bin/play.sh \
 && printf '[client]\nuser=root\npassword=%s\nhost=127.0.0.1\ndefault-character-set=utf8mb4\n' \
      "$MYSQL_ROOT_PASSWORD" > /etc/yrgo-client.cnf
EXPOSE 3306
ENTRYPOINT ["play.sh"]
