import json
import argparse
import subprocess
import shutil
import sys
import time
import itertools
import requests.exceptions
import requests_futures.sessions

# Timeout in seconds used for both muffet and retries via requests if enabled
TIMEOUT = 30

# Max worker threads for parallel retry requests
WORKERS = 100

# Sometimes decoding muffet json output fails (not sure why), so we retry this
# many times by running muffet again
MUFFET_RETRIES = 2

# We retry certain codes using requests, because sites seem to block muffet by
# returning these codes, even if we limit it to a single simultaneous request
# per host and spoof the user agent. Not sure why requests is different, but
# this helps reduce false positives significantly
RETRY_CODES = ["403", "429"]

# We also retry on certain messages that muffet returns
RETRY_MSGS = ["not found", "timeout", "timed out", "couldn't find DNS entries", "server closed connection"]

# Nothing special about this, just a believable user agent
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def get_headers_concurrent(urls):
    urls = set(urls) # Remove any duplicates
    session = requests_futures.sessions.FuturesSession(max_workers=WORKERS)
    futures = []
    for url in urls:
        futures.append(session.get(url, stream=True, headers=HEADERS, timeout=TIMEOUT))
    responses = []
    for future in futures:
        try:
            response = future.result()
            response.close()
            responses.append(response)
        except requests.exceptions.ReadTimeout:
            # We only care about okay responses, so timeouts can be discarded
            pass
    return responses

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

for i in range(MUFFET_RETRIES):
    try:
        muffet_start = time.time()
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
        muffet_end = time.time()

        data = json.loads(proc.stdout)
        break

    except json.decoder.JSONDecodeError:
        if i == MUFFET_RETRIES:
            print("Muffet retry limit reached.")
            raise

has_error = False
muffet_links = set() # Track total links checked by muffet for stats
filtered_data = {}
for page in data:
    for link in page["links"]:
        muffet_links.add(link['url'])
        error = link["error"].split()[0]
        if (errors == "all" and error not in warnings) or error in errors:
            alerts = filtered_data.setdefault(page["url"], {"errors": [], "warnings": []})
            alerts["errors"].append((link["url"], link["error"]))
            has_error = True
        elif warnings == "all" or error in warnings:
            alerts = filtered_data.setdefault(page["url"], {"errors": [], "warnings": []})
            alerts["warnings"].append((link["url"], link["error"]))

if args.retry:
    # Make a list of urls that match the retry criteria
    retry_urls = set()
    for alerts in filtered_data.values():
        for link_url, error in alerts["errors"] + alerts["warnings"]:
            if error in RETRY_CODES or [True for msg in RETRY_MSGS if msg in error]:
                    retry_urls.add(link_url)

    retry_start = time.time()
    responses = get_headers_concurrent(retry_urls)
    retry_end = time.time()

    # Make a set (for fast "in") of urls that turned out to be okay. In case of
    # redirect, the original url appears in history[0]. TODO: convert redirects
    # into errors/warnings when appropriate
    ok_urls = {(r.history or [r])[0].url for r in responses if r.ok}

    # Now filter the results again and discard links that are actually okay
    for alerts in filtered_data.values():
        for alert, links in alerts.items():
            alerts[alert] = [a for a in links if a[0] not in ok_urls]

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
        for link_url, error in alerts["errors"]:
            print("Error {} -> {}".format(error, link_url))
    except KeyError:
        pass
    try:
        for link_url, error in alerts["warnings"]:
            print("Warning {} -> {}".format(error, link_url))
    except KeyError:
        pass
    print()

print()
print("{} errors found by muffet in {:.2f} seconds".format(len(muffet_links), muffet_end - muffet_start))
if args.retry:
    print("{} links retried and {} okay urls found in {:.2f} seconds".format(len(retry_urls), len(ok_urls), retry_end - retry_start))

# Exit with exit(1) if the website contains at least one error. Otherwise, exit with exit(0).
if has_error:
    print()
    sys.exit(1)
else:
    sys.exit(0)