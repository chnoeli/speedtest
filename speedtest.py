"""A simple python script template.
"""

import json
import os
import platform
import sys
import time
import influxdb_client
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS

HOSTNAME = os.environ.get("INFLUX_HOSTNAME", platform.node())
DB_SAVE = True if os.environ.get("DB_SAVE", "true").lower() == "true" else False

IPERF_ENABLE = (
    True if os.environ.get("IPERF_ENABLE", "false").lower() == "true" else False
)
IPERF_SERVER = os.environ.get("IPERF_SERVER", "")
IPERF_PORT = int(os.environ.get("IPERF_PORT", "5201"))
IPERF_PARALLEL = int(os.environ.get("IPERF_PARALLEL", "10"))
IPERF_MAX_RETRIES = int(os.environ.get("IPERF_MAX_RETRIES", "5"))
IPERF_RETRY_DELAY = int(os.environ.get("IPERF_RETRY_DELAY", "5"))
IPERF_BUCKET = os.environ.get("IPERF_BUCKET", "iperf")

SPEEDTEST_ENABLE = (
    True if os.environ.get("SPEEDTEST_ENABLE", "true").lower() == "true" else False
)
SPEEDTEST_BUCKET = os.environ.get("IPERF_BUCKET", "speedtest")

INFLUX_ORG = os.environ.get("INFLUX_ORG", "")
INFLUX_URL = os.environ.get("INFLUX_URL", "")
INFLUX_API_TOKEN = os.environ.get("INFLUX_API_TOKEN", "")


# print("HOSTNAME: ", HOSTNAME)
# print("DB_SAVE: ", DB_SAVE)
# print("IPERF_ENABLE: ", IPERF_ENABLE)
# print("IPERF_SERVER: ", IPERF_SERVER)
# print("IPERF_PORT: ", IPERF_PORT)
# print("IPERF_PARALLEL: ", IPERF_PARALLEL)
# print("IPERF_MAX_RETRIES: ", HOSTNAME)
# print("IPERF_RETRY_DELAY: ", HOSTNAME)
# print("IPERF_BUCKET: ", HOSTNAME)
# print("SPEEDTEST_ENABLE: ", SPEEDTEST_ENABLE)
# print("SPEEDTEST_BUCKET: ", SPEEDTEST_BUCKET)
# print("INFLUX_ORG: ", INFLUX_ORG)
# print("INFLUX_URL: ", INFLUX_URL)
# print("INFLUX_API_TOKEN: ", INFLUX_API_TOKEN)


INFLUX_CLIENT = (
    influxdb_client.InfluxDBClient(
        url=INFLUX_URL, token=INFLUX_API_TOKEN, org=INFLUX_ORG
    )
    if DB_SAVE
    else None
)


def main():
    if SPEEDTEST_ENABLE:
        print("Running speedtest-cli speedtest...")
        speedRes = runSpeedtestCli()
        speedDownload = speedRes["download"]["bandwidth"]
        speedUpload = speedRes["upload"]["bandwidth"]
        speedPing = speedRes["ping"]["latency"]
        print(
            f"Your speedtest-cli download speed is {round(speedDownload / 125000, 2)} Mbps ({speedDownload} Bytes/s)."
        )
        print(
            f"Your speedtest-cli upload speed is {round(speedUpload / 125000)} Mbps ({speedUpload} Bytes/s)."
        )
        print(f"Your speedtest-cli ping latency is {speedPing} ms.")

        if DB_SAVE:
            print("Saving speedtest-cli data to influxdb...")
            saveToInflux(SPEEDTEST_BUCKET, "download", speedDownload)
            saveToInflux(SPEEDTEST_BUCKET, "upload", speedUpload)
            saveToInflux(SPEEDTEST_BUCKET, "ping", speedPing)

    if IPERF_ENABLE:
        print("Running iperf speedtest...")
        iperfRes = runIperf(IPERF_SERVER, IPERF_PORT, IPERF_PARALLEL)
        iperfDownload = 0
        iperfUpload = 0
        if "error" in iperfRes:
            index = 0
            while "error" in iperfRes and index < IPERF_MAX_RETRIES:
                print(
                    f"iperf returned error: '{iperfRes['error']}'. Retrying... {index+1} of {IPERF_MAX_RETRIES}"
                )
                time.sleep(IPERF_RETRY_DELAY)
                iperfRes = runIperf(IPERF_SERVER, IPERF_PORT, IPERF_PARALLEL)
                index += 1

        if "end" in iperfRes:
            iperfDownload = iperfRes["end"]["sum_sent"]["bytes"]
            iperfUpload = iperfRes["end"]["sum_received"]["bytes"]
            print(
                f"Your iperf download speed is {round(iperfDownload / 125000, 2)} Mbps ({iperfDownload} Bytes/s)."
            )
            print(
                f"Your iperf upload speed is {round(iperfUpload / 125000)} Mbps ({iperfUpload} Bytes/s)."
            )

            if DB_SAVE:
                print("Saving iperf data to influxdb...")
                saveToInflux(IPERF_BUCKET, "download", iperfDownload)
                saveToInflux(IPERF_BUCKET, "upload", iperfUpload)


def runIperf(server: str, port: int, parallel: str) -> json:
    cmd = f"iperf3 -c {server} -p {port} -P {parallel} --json"
    stream = os.popen(cmd)
    output = json.loads(stream.read())
    return output


def runSpeedtestCli():
    cmd = "speedtest --accept-license --accept-gdpr -f json"
    stream = os.popen(cmd)
    output = json.loads(stream.read())
    return output


def saveToInflux(bucket: str, key: str, value: any):
    write_api = INFLUX_CLIENT.write_api(write_options=SYNCHRONOUS)
    point = Point(key).tag("host", HOSTNAME).field("value", value)
    write_api.write(bucket=bucket, org=INFLUX_ORG, record=point)


if __name__ == "__main__":
    sys.exit(main())