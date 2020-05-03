#!/bin/bash

rm -rf var/db.sqlite3
mkdir -p var
sqlite3 var/db.sqlite3 < sql/schema.sql
sqlite3 var/db.sqlite3 < sql/data.sql