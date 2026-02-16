import subprocess
import json
import re
import requests
from urllib.parse import quote

DB_PATH = "known_bad_packages.json"


def run_adb_command(command):
    result = subprocess.run(["adb"] + command.split(),
                            capture_output=True, text=True)
    return result.stdout.strip()


def get_installed_packages():
    output = run_adb_command("shell pm list packages -3")
    return [line.split(":")[1] for line in output.splitlines()]


def load_known_bad_packages():
    try:
        with open(DB_PATH, "r") as f:
            return set(json.load(f))
    except:
        return set()


def save_known_bad_packages(packages):
    with open(DB_PATH, "w") as f:
        json.dump(sorted(list(packages)), f, indent=2)


def is_suspicious_package(pkg):
    suspicious_keywords = ["clean", "boost", "antivirus",
                           "vpn", "recover", "junk", "radar", "battery", "pdf", "bloodpressure", "freeup"]
    return any(keyword in pkg.lower() for keyword in suspicious_keywords)


def get_suspicious_packages(all_packages, known_bad):
    suggested = []
    known = []
    for pkg in all_packages:
        if pkg in known_bad:
            known.append(pkg)
        elif is_suspicious_package(pkg):
            suggested.append(pkg)
    return known, suggested


def get_all_other_packages(all_packages, known_bad, suggested):
    """Get all packages that are not in known_bad or suggested lists."""
    excluded = set(known_bad + suggested)
    return [pkg for pkg in all_packages if pkg not in excluded]


def uninstall_package(pkg):
    run_adb_command(f"uninstall {pkg}")


def get_play_store_url(pkg):
    """Generate Google Play Store URL for a package."""
    return f"https://play.google.com/store/apps/details?id={pkg}"


def is_valid_play_store_link(pkg):
    """Check if the Google Play Store link for a package is valid (doesn't 404)."""
    try:
        url = get_play_store_url(pkg)
        response = requests.head(url, timeout=5, allow_redirects=True)
        # Google Play returns 200 for valid apps, and usually redirects to error page for invalid ones
        if response.status_code == 200:
            # Additional check: make sure we're not redirected to an error page
            final_url = response.url
            return "store/apps/details" in final_url and "id=" in final_url
        return False
    except (requests.RequestException, Exception):
        return False
