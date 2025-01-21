import os
from dotenv import load_dotenv
from agentkit_python.cdp_agentkit_core.actions import Action
from ..utils.farcaster import post_cast, get_cast
from ..utils.database import get_daily_leader

# Load environment variables
load_dotenv()

class HighlightCreator(Action):
    def __init__(self):
        self.neynar_api_key = os.getenv("NEYNAR_API_KEY")
        self.signer_uuid = os.getenv("SIGNER_UUID")

    async def run(self, *args, **kwargs):
        """
        Highlights the "Based Creator of the Day" on Farcaster.
        """
        print("Highlighting Based Creator of the Day...")

        leader = get_daily_leader()
        if leader:
            cast = await get_cast(self.neynar_api_key, leader["hash"])

            highlight_message = (
                f"🎉 Based Creator of the Day! 🎉\n\n"
                f"Congratulations to @{cast['author']['username']} for their awesome creation:\n\n"
                f"{cast['text']}"
            )
            cast_hash = await post_cast(
                self.neynar_api_key,
                highlight_message,
                self.signer_uuid
            )
            print(f"Highlighted Based Creator of the Day in cast: {cast_hash}")
        else:
            print("No Based Creator of the Day found for today.")