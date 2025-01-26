import os
from typing import List, Optional, TypedDict, Dict, Any
from dotenv import load_dotenv
import requests
import json
import re

# Load environment variables
load_dotenv()

# Use the Hub API URL for fetching user data by FID and potentially for get_cast
HUB_API_URL = "https://hub-api.neynar.com"

class User(TypedDict):
    fid: int
    username: str

class Cast(TypedDict):
    hash: str
    text: str
    timestamp: str
    author: User
    reactions: Dict[str, Any]
    mentions: List[User]
    parent_hash: Optional[str]

def is_valid_username(username: str) -> bool:
    """Checks if a username is valid according to Farcaster rules."""
    return bool(re.fullmatch(r"[a-z0-9]([a-z0-9-]{0,14}[a-z0-9])?", username))

async def fetch_casts(neynar_api_key: str, channel_id: Optional[str] = None, keyword_filter: Optional[str] = None, limit: int = 100) -> List[Cast]:
    """
    Fetches casts from Farcaster, optionally filtering by channel ID and keywords.

    Args:
        neynar_api_key: The Neynar API key.
        channel_id: The ID of the channel to fetch casts from.
        keyword_filter: Optional keyword to filter casts by.
        limit: The number of casts to fetch (default 100, max 1000).

    Returns:
        A list of casts.
    """
    headers = {
        "accept": "application/json",
        "api_key": neynar_api_key,
    }

    casts = []
    cursor = None  # For pagination

    try:
        while True:
            if channel_id:
                params = {
                    "feed_type": "filter",
                    "filter_type": "channel_id",
                    "channel_id": channel_id,
                    "with_recasts": "false",
                    "limit": min(limit, 100),
                    "cursor": cursor
                }
                url = "https://api.neynar.com/v2/farcaster/feed"
            else:
                params = {
                    "with_recasts": "false",
                    "limit": min(limit, 100),
                    "cursor": cursor
                }
                url = "https://api.neynar.com/v2/farcaster/casts"

            print(f"Fetching casts from: {url} with params: {params}")

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            response_json = response.json()
            if response_json and response_json.get("casts"):
                new_casts = response_json["casts"]
                if keyword_filter:
                    new_casts = [
                        cast for cast in new_casts
                        if keyword_filter.lower() in cast["text"].lower()
                    ]
                casts.extend(new_casts)

                # Check if we've reached the limit or if there are no more pages
                if len(casts) >= limit or not response_json.get("next") or not response_json["next"].get("cursor"):
                    break

                cursor = response_json["next"]["cursor"]
            else:
                print("No more casts found.")
                break

        cast_list = []
        for cast in casts:
            author_data = cast.get('author')
            if author_data:
                author = User(fid=author_data.get('fid'), username=author_data.get('username'))
            else:
                author = None

            mentions_data = cast.get('mentions', [])
            mentions = [User(fid=mention.get('fid'), username=mention.get('username')) for mention in mentions_data]

            cast_obj = Cast(
                hash=cast['hash'],
                text=cast['text'],
                timestamp=cast['timestamp'],
                author=author,
                reactions=cast.get('reactions'),
                mentions=mentions,
                parent_hash=cast.get('parent_hash')
            )
            cast_list.append(cast_obj)

        return cast_list

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error fetching casts: {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        print(f"General error fetching casts: {e}")
        return []

async def fetch_mentions_for_fid(neynar_api_key: str, fid: int, limit: int = 100) -> List[Cast]:
    """
    Fetches mentions for a given Farcaster FID.

    Args:
        neynar_api_key: The Neynar API key.
        fid: The Farcaster FID to fetch mentions for.
        limit: The number of mentions to fetch (default 100, max 250).

    Returns:
        A list of casts mentioning the given FID.
    """
    try:
        headers = {
            "accept": "application/json",
            "api_key": neynar_api_key,
        }

        mentions = []
        cursor = None  # For pagination

        while True:
            # Fetch mentions
            params = {
                "type": 'mentions',
                "fid": fid,
                "limit": min(limit, 250),
                "cursor": cursor
            }
            url = "https://api.neynar.com/v2/farcaster/notifications"

            print(f"Fetching mentions from: {url} with params: {params}")

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            response_json = response.json()
            print(f"Response JSON for fetch_mentions_for_fid: {response_json}")

            if response_json and response_json.get("result") and response_json["result"].get("notifications"):
                new_mentions = response_json["result"]["notifications"]
                mentions.extend(new_mentions)

                # Check if we've reached the limit or if there are no more pages
                if len(mentions) >= limit or not response_json.get("next") or not response_json["next"].get("cursor"):
                    break

                cursor = response_json["next"]["cursor"]
            else:
                print("No more mentions found.")
                break

        casts = []
        for mention in mentions:
            if mention["type"] == "cast-mention":
                cast_hash = mention["cast"]["hash"]
                cast = await get_cast(neynar_api_key, cast_hash)
                if cast:
                    casts.append(cast)

        return casts
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error fetching mentions: {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        print(f"General error fetching mentions: {e}")
        return []

async def fetch_user_data(neynar_api_key: str, identifier: str, by_fid: bool = True) -> Optional[User]:
    """
    Fetches user data from Farcaster by FID or username.

    Args:
        neynar_api_key: The Neynar API key.
        identifier: The FID or username of the user.
        by_fid: Whether to fetch by FID (True) or username (False).

    Returns:
        User data object or None if the user is not found.
    """
    try:
        headers = {
            "accept": "application/json",
            "api_key": neynar_api_key,
        }

        if by_fid:
            url = f"{HUB_API_URL}/v1/userDataByFid?fid={identifier}"
        else:
            url = f"https://api.neynar.com/v1/farcaster/user-by-username?username={identifier}"

        print(f"Fetching user data from: {url}")

        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        response_json = response.json()
        print(f"Response JSON for fetch_user_data: {response_json}")

        if by_fid:
            if response_json and response_json.get("messages"):
                # Extract user data from the messages array
                for message in response_json['messages']:
                    data = message.get('data')
                    if data and data.get('userDataBody') and data['userDataBody'].get('type') == 6:
                        return User(fid=data.get('fid'), username=data['userDataBody'].get('value'))
            print(f"User data not found for FID: {identifier}")
            return None
        else:
            if response_json and response_json.get('users') and response_json['users']:
                user_data = response_json['users'][0]
                return User(fid=user_data.get('fid'), username=user_data.get('username'))
            else:
                print(f"User data not found for username: {identifier}")
                return None

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error fetching user data: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"General error fetching user data: {e}")
        return None

async def post_cast(neynar_api_key: str, text: str, signer_uuid: str, channel_id: Optional[str] = None, reply_to: Optional[str] = None) -> str:
    """
    Posts a cast to Farcaster.

    Args:
        neynar_api_key: The Neynar API key.
        text: The text of the cast.
        signer_uuid: The UUID of the signer.
        channel_id: The channel to post to (not used in this implementation).
        reply_to: The hash of the cast to reply to.

    Returns:
        Hash of the cast if successful.
    """
    headers = {
        "accept": "application/json",
        "api_key": neynar_api_key,
        "content-type": "application/json"
    }

    try:
        payload = {
            "signer_uuid": signer_uuid,
            "text": text
        }

        if reply_to:
            # Post a reply
            payload["parent_hash"] = reply_to
            url = "https://api.neynar.com/v2/farcaster/cast"
        else:
            # Post a regular cast
            url = "https://api.neynar.com/v2/farcaster/cast"

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        response_json = response.json()

        if response_json:
            return response_json["hash"]  # Assuming Neynar returns the cast hash
        else:
            print(f"Failed to post cast: {response_json}")
            return ""

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error posting cast: {e.response.status_code} - {e.response.text}")
        return ""
    except Exception as e:
        print(f"General error posting cast: {e}")
        return ""

async def get_cast(neynar_api_key: str, cast_hash: str) -> Optional[Cast]:
    """
    Gets a cast from Farcaster by its hash.
    """
    try:
        headers = {
            "accept": "application/json",
            "api_key": neynar_api_key,
        }

        url = f"{HUB_API_URL}/v1/cast"
        params = {"hash": cast_hash}

        print(f"Fetching cast from: {url} with params: {params}")

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        response_json = response.json()
        print(f"Response JSON for get_cast: {response_json}")

        # Assuming the cast data is directly returned in the response.
        cast_data = response_json

        if cast_data and cast_data.get('messages'):
            cast_msg = cast_data['messages'][0]
            author_data = cast_msg.get('data').get('castAddBody').get('author')
            if author_data:
                author = await fetch_user_data(neynar_api_key, author_data, by_fid=True)
            else:
                author = None

            mentions_data = cast_data.get('mentions', [])
            mentions = [User(fid=mention.get('fid'), username=mention.get('username')) for mention in mentions_data]

            return Cast(
                hash=cast_data['hash'],
                text=cast_data['data']['castAddBody']['text'],
                timestamp=cast_data['data']['timestamp'],
                author=author,
                reactions=cast_data.get('reactions'),
                mentions=mentions,
                parent_hash=cast_data.get('parent_hash')
            )
        else:
            print(f"Cast not found for hash: {cast_hash}")
            return None

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error fetching cast: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"General error fetching cast: {e}")
        return None