import os
import re
import shutil
import subprocess
import urllib.request

# URL for the Fedora Server downloads page
RELEASES_URL = "https://www.fedoraproject.org/en/server/download/"

# The remote mirror to rsync from
MIRROR = "mirror.rackspace.com"

# Local path for the repo mirror
REPO_MIRROR_PATH = "/mnt/storage-x/repo_mirror/fedora/"

# Regex pattern to match Fedora Server release numbers
RELEASE_PATTERN = f"Fedora Server ([0-9]+)"

# Get the latest Fedora Server release number from the website
with urllib.request.urlopen(RELEASES_URL) as response:
    html = response.read().decode("utf-8")
    match = re.search(RELEASE_PATTERN, html)
    latest_release = int(match.group(1))

# Calculate the paths for the latest release and the previous release
# I don't want the absolute latest, so I will use n - 1 for my latest
latest_release = latest_release - 1
print(f"{latest_release=}")
latest_release_path = os.path.join(REPO_MIRROR_PATH, f"releases/{latest_release}")
print(f"{latest_release_path=}")
prev_release = latest_release - 1
prev_release_path = os.path.join(REPO_MIRROR_PATH, f"releases/{prev_release}")
print(f"{prev_release_path=}")

# Sync the updates for the latest two releases
for release in [latest_release, prev_release]:
    updates_path = os.path.join(REPO_MIRROR_PATH, f"updates/{release}")
    if not os.path.exists(updates_path):
        print(f"{updates_path=}")
        os.makedirs(updates_path)
    print(f"Cloning release for {release}")
    subprocess.run(
        [
            "rsync",
            "-amH",
            "--timeout=300",
            "--exclude='drpms'",
            "--exclude='debug'",
            "--delete-after",
            f"rsync://{MIRROR}/fedora/linux/updates/{release}/Everything/x86_64/",
            updates_path,
        ]
    )
    print(f"Cloning updates for {release}")
    subprocess.run(
        [
            "rsync",
            "-amH",
            "--timeout=300",
            "--exclude='debug'",
            "--delete-after",
            f"rsync://{MIRROR}/fedora/linux/releases/{prev_release}/Server/x86_64/os/",
            prev_release_path,
        ]
    )

# Remove the synced release and updates for the oldest synced release if there are more than two releases
oldest_synced = latest_release - 2
if oldest_synced >= 0:
    oldest_release_path = os.path.join(REPO_MIRROR_PATH, f"releases/{oldest_synced}")
    oldest_updates_path = os.path.join(REPO_MIRROR_PATH, f"updates/{oldest_synced}")
    for location in [oldest_release_path, oldest_updates_path]:
        if os.path.exists(location):
            shutil.rmtree(location)
