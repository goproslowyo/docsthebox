#!/usr/bin/env python3

import os
import argparse
import json
import logging
from time import sleep
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

from models import Machine
from utils import WRITEUP_TEMPLATE

NOTION_DB_CACHE: List = []
NOTION_DB_LOADED = False
HTB_STORAGE_URL = "https://labs.hackthebox.com/storage"
# Hosts HTB has served box art from. Page art pointing anywhere else was set
# by the user and is never touched.
HTB_ART_HOSTS = ("hackthebox.com", "hackthebox.eu", "htb.systems")


def htb_avatar_url(avatar: str) -> str:
    """Build a full avatar URL whether HTB returns "/storage/avatars/x.png",
    "avatars/x.png" or an absolute URL."""
    if avatar.startswith(("http://", "https://")):
        return avatar
    path = avatar.lstrip("/")
    if path.startswith("storage/"):
        path = path[len("storage/") :]
    return f"{HTB_STORAGE_URL}/{path}"


def notion_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }


def notion_request(method: str, url: str, **kwargs: Any) -> requests.Response:
    """Call the Notion API, retrying on rate limits and server errors."""
    response = requests.request(method, url, headers=notion_headers(), **kwargs)
    for attempt in range(1, 4):
        if response.status_code != 429 and response.status_code < 500:
            break
        delay = float(response.headers.get("Retry-After", attempt))
        logging.warning(f"Notion returned {response.status_code}, retrying in {delay}s")
        sleep(delay)
        response = requests.request(method, url, headers=notion_headers(), **kwargs)
    return response


def is_htb_art_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in HTB_ART_HOSTS)


def art_is_stale(art: Optional[Dict[str, Any]], art_url: str) -> bool:
    """True if an icon/cover is HTB box art that differs from art_url (HTB has
    moved its images more than once, which leaves old pages pointing at dead
    links). Missing art, emoji, uploaded files and images from anywhere else
    are the user's choice and never touched."""
    if not art or art.get("type") != "external":
        return False
    current = art.get("external", {}).get("url", "")
    return current != art_url and is_htb_art_url(current)


def art_needs_repair(page: Dict[str, Any], art_url: str) -> bool:
    return any(art_is_stale(page.get(key), art_url) for key in ("icon", "cover"))


def repair_page_art(page: Dict[str, Any], art_url: str) -> bool:
    """Point a page's HTB icon and cover at art_url. Returns True on success."""
    payload = {
        key: {"type": "external", "external": {"url": art_url}}
        for key in ("icon", "cover")
        if art_is_stale(page.get(key), art_url)
    }
    if not payload:
        return True
    if args.dry_run:
        logging.info(f"[dry run] would update {', '.join(payload)} on {page['id']}")
        return True
    response = notion_request(
        "PATCH", f"https://api.notion.com/v1/pages/{page['id']}", json=payload
    )
    if response.status_code != requests.codes.ok:
        logging.error(f"Failed to update art on page {page['id']}: {response.text}")
        return False
    return True


def fetch_htb_machines() -> Optional[List[Machine]]:
    """Fetch machines from HTB.

    Returns:
        Optional[List[Machine]]: A list of Machine objects or None if fetching fails.
    """

    # Initialize variables for pagination
    per_page = 25
    current_page = 1
    machines: List[Machine] = []

    while True:
        htb_url = f"https://labs.hackthebox.com/api/v4/machine/list/retired/paginated?per_page={per_page}&page={current_page}"
        headers = {
            "Authorization": f"Bearer {htb_token}",
            "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",
        }
        response = requests.get(htb_url, headers=headers)

        if response.status_code == requests.codes.ok:
            page_data = response.json()

            # Convert the JSON machine data to Machine objects
            for machine_data in page_data.get("data", []):
                machine = Machine(
                    id=machine_data["id"],
                    name=machine_data["name"],
                    os=machine_data["os"],
                    release=machine_data["release"],
                    isTodo=machine_data["isTodo"],
                    difficultyText=machine_data["difficultyText"],
                    star=machine_data["star"],
                    playInfo=machine_data["playInfo"],
                    authUserInUserOwns=machine_data["authUserInUserOwns"],
                    authUserInRootOwns=machine_data["authUserInRootOwns"],
                    avatar=machine_data["avatar"],
                )
                machines.append(machine)

            # Check if there is a "Next &raquo; (»)" link in the meta section
            next_link = next(
                (
                    link["url"]
                    for link in page_data.get("meta", {}).get("links", [])
                    if link.get("label") == "Next &raquo;"
                ),
                None,
            )

            if next_link:
                logging.debug(f"more pages: {next_link}")
                # Extract the page number from the URL for the next request
                current_page = int(next_link.split("&page=")[1])
            else:
                logging.debug("no more pages found")
                # No more "Next »" link found, exit the loop
                break
        else:
            logging.error("Failed to fetch data from HTB API.")
            return None

    # Write the collected machine data to a JSON file for debugging
    with open("/tmp/retired-machines.json", "w") as f:
        json.dump([machine.to_dict() for machine in machines], f, indent=2)

    return machines


def load_notion_db() -> bool:
    """Fetch every page in the database into NOTION_DB_CACHE once."""
    global NOTION_DB_LOADED
    if NOTION_DB_LOADED:
        return True
    notion_api_url = f"https://api.notion.com/v1/databases/{args.database_id}/query"
    body: Dict[str, Any] = {}
    while True:
        response = notion_request("POST", notion_api_url, json=body)
        if response.status_code != requests.codes.ok:
            logging.error(response.text)
            logging.error("Failed to read the Notion database")
            return False
        data = response.json()
        NOTION_DB_CACHE.extend(
            item for item in data.get("results", []) if item["object"] == "page"
        )
        if not data.get("has_more"):
            break
        body = {"start_cursor": data.get("next_cursor")}
    NOTION_DB_LOADED = True
    logging.debug(f"Loaded {len(NOTION_DB_CACHE)} pages from Notion")
    return True


def find_existing_items(machine_id: int) -> List[Dict[str, Any]]:
    """Return every database page with this Box ID."""
    return [
        item
        for item in NOTION_DB_CACHE
        if item["properties"].get("Box ID", {}).get("number") is not None
        and int(item["properties"]["Box ID"]["number"]) == machine_id
    ]


def update_notion_database(machines: List[Machine]) -> None:
    """Adds HTB machines missing from the Notion database and repairs stale
    box art on the ones already there.

    Args:
        machines (List[Machine]): A list of Machine objects.
    """
    notion_api_url = "https://api.notion.com/v1/pages"
    if not load_notion_db():
        exit(1)

    created = repaired = failed = 0
    for machine in machines:
        machine_id = int(machine.id)
        machine_name = machine.name
        logging.debug(f"machine: {machine}")
        logging.debug(f"Box Name: {machine_name}\nBox ID: {machine_id}")

        art_url = htb_avatar_url(machine.avatar)

        # Existing pages keep their content; only stale box art is repaired
        existing = find_existing_items(machine_id)
        if existing:
            for page in existing:
                if not art_needs_repair(page, art_url):
                    continue
                logging.info(f"Repairing box art for {machine_name}")
                if repair_page_art(page, art_url):
                    repaired += 1
                else:
                    failed += 1
                if not args.dry_run:
                    sleep(0.35)
            continue

        child_blocks = [block for block in WRITEUP_TEMPLATE]
        logging.debug(f"child_blocks: {child_blocks}")
        payload = {
            "parent": {"database_id": args.database_id, "type": "database_id"},
            "icon": {
                "type": "external",
                "external": {"url": art_url},
            },
            "cover": {
                "type": "external",
                "external": {"url": art_url},
            },
            "properties": {
                "Name": {"title": [{"text": {"content": machine_name}}]},
                "Box ID": {"number": int(machine_id)},
                "OS": {"select": {"name": machine.os}},
                "Release Date": {"date": {"start": machine.release}},
                "To Do?": {"checkbox": machine.isTodo},
                "Difficulty": {"select": {"name": machine.difficultyText}},
                "Rating": {"number": float(machine.star)},
                "Active?": {"checkbox": machine.playInfo["isActive"] or False},
                "$": {"checkbox": machine.authUserInUserOwns or False},
                "#": {"checkbox": machine.authUserInRootOwns or False},
            },
            "children": child_blocks,
        }
        logging.debug(f"payload: {payload}")

        if args.dry_run:
            logging.info(f"[dry run] would create {machine_name}")
            created += 1
            continue
        response = notion_request("POST", notion_api_url, json=payload)
        if response.status_code != requests.codes.ok:
            logging.error(response.text)
            logging.error(f"Failed to add {machine_name} to the Notion database")
            failed += 1
            continue
        created += 1
        sleep(0.35)

    logging.info(
        f"{'[dry run] ' if args.dry_run else ''}"
        f"Created {created}, repaired art on {repaired}, failed {failed}."
    )


if __name__ == "__main__":
    # Initialize logging
    logging.basicConfig(level=logging.INFO)

    # Argument parsing
    parser = argparse.ArgumentParser(
        description="docsthebox: HTB Machines to Notion DB for Writeups"
    )
    parser.add_argument(
        "--database-id", required=True, help="Notion Database to update"
    )
    # Flag to skip HTB api calls and use local json file
    parser.add_argument(
        "--local",
        action="store_true",
        help="Skip HTB API calls and use local JSON file instead",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created or repaired without changing Notion",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Set debug logging if debug flag is set
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # HTB and Notion token are read from environment variables
    htb_token = os.getenv("HTB_TOKEN")
    notion_token = os.getenv("NOTION_TOKEN")

    # Check if tokens are set in environment variables
    if not htb_token and not args.local:
        logging.error("HTB Token not set in environment variables. Exiting.")
        exit(1)

    if not notion_token:
        logging.error("Notion Token not set in environment variables. Exiting.")
        exit(1)

    # Check if local flag is set
    if args.local:
        # Check if local file exists
        try:
            with open("/tmp/retired-machines.json", "r") as f:
                logging.info(
                    "Skipping HTB API calls and using local JSON file instead."
                )
                machines = json.load(f)
                # print length
                logging.info(f"Loaded {len(machines)} Retired machines")
                # For each machine, create a Machine object and load into machines list
                machines = [Machine(**machine) for machine in machines]
        # if not exists warn and use fetch_htb_machines
        except FileNotFoundError:
            logging.warning("Local JSON file not found. Fetching from HTB...")
            machines = fetch_htb_machines()
            if machines is None:
                logging.error("Could not fetch retired machines. Exiting.")
                exit(1)
    else:
        # Let the user know about the --local flag if a machines json file is found
        try:
            with open("/tmp/retired-machines.json", "r") as f:
                logging.info(
                    "!!! HINT: Found local JSON file. Use --local flag to skip the slow HTB API calls!"
                )
        except FileNotFoundError:
            pass
        # Fetch retired machines from HTB
        logging.info("Fetching retired machines from HTB...")
        machines = fetch_htb_machines()
        if machines is None:
            logging.error("Could not fetch retired machines. Exiting.")
            exit(1)

    # Update Notion database
    logging.info("Updating Notion database...")
    logging.info("This is going to take a while. Go grab a coffee.")
    logging.info("We slow this down to avoid hitting Notion API rate limits.")
    update_notion_database(machines)
    logging.info("Finished updating the Notion database with retired HTB machines.")
