#!/usr/bin/env bash

pdm export -o requirements.txt
git add .
git commit
