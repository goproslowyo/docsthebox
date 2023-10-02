#!/usr/bin/env python3

import argparse
import json
import logging
from time import sleep
from typing import List, Optional

import requests

from models import Machine
from utils import WRITEUP_TEMPLATE


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
        htb_url = f"https://www.hackthebox.com/api/v4/machine/list/retired/paginated?per_page={per_page}&page={current_page}"
        headers = {
            "Authorization": f"Bearer {args.htb_token}",
            "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",
        }
        response = requests.get(htb_url, headers=headers)

        if response.status_code == requests.codes.ok:
            page_data = response.json()

            # Convert the JSON machine data to Machine objects
            for machine_data in page_data.get("data", []):
                machine = Machine(
                    machine_id=machine_data["id"],
                    name=machine_data["name"],
                    os=machine_data["os"],
                    release_date=machine_data["release"],
                    todo=machine_data["isTodo"],
                    difficulty=machine_data["difficultyText"],
                    rating=machine_data["star"],
                    machine_state=machine_data["playInfo"],
                    userOwned=machine_data["authUserInUserOwns"],
                    rootOwned=machine_data["authUserInRootOwns"],
                    image=machine_data["avatar"],
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
    with open("retired-machines.json", "w") as f:
        json.dump([machine.to_dict() for machine in machines], f, indent=2)

    return machines


def check_existing_item(machine_id: int) -> bool:
    """Checks if an item with a specific Box ID exists in the Notion database.

    Args:
        machine_id (int): The Box ID to check for.

    Returns:
        bool: True if the item exists, False otherwise.
    """
    notion_api_url = f"https://api.notion.com/v1/databases/{args.database_id}/query"
    headers = {
        "Authorization": f"Bearer {args.notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    payload = {"filter": {"property": "Box ID", "number": {"equals": machine_id}}}

    response = requests.post(notion_api_url, headers=headers, json=payload)
    if response.status_code != requests.codes.ok:
        logging.error(response.text)
        logging.error(f"Failed to check for existing item with Box ID {machine_id}")
        return False

    data = response.json().get("results", [])
    return len(data) > 0  # If there are results, an item with the Box ID already exists


def update_notion_database(machines: List[Machine]) -> None:
    """Updates a Notion database with the list of HTB machines skipping any existing machines found by machine_id.

    Args:
        machines (List[Machine]): A list of Machine objects.
    """
    notion_api_url = f"https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {args.notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }


    for machine in machines:
        machine_id = int(machine["id"])
        machine_name = machine["name"]
        logging.debug(f"machine: {machine}")
        logging.debug(f"Box Name: {machine_name}\nBox ID: {machine_id}")

        # Check if an item with the same Box ID already exists in the database
        if check_existing_item(machine_id):
            logging.warn(
                f"Item with Box ID {machine_id} for {machine_name} already exists. Skipping."
            )
            sleep(0.5)
            continue

        child_blocks = [block for block in WRITEUP_TEMPLATE]
        logging.debug(f"child_blocks: {child_blocks}")
        payload = {
            "parent": {"database_id": args.database_id, "type": "database_id"},
            "icon": {
                "type": "external",
                "external": {"url": f"https://www.hackthebox.com{machine['avatar']}"},
            },
            "cover": {
                "type": "external",
                "external": {"url": f"https://www.hackthebox.com{machine['avatar']}"},
            },
            "properties": {
                "Name": {"title": [{"text": {"content": machine.name}}]},
                "Box ID": {"number": int(machine_id)},
                "OS": {"select": {"name": machine["os"]}},
                "Release Date": {"date": {"start": machine["release"]}},
                "To Do?": {"checkbox": machine["isTodo"]},
                "Difficulty": {"select": {"name": machine["difficultyText"]}},
                "Rating": {"number": float(machine["star"])},
                "Active?": {"checkbox": machine["playInfo"]["isActive"] or False},
                "$": {"checkbox": machine["authUserInUserOwns"] or False},
                "#": {"checkbox": machine["authUserInRootOwns"] or False},
            },
            "children": child_blocks,
        }
        logging.debug(f"payload: {payload}")

        # todo(gpsy): Use NotionX client instead of requests
        response = requests.post(notion_api_url, headers=headers, json=payload)
        if response:
            logging.debug(response.status_code)
            logging.debug(response.headers)
            logging.debug(response.text)
        # Retry up to 3 times if the request fails
        if response.status_code != requests.codes.ok:
            retry = 0
            logging.error(response.text)
            logging.error(
                f"Failed to update Notion database for machine {machine_name}"
            )
            while retry < 3:
                sleep(1)
                logging.info(f"Retrying update for machine {machine_name}")
                response = requests.post(notion_api_url, headers=headers, json=payload)
                if response.status_code == requests.codes.ok:
                    break
                retry += 1
            break
        sleep(0.5)


if __name__ == "__main__":
    # Initialize logging
    logging.basicConfig(level=logging.INFO)

    # Argument parsing
    # TODO(gpsy): Make these read env vars instead of passing secrets as args
    parser = argparse.ArgumentParser(description="docsthebox: HTB Machines to Notion DB for Writeups")
    parser.add_argument("--htb-token", required=False, help="Your HTB Bearer Token")
    parser.add_argument("--notion-token", required=True, help="Your Notion API Token")
    parser.add_argument("--database-id", required=True, help="Notion Database where machines will be created")
    # Flag to skip HTB api calls and use local json file
    parser.add_argument("--local", action="store_true", help="Skip HTB API calls and use local JSON file instead")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Set debug logging if debug flag is set
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Return an error is HTB token not set but local flag is not set
    if not args.htb_token and not args.local:
        logging.error("HTB Token not set. Exiting.")
        exit(1)

    # Check if local flag is set
    if args.local:
        # Check if local file exists
        try:
            with open("retired-machines.json", "r") as f:
                logging.info(
                    "Skipping HTB API calls and using local JSON file instead."
                )
                machines = json.load(f)
                # print length
                logging.info(f"Loaded {len(machines)} Retired machines")
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
            with open("retired-machines.json", "r") as f:
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
    update_notion_database(machines)
    logging.info("Finished updating the Notion database with retired HTB machines.")
