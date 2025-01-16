#!/usr/bin/env bash

pid_fpath="log/pid"
if [[ ! -f "$pid_fpath" ]]; then
  echo "No running instance"
  exit 1
fi

pid=$(cat $pid_fpath)
kill -TERM "$pid"
rm "$pid_fpath"
