#!/usr/bin/env bash
if test "$BASH" = "" || "$BASH" -uc "a=();true \"\${a[@]}\"" 2>/dev/null; then
    # Bash 4.4, Zsh
    set -euo pipefail
else
    # Bash 4.3 and older chokes on empty arrays with set -u.
    set -eo pipefail
fi
shopt -s nullglob globstar



create_extension() {
    printf "\n\n ###########\n
    create_extension START \n
    #############\n\n"

    psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"

    psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements CASCADE;"

    printf "\n\n create_extension END \n\n"      
}

# PostgreSQL stores TIMESTAMPTZ in UTC value.
# When you insert a value into a TIMESTAMPTZ column, PostgreSQL converts the TIMESTAMPTZ value into a UTC value and stores the UTC value in the table.
# When you query timestamptz from the database, PostgreSQL converts the UTC value back to the time value of the timezone set by the database server, the user, or the current database connection.


create_table() {
    printf "\n\n ###########\n
    create_table START \n
    #############\n\n"

    psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" -c "CREATE TABLE logs (
    timestamp   TIMESTAMPTZ       NOT NULL,
    event       TEXT              NOT NULL,
    stage       TEXT              NOT NULL,
    client_id   TEXT              NOT NULL,
    log_id      TEXT              NOT NULL,
    error       TEXT              NOT NULL,
    metadata    JSONB             NULL,

    PRIMARY KEY(timestamp)
    );"

    printf "\n\n create_table END \n\n"    
}


create_table_indices() {
     printf "\n\n ###########\n
    create_table_indices START \n
    #############\n\n"

    # you may want to index the json field
    # see: https://docs.timescale.com/v1.0/using-timescaledb/schema-management#indexing-all-json
    # psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" -c "CREATE INDEX idxgin ON logs USING GIN (metadata);"

    # An index allows the database server to find and retrieve specific rows much faster than it could do without an index.
    # For indexing columns with discrete (limited-cardinality) values; ie those that u are likely to query using "equals" or "not equals" comparator
    # as opposed to using "less than" or "greater than" comparator. For those create index with time last
    # read:
    # 1. https://www.postgresql.org/docs/11/indexes.html
    # 2. https://blog.timescale.com/use-composite-indexes-to-speed-up-time-series-queries-sql-8ca2df6b3aaa
    # 3. https://docs.timescale.com/v1.0/using-timescaledb/schema-management#indexing-best-practices
    # 4. https://info.crunchydata.com/blog/postgresql-brin-indexes-big-data-performance-with-minimal-storage
    #  ^-- Use BRIN indexes for performance and reduce index size

    psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" -c "CREATE INDEX ON logs (event, log_id, timestamp DESC NULLS LAST) WHERE event IS NOT NULL AND log_id IS NOT NULL;"

    printf "\n\n create_table_indices END \n\n"   
}

create_hypertable() {
    printf "\n\n ###########\n
    create_hypertable START \n
    #############\n\n"

    # we wont add space partition
    # see:
    # 1. https://docs.timescale.com/v1.0/getting-started/creating-hypertables
    # 2. https://docs.timescale.com/v1.0/using-timescaledb/hypertables#best-practices
    psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" -c "SELECT create_hypertable('logs', 'timestamp');"

    printf "\n\n create_hypertable END \n\n" 

}

# 1. create timescaledb extension
# 2. create database table
# 3. create  hypertable
create_extension
create_table
create_table_indices
create_hypertable