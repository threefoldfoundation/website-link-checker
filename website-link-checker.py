import json
import argparse
import subprocess
import shutil
import sys
import requests

# Timeout in seconds used for both muffet and retries via requests if enabled
TIMEOUT = 30

# We retry certain codes using requests, because sites seem to block muffet by
# returning these codes, even if we limit it to a single simultaneous request
# per host and spoof the user agent. Not sure why requests is different, but
# this helps reduce false positives significantly
RETRY_CODES = ["403", "429"]

# We also retry on certain messages that muffet returns
RETRY_MSGS = ["not found", "timeout", "couldn't find DNS entries", "server closed connection"]

# Nothing special about this, just a believable user agent
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def get_headers(url):
    """
    Download only the headers of an http response and then close the connection.
    Since we only care about the response code, no need to download the site
    """
    try:
        with requests.get(url, stream=True, headers=HEADERS, timeout=TIMEOUT) as response:
            return response.ok
    except:
        return False

parser = argparse.ArgumentParser(
    prog="muffet error filter",
    description="This program calls muffet on a whole website and filters errors. Exits with error code 1 if at least one error is found, as specified with --errors flag. Otherwise exits with code 0.",
)

parser.add_argument("url", help="The URL to scan. Please include https:// or http://")
parser.add_argument(
    "-e",
    "--errors",
    nargs='+',
    help="Specify one, many or all error codes to be filtered (e.g. -e 404, -e 403 404, -e all). Use -e all to show all errors.",
)
parser.add_argument(
    "-w",
    "--warnings",
    nargs='+',
    help="Specify one, many or all error codes to be filtered as warnings (e.g. -w 404, -w 403 404, -w all). Use -w all to show all warnings.",
)
parser.add_argument(
    "-r",
    "--retry",
    action="store_true",
    help="Retry 403 and 429 codes using python requests. This adds time but reduces false positives.",
)

args = parser.parse_args()

if args.errors is None:
    errors = list()
elif args.errors and args.errors[0] == "all":
    errors = "all"
else:
    errors = args.errors

if args.warnings is None:
    warnings = list()
elif args.warnings and args.warnings[0] == "all":
    warnings = "all"
else:
    warnings = args.warnings

# If muffet isn't on PATH, check a couple other likely spots
muffet_path = shutil.which("muffet")
if not muffet_path:
    if shutil.os.path.isfile("/muffet"):
        muffet_path = "/muffet"
    elif shutil.os.path.isfile("./muffet"):
        muffet_path = shutil.os.path.realpath("./muffet")
    else:
        raise Exception("Couldn't find muffet")

proc = subprocess.run(
    [
        muffet_path,
        "--timeout=" + str(TIMEOUT),
        "--color=always",
        "--buffer-size=8192",
        "--format=json",
        args.url,
    ],
    capture_output=True,
)

data = json.loads(proc.stdout)

has_error = False
filtered_data = {}
for page in data:
    for link in page["links"]:
        error = link["error"].split()[0]
        if (errors == "all" and error not in warnings) or error in errors:
            alerts = filtered_data.setdefault(page["url"], {"errors": {}, "warnings": {}})
            alerts["errors"][link["url"]] = link["error"]
            has_error = True
        elif warnings == "all" or error in warnings:
            alerts = filtered_data.setdefault(page["url"], {"errors": {}, "warnings": {}})
            alerts["warnings"][link["url"]] = link["error"]

if args.retry:
    # Since links appearing on multiple pages will be duplicated in muffet's
    # report, keep track of any detected false positives to avoid rechecking
    false_positives = []
    for page, alerts in filtered_data.items():
        for alert in ["errors", "warnings"]:
            for link_url, error in list(alerts[alert].items()):
                if link_url in false_positives:
                    alerts[alert].pop(link_url)
                # Only match the exact code here. In case there's more info
                # like a redirect, we can retain it
                elif error in RETRY_CODES or [True for msg in RETRY_MSGS if msg in error]:
                    ok = get_headers(link_url)
                    if ok:
                        false_positives.append(link_url)
                        alerts[alert].pop(link_url)

    # Remove any pages for which all alerts cleared
    for page, alerts in list(filtered_data.items()):
        if not (alerts["errors"] or alerts["warnings"]):
            filtered_data.pop(page)

print()
for page_url, alerts in filtered_data.items():
    heading = "Found on page: " + page_url
    print(heading)
    print("=" * len(heading))
    try:
        for link_url, error in alerts["errors"].items():
            print("Error {} -> {}".format(error, link_url))
    except KeyError:
        pass
    try:
        for link_url, error in alerts["warnings"].items():
            print("Warning {} -> {}".format(error, link_url))
    except KeyError:
        pass
    print()

# Exit with exit(1) if the website contains at least one error. Otherwise, exit with exit(0).
if has_error:
    sys.exit(1)
else:
    sys.exit(0)