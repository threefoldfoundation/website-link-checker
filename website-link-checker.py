import json
import argparse
import subprocess
import shutil
import sys

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

# Try to find muffet on PATH. If not, assume it's in the pwd
muffet_path = shutil.which("muffet")
if not muffet_path:
    muffet_path = "./muffet"

proc = subprocess.run(
    [
        muffet_path,
        "--timeout=30",
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
for item in data:
    for link in item["links"]:
        error = link["error"].split()[0]
        if (errors == "all" and error not in warnings) or error in errors:
            alerts = filtered_data.setdefault(item["url"], {})
            alerts.setdefault("errors", []).append(link)
            has_error = True
        elif warnings == "all" or error in warnings:
            alerts = filtered_data.setdefault(item["url"], {})
            alerts.setdefault("warnings", []).append(link)

print()
for url, alerts in filtered_data.items():
    heading = "Found on page: " + url
    print(heading)
    print("=" * len(heading))
    try:
        for link in alerts["errors"]:
            print("Error {} -> {}".format(link["error"], link["url"]))
    except KeyError:
        pass
    try:
        for link in alerts["warnings"]:
            print("Warning {} -> {}".format(link["error"], link["url"]))
    except KeyError:
        pass
    print()

# Exit with exit(1) if the website contains at least one error. Otherwise, exit with exit(0).
if has_error:
    sys.exit(1)
else:
    sys.exit(0)