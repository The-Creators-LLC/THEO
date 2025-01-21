import os
from dotenv import load_dotenv
from agentkit_python.cdp_agentkit_core.actions import Action
from ..utils.farcaster import post_cast
from ..utils.database import get_leaderboard

# Load environment variables
load_dotenv()

class UpdateLeaderboard(Action):
    def __init__(self):
        self.signer_uuid = os.getenv("SIGNER_UUID")
        self.neynar_api_key = os.getenv("NEYNAR_API_KEY")
        self.theo_farcaster_username = os.getenv("THEO_FARCASTER_USERNAME")

    async def run(self, *args, **kwargs):
        """
        Updates and publishes the leaderboard.
        """
        print("Updating leaderboard...")
        leaderboard = get_leaderboard()
        leaderboard_cast = "🏆 Top Creators Leaderboard (Based on Nominations):\n\n"
        for i, creator in enumerate(leaderboard):
            leaderboard_cast += f"{i+1}. @{creator['username']} - {creator['points']} points\n"
        leaderboard_cast += f"\nNominate your favorite creators by tagging @{self.theo_farcaster_username} in the comments of their posts!"

        # Post the leaderboard update to Farcaster
        cast_hash = await post_cast(
            self.neynar_api_key,
            leaderboard_cast,
            self.signer_uuid
        )
        print(f"Leaderboard updated and posted to Farcaster with hash: {cast_hash}")