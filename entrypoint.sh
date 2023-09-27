#!/bin/bash

echo "Docker container has been started"

#Prepare cron env
declare -p | grep -Ev 'BASHOPTS|BASH_VERSINFO|EUID|PPID|SHELLOPTS|UID' > /app/container.env
CRON="${CRON:-"*/10 * * * *"}"


# Setup a cron schedule
echo "SHELL=/bin/bash
BASH_ENV=/app/container.env
$CRON /usr/local/bin/python /app/speedtest.py >> /app/cron.log 2>&1
# This extra line makes it a valid cron" > scheduler.txt

# Create log file
touch /app/cron.log

crontab scheduler.txt
cron
tail -f /app/cron.log