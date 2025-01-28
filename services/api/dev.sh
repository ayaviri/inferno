#!/usr/bin/env bash

pdm install
docker compose up -d # this is for the redis instance that serves the pre-computed optimal configurations
trap "docker compose down" EXIT
pdm run uvicorn main:app --reload
