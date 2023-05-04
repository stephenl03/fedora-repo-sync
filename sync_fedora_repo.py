import os
import re
import shutil
import subprocess
import urllib.request
import logging

# URL for the Fedora Server downloads page
RELEASES_URL = "https://www.fedoraproject.org/en/server/download/"

# The remote mirror to rsync from
MIRROR = "mirror.rackspace.com"

# Local path for the repo mirror
REPO_MIRROR_PATH = "/mnt/storage-x/repo_mirror/fedora/"

# Regex pattern to match Fedora Server release numbers
RELEASE_PATTERN = f"Fedora Server ([0-9]+)"

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def sync_path(path, source, excludes=None):
    if not os.path.exists(path):
        logger.info(f"{path=} does not exist, creating...")
        os.makedirs(path)
    logger.info(f"Cloning {source} to {path}")
    command = [
        "rsync",
        "-amH",
        "--timeout=300",
        "--delete-after",
    ]
    if excludes:
        for ex in excludes:
            command.append(f"--exclude={ex}")
    command.extend(
        [
            f"rsync://{MIRROR}/fedora/linux/{source}",
            path,
        ]
    )
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error occurred while syncing {source} to {path}: {e}")


try:
    # Get the latest Fedora Server release number from the website
    with urllib.request.urlopen(RELEASES_URL) as response:
        html = response.read().decode("utf-8")
        match = re.search(RELEASE_PATTERN, html)
        latest_release = int(match.group(1))

    # Calculate the paths for the latest release and the previous release
    # I don't want the absolute latest, so I will use n - 1 for my latest
    latest_release = latest_release - 1
    prev_release = latest_release - 1
    logger.info(f"Latest release: {latest_release}")

    repo = {
        "latest_release": {
            "version": latest_release,
            "release_path": os.path.join(
                REPO_MIRROR_PATH, f"releases/{latest_release}"
            ),
            "update_path": os.path.join(REPO_MIRROR_PATH, f"updates/{latest_release}"),
        },
        "prev_release": {
            "version": prev_release,
            "release_path": os.path.join(REPO_MIRROR_PATH, f"releases/{prev_release}"),
            "update_path": os.path.join(REPO_MIRROR_PATH, f"updates/{prev_release}"),
        },
    }

    # Sync the updates for the latest two releases
    for _, v in repo.items():
        sync_path(
            path=v["release_path"],
            source=f"releases/{v['version']}/Everything/x86_64/os/",
            excludes=["debug"],
        )
        sync_path(
            path=v["update_path"],
            source=f"updates/{v['version']}/Everything/x86_64/",
            excludes=["drpms", "debug"],
        )

    # Remove the synced release and updates for the oldest synced release if there are more than two releases
    oldest_synced = latest_release - 2
    if oldest_synced >= 0:
        oldest_release_path = os.path.join(
            REPO_MIRROR_PATH, f"releases/{oldest_synced}"
        )
        oldest_updates_path = os.path.join(REPO_MIRROR_PATH, f"updates/{oldest_synced}")
        for location in [oldest_release_path, oldest_updates_path]:
            if os.path.exists(location):
                shutil.rmtree(location)
                logger.info(f"Removed {location}")

except Exception as e:
    logger.exception(f"Error occurred: {e}")
