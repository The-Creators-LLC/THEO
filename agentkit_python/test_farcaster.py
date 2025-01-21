import os
import asyncio
from dotenv import load_dotenv
from agentkit_python.cdp_agentkit_core.utils.farcaster import (
    fetch_casts,
    fetch_mentions_for_fid,
    fetch_user_data,
    get_cast,
)

# Load environment variables (make sure you have NEYNAR_API_KEY set)
load_dotenv()

async def test_fetch_casts():
    api_key = os.getenv("NEYNAR_API_KEY")
    if api_key is None:
        print("Error: NEYNAR_API_KEY environment variable not set.")
        return

    print("Testing fetch_casts...")
    casts = await fetch_casts(api_key, "thecreators", keyword_filter="FRIEND")
    print("Fetched casts:", casts)

async def test_fetch_mentions():
    api_key = os.getenv("NEYNAR_API_KEY")
    fid = os.getenv("THEO_FARCASTER_FID")
    if api_key is None or fid is None:
        print("Error: NEYNAR_API_KEY or THEO_FARCASTER_FID environment variables not set.")
        return

    try:
        fid = int(fid)  # Ensure FID is an integer
    except ValueError:
        print(f"Error: Invalid THEO_FARCASTER_FID value: {fid}. It should be an integer.")
        return

    print("\nTesting fetch_mentions...")
    mentions = await fetch_mentions_for_fid(api_key, fid)
    print("Fetched mentions:", mentions)

async def test_fetch_user_data():
    api_key = os.getenv("NEYNAR_API_KEY")
    if api_key is None:
        print("Error: NEYNAR_API_KEY environment variable not set.")
        return

    print("\nTesting fetch_user_data...")

    # Test fetching by username
    user_data = await fetch_user_data(api_key, "tonchu", by_fid=False)  # Replace with a valid username for testing
    print("User data (by username):", user_data)

    # Test fetching by FID
    fid = "408268"  # Replace with an actual FID you want to test
    user_data_by_fid = await fetch_user_data(api_key, fid)
    print("User data (by FID):", user_data_by_fid)

async def test_get_cast():
    api_key = os.getenv("NEYNAR_API_KEY")
    if api_key is None:
        print("Error: NEYNAR_API_KEY environment variable not set.")
        return

    print("\nTesting get_cast...")

    # Test fetching a cast by hash (replace with valid cast hashes for testing)
    cast_hash = "0x271c6f36992bc2e1dd2b4be1b408ff1753f63ff2"  # Replace with a valid cast hash
    cast = await get_cast(api_key, cast_hash)
    print("Fetched cast:", cast)

async def main():
    await test_fetch_casts()
    await test_fetch_mentions()
    await test_fetch_user_data()
    await test_get_cast()

if __name__ == "__main__":
    asyncio.run(main())