import os
from dotenv import load_dotenv
from agentkit_python.cdp_agentkit_core.actions import Action
from ..utils.farcaster import (
    fetch_casts,
    fetch_mentions_for_fid,
    fetch_user_data,
    post_cast,
    get_cast,
)
from ..utils.database import (
    get_user,
    create_user,
    get_post,
    create_post,
    record_nomination,
    get_daily_leader,
    mark_based_creator_of_the_day,
)

# Load environment variables
load_dotenv()

class MonitorFarcaster(Action):
    def __init__(self):
        self.neynar_api_key = os.getenv("NEYNAR_API_KEY")
        self.theo_farcaster_fid = os.getenv("THEO_FARCASTER_FID")
        self.theo_farcaster_username = os.getenv("THEO_FARCASTER_USERNAME")
        self.base_channel_id = "base"

    async def run(self, *args, **kwargs):
        """
        Monitors Farcaster for relevant activity.
        """
        print("Monitoring Farcaster...")

        # Fetch and process new casts
        casts = await fetch_casts(
            self.neynar_api_key,
            self.base_channel_id,
            keyword_filter="Today on Base I created...",
        )
        for cast in casts:
            await self.process_cast(cast)

        # Fetch and process mentions of THEO
        mentions = await fetch_mentions_for_fid(
            self.neynar_api_key, self.theo_farcaster_fid
        )
        for mention in mentions:
            await self.process_mention(mention)

    async def process_cast(self, cast):
        """
        Processes a cast to extract relevant information and take actions.
        """
        author_fid = cast["author"]["fid"]
        author_username = cast["author"]["username"]

        # Check if user exists in the database, if not create them
        existing_user = get_user(author_fid)
        if existing_user is None:
            user_data = await fetch_user_data(self.neynar_api_key, author_fid)
            create_user(user_data["fid"], user_data["username"])

        # Check if post exists, if not create it
        existing_post = get_post(cast["hash"])
        if existing_post is None:
            create_post(
                author_fid,
                author_username,
                cast["text"],
                cast["reactions"]["likes"]["count"],
                cast["timestamp"],
                cast["hash"],
            )

        # Check if this post has the most likes for the day
        if self.is_most_liked_post_of_the_day(cast):
            # Mark the author as "Based Creator of the Day"
            mark_based_creator_of_the_day(author_fid)
            # Highlight the post
            await self.highlight_post(cast)

    async def process_mention(self, mention):
        """
        Processes a mention of THEO to record nominations.
        """
        # Check if the mention is a reply to another cast and contains a nomination
        if mention["parent_hash"]:
            parent_cast = await get_cast(self.neynar_api_key, mention["parent_hash"])

            nominator_fid = mention["author"]["fid"]
            nominated_post = parent_cast
            nominee_fid = nominated_post["author"]["fid"]

            # Check if the nominator is the same as the nominee
            if nominator_fid == nominee_fid:
                print("User cannot nominate themselves.")
                return

            # Check if user exists in the database, if not create them
            existing_nominator = get_user(nominator_fid)
            if existing_nominator is None:
                nominator_data = await fetch_user_data(
                    self.neynar_api_key, nominator_fid
                )
                create_user(nominator_data["fid"], nominator_data["username"])

            # Check if nominee exists in the database, if not create them
            existing_nominee = get_user(nominee_fid)
            if existing_nominee is None:
                nominee_data = await fetch_user_data(
                    self.neynar_api_key, nominee_fid
                )
                create_user(nominee_data["fid"], nominee_data["username"])

            # Check if post exists, if not create it
            existing_post = get_post(nominated_post["hash"])
            if existing_post is None:
                create_post(
                    nominee_fid,
                    nominated_post["author"]["username"],
                    nominated_post["text"],
                    nominated_post["reactions"]["likes"]["count"],
                    nominated_post["timestamp"],
                    nominated_post["hash"],
                )

            # Record the nomination
            record_nomination(
                nominator_fid, nominee_fid, nominated_post["hash"], mention["timestamp"]
            )

            # THEO responds to the cast (optional)
            response = f"Thanks for the nomination, @{existing_nominator}! I've recorded it."
            # You would need to use THEO's account to sign this and post it
            await post_cast(
                self.neynar_api_key,
                response,
                os.getenv("SIGNER_UUID"),
                reply_to=mention["hash"],
            )

    def is_most_liked_post_of_the_day(self, cast):
        """
        Checks if a given cast is a "Today on Base I created..." post with the most likes for the day.
        """
        current_leader = get_daily_leader()
        return (
            current_leader is None
            or cast["reactions"]["likes"]["count"] > current_leader["likes"]
        )

    async def highlight_post(self, cast):
        """
        Highlights the given cast and its author by reposting it with a message.
        """
        highlight_message = f"🎉 Based Creator of the Day! 🎉\n\nCongratulations to @{cast['author']['username']} for their awesome creation:\n\n{cast['text']}"

        # You would need to use THEO's account to sign this and post it.
        print(highlight_message)