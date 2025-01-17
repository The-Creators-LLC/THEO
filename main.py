import os
import asyncio
from dotenv import load_dotenv
from agentkit_python.agent import TheoAgent # Now imports correctly

# Import your custom actions
from agentkit_python.actions.monitor_farcaster import MonitorFarcaster
from agentkit_python.actions.update_leaderboard import UpdateLeaderboard
from agentkit_python.actions.highlight_creator import HighlightCreator

# Import database functions
from agentkit_python.utils.database import create_tables

# Load environment variables
load_dotenv()

async def main():
    # Initialize database tables
    create_tables()

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
        # Example: Run the monitoring action
        await monitor_farcaster_action.run()

        # Example: Update and post the leaderboard every 4 hours
        if should_update_leaderboard():  # Implement this function based on your schedule
            await update_leaderboard_action.run()

        # Example: Highlight the "Based Creator of the Day" daily
        if should_highlight_creator():  # Implement this function based on your schedule
            await highlight_creator_action.run()

        # Wait for a certain period (e.g., 1 hour)
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())