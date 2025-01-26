import os
import asyncio
from dotenv import load_dotenv
from agentkit_python.cdp_agentkit_core.agent import TheoAgent
from agentkit_python.cdp_agentkit_core.utils.database import Database
import datetime

# Import your custom actions
from agentkit_python.cdp_agentkit_core.actions.monitor_farcaster import MonitorFarcaster
from agentkit_python.cdp_agentkit_core.actions.update_leaderboard import UpdateLeaderboard
from agentkit_python.cdp_agentkit_core.actions.highlight_creator import HighlightCreator

# Load environment variables
load_dotenv()

# Global variable to track the last leaderboard update time
last_leaderboard_update = None
last_highlight_creator_run = None

async def should_update_leaderboard():
    """Checks if it's time to update the leaderboard."""
    global last_leaderboard_update
    now = datetime.datetime.now()

    if last_leaderboard_update is None or (now - last_leaderboard_update) >= datetime.timedelta(hours=4):
        last_leaderboard_update = now
        return True
    else:
        return False

async def should_highlight_creator():
    """Checks if it's time to highlight the 'Based Creator of the Day'."""
    global last_highlight_creator_run
    now = datetime.datetime.now()

    if last_highlight_creator_run is None or (now - last_highlight_creator_run) >= datetime.timedelta(days=1):
        last_highlight_creator_run = now
        return True
    else:
        return False

async def main():
    # Initialize database tables
    db = Database()
    db.create_tables()

    # Initialize THEO's actions
    monitor_farcaster_action = MonitorFarcaster()
    update_leaderboard_action = UpdateLeaderboard()
    highlight_creator_action = HighlightCreator()

    # Create an instance of THEO
    theo = TheoAgent(tools=[
            monitor_farcaster_action,
            update_leaderboard_action,
            highlight_creator_action,
        ])

    # Start THEO's main loop
    while True:
        try:
            # Run the monitoring action
            await monitor_farcaster_action.run()

            # Update and post the leaderboard every 4 hours
            if await should_update_leaderboard(): 
                await update_leaderboard_action.run()

            # Highlight the "Based Creator of the Day" daily
            if await should_highlight_creator():
                await highlight_creator_action.run()

            # Wait for a certain period (e.g., 1 hour)
            await asyncio.sleep(3600)

        except Exception as e:
            print(f"An error occurred in the main loop: {e}")
            await asyncio.sleep(60)  # Wait for 1 minute before retrying

if __name__ == "__main__":
    asyncio.run(main())