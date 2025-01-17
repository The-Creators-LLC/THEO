import os
from typing import List, Optional, TypedDict
from dotenv import load_dotenv
from neynar import NeynarAPIClient, CastsApi, NotificationsApi, UsersApi

# Load environment variables
load_dotenv()

class Cast(TypedDict):
    hash: str
    text: str
    timestamp: str
    author: object
    reactions: object
    mentions: List[object]
    parent_hash: Optional[str]

async def fetch_casts(neynar_api_key: str, channel_id: str, keyword_filter: Optional[str] = None) -> List[Cast]:
    """
    Fetches casts from Farcaster, optionally filtering by channel ID and keywords.

    Args:
        neynar_api_key: The Neynar API key.
        channel_id: The ID of the channel to fetch casts from.
        keyword_filter: Optional keyword to filter casts by.

    Returns:
        A list of casts.
    """
    try:
        client = NeynarAPIClient(api_key=neynar_api_key)
        casts_api = CastsApi(client)

        casts = []
        # You might need to implement pagination for large channels

        if channel_id:
            response = casts_api.get_casts_by_channel(channel_id, limit=100)  # Adjust limit as needed
        else:
            response = casts_api.get_casts(limit=100)

        if response and response.result:
            casts = response.result.casts
            if keyword_filter:
                casts = [cast for cast in casts if keyword_filter.lower() in cast.text.lower()]

        return [Cast(hash=cast.hash, text=cast.text, timestamp=cast.timestamp, author=cast.author, reactions=cast.reactions, mentions=cast.mentions) for cast in casts]
    except Exception as e:
        print(f"Error fetching casts: {e}")
        return []

async def fetch_mentions_for_fid(neynar_api_key: str, fid: int) -> List[Cast]:
    """
    Fetches mentions for a given Farcaster FID.

    Args:
        neynar_api_key: The Neynar API key.
        fid: The Farcaster FID to fetch mentions for.

    Returns:
        A list of casts mentioning the given FID.
    """
    try:
        client = NeynarAPIClient(api_key=neynar_api_key)
        notifications_api = NotificationsApi(client)

        # Fetch mentions
        response = notifications_api.get_notifications(fid, type='mention', limit=100)  # Adjust limit as needed

        if response and response.result:
            casts_hashes = [mention.cast_hash for mention in response.result.notifications]
            casts = []

            for cast_hash in casts_hashes:
                cast = client.get_cast(cast_hash).cast
                casts.append(cast)

            return [Cast(hash=cast.hash, text=cast.text, timestamp=cast.timestamp, author=cast.author, reactions=cast.reactions, mentions=cast.mentions, parent_hash=cast.parent_hash) for cast in casts]
        else:
            return []
    except Exception as e:
        print(f"Error fetching mentions: {e}")
        return []

async def fetch_user_data(neynar_api_key: str, identifier: str, by_fid: bool = True) -> object:
    """
    Fetches user data from Farcaster by FID or username.

    Args:
        neynar_api_key: The Neynar API key.
        identifier: The FID or username of the user.
        by_fid: Whether to fetch by FID (True) or username (False).

    Returns:
        User data object.
    """
    try:
        client = NeynarAPIClient(api_key=neynar_api_key)
        users_api = UsersApi(client)

        if by_fid:
            response = users_api.lookup_user(fid=identifier)
        else:
            response = users_api.lookup_user(username=identifier)

        if response and response.result:
            return response.result.user
        else:
            return None
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return None

async def post_cast(neynar_api_key: str, text: str, signer_uuid: str, channel_id: Optional[str] = None, reply_to: Optional[str] = None) -> str:
    """
    Posts a cast to Farcaster.

    Args:
        neynar_api_key: The Neynar API key.
        text: The text of the cast.
        signer_uuid: The UUID of the signer.
        channel_id: The channel to post to.
        reply_to: The hash of the cast to reply to.

    Returns:
        Hash of the cast if successful.
    """
    client = NeynarAPIClient(api_key=neynar_api_key)
    casts_api = CastsApi(client)

    try:
        if channel_id:
            # Post to channel
            response = casts_api.post_cast_to_channel(signer_uuid=signer_uuid, channel_id=channel_id, text=text)
        else:
            response = casts_api.post_cast(signer_uuid=signer_uuid, text=text, reply_to=reply_to)

        if response and response.result:
            return response.result.hash
        else:
            print(f"Failed to post cast: {response}")
            return ""

    except Exception as e:
        print(f"Error posting cast: {e}")
        return ""

async def get_cast(neynar_api_key: str, cast_hash: str) -> Cast:
    """
    Gets a cast from Farcaster by its hash.
    """
    client = NeynarAPIClient(api_key=neynar_api_key)
    cast = client.get_cast(cast_hash).cast

    return Cast(hash=cast.hash, text=cast.text, timestamp=cast.timestamp, author=cast.author, reactions=cast.reactions, mentions=cast.mentions, parent_hash=cast.parent_hash)