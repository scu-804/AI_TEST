#!/bin/bash

log_dir='log'

if [[ ! -d "$log_dir" ]]; then
	mkdir "$log_dir"
fi

gunicorn --access-logfile "$log_dir"/access_log --error-logfile "$log_dir"/error_log interface_main:app -c gunicorn.conf.py     ##--log-level=debug
