#!/bin/bash
# These values can be overwritten with env variables
LOOP="${LOOP:-false}"
LOOP_DELAY="${LOOP_DELAY:-60}"
DB_SAVE="${DB_SAVE:-false}"

DB_HOST="${DB_HOST:-http://localhost:8086}"
DB_API_TOKEN="${DB_API_TOKEN:-uuid-like-val-from-influxdb2}"
DB_ORG="${DB_ORG:-domain.com}"
DB_BUCKET="${DB_BUCKET:-speedtest}"

HOST="${HOST:-$(hostname)}"

run_speedtest() {
    DATE=$(date +%s)
    HOSTNAME=$HOST

    # Start speed test
    echo "Running a Speed Test..."
    JSON=$(speedtest --accept-license --accept-gdpr -f json)
    DOWNLOAD="$(echo $JSON | jq -r '.download.bandwidth')"
    UPLOAD="$(echo $JSON | jq -r '.upload.bandwidth')"
    PING="$(echo $JSON | jq -r '.ping.latency')"
    echo "Your download speed is $(($DOWNLOAD / 125000)) Mbps ($DOWNLOAD Bytes/s)."
    echo "Your upload speed is $(($UPLOAD / 125000)) Mbps ($UPLOAD Bytes/s)."
    echo "Your ping is $PING ms."

    # Save results in the database
    if $DB_SAVE; then
        echo " "
        echo "Saving values to database..."
        echo " "

        curl -s -S --location "$DB_HOST/api/v2/write?bucket=$DB_BUCKET&precision=s&org=$DB_ORG" \
            --header 'Accept: application/json' \
            --header 'Content-Type: text/plain' \
            --header "Authorization: Token $DB_API_TOKEN" \
            --data "download,host=$HOSTNAME value=$DOWNLOAD $DATE"

        curl -s -S --location "$DB_HOST/api/v2/write?bucket=$DB_BUCKET&precision=s&org=$DB_ORG" \
            --header 'Accept: application/json' \
            --header 'Content-Type: text/plain' \
            --header "Authorization: Token $DB_API_TOKEN" \
            --data "upload,host=$HOSTNAME value=$UPLOAD $DATE"

        curl -s -S --location "$DB_HOST/api/v2/write?bucket=$DB_BUCKET&precision=s&org=$DB_ORG" \
            --header "Authorization: Token $DB_API_TOKEN" \
            --header 'Content-Type: text/plain' \
            --header 'Accept: application/json' \
            --data "ping,host=$HOSTNAME value=$PING $DATE"

        echo " "
        echo "Values saved."
    fi
}

if $LOOP; then
    while :; do
        run_speedtest
        echo "Running next test in ${LOOP_DELAY}s..."
        echo ""
        sleep $LOOP_DELAY
    done
else
    run_speedtest
fi
