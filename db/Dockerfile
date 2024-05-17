FROM postgres:latest

ARG DB_REPL_PASSWORD=default_password
ARG DB_REPL_USER=default_user
ARG DB_DATABASE=default_database

RUN test "$DB_REPL_PASSWORD" != "default_password" && \
    test "$DB_REPL_USER" != "default_user" && \
    test "$DB_DATABASE" != "default_database" || \
    { echo "ERROR: Please provide values for build arguments: DB_REPL_PASSWORD, DB_REPL_USER, DB_DATABASE"; exit 1; }
COPY init.sql /docker-entrypoint-initdb.d/

RUN apt update && apt install sed && apt install postgresql-client

RUN sed -i "s/%REPLUSER_PASSWORD%/$DB_REPL_PASSWORD/g" /docker-entrypoint-initdb.d/init.sql
RUN sed -i "s/%DB_REPL_USER%/$DB_REPL_USER/g" /docker-entrypoint-initdb.d/init.sql
RUN sed -i "s/%DBNAME%/$DB_DATABASE/g" /docker-entrypoint-initdb.d/init.sql

RUN mkdir -p /oracle/pg_data/archive/ && chown -R postgres:postgres /oracle/pg_data/archive/