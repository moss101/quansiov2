#!/bin/sh
# Identity isolation for the qualification environment.
# Runs once on first volume initialization as the postgres superuser.
set -eu
psql -v ON_ERROR_STOP=1 -U quansio_admin <<-SQL
CREATE ROLE quansio_app LOGIN PASSWORD '${QUAL_PG_APP_PASSWORD}';
CREATE DATABASE quansio_platform OWNER quansio_app;
CREATE DATABASE quansio_events OWNER quansio_app;
REVOKE ALL ON DATABASE quansio_platform FROM PUBLIC;
REVOKE ALL ON DATABASE quansio_events FROM PUBLIC;
SQL
