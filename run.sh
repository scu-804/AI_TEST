#!/bin/bash


gunicorn interface_main:app -c gunicorn.conf.py     ##--log-level=debug
