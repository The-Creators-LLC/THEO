import os
import asyncio
from dotenv import load_dotenv
from agentkit_python.cdp_agentkit_core.agent import TheoAgent
from agentkit_python.cdp_agentkit_core.utils.database import Database
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Import your custom actions
from agentkit_python.cdp_agentkit_core.actions.monitor_farcaster import MonitorFarcaster
from agentkit_python.cdp_agentkit_core.actions.update_leaderboard import UpdateLeaderboard
from agentkit_python.cdp_agentkit_core.actions.highlight_creator import HighlightCreator

# Load environment variables
load_dotenv()

# Global variable to track the last leaderboard update time
last_leaderboard_update = None
last_highlight_creator_run = None

# Create a database instance
db = Database()

# Create an instance of THEO globally
theo = None

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Hello! I'm THEO, your onchain helper. "
        "I track 'Today on Base I created...' posts and help run the daily leaderboard. "
        "Tag me in comments to nominate creators!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the /help command is issued."""
    await update.message.reply_text('Here are some commands to get started with: \n /start - starts the bot \n /help - get help \n /leaderboard - display the current leaderboard \n /todayonbase - display the current "Today on Base I created" highlights')

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the current leaderboard."""
    leaderboard_data = db.get_leaderboard()
    leaderboard_string = db.format_leaderboard(leaderboard_data)
    await update.message.reply_text(leaderboard_string)

async def today_on_base(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Displays the current "Today on Base I created" highlights.
    Fetches the top 3 most liked "Today on Base I created" posts from the last 24 hours.
    """
    try:
        # Get the current time
        now = datetime.datetime.now()

        # Calculate the start time (24 hours ago)
        start_time = now - datetime.timedelta(days=1)

        # Format the start time as an ISO 8601 string (YYYY-MM-DDTHH:MM:SS)
        start_time_str = start_time.isoformat()

        # Fetch the top 3 most liked posts from the last 24 hours
        top_posts = db.get_most_liked_posts(start_time_str, limit=3)

        if top_posts:
            highlights = "Today on Base I created highlights:\n"
            for post in top_posts:
                highlights += f"• @{post['username']} - {post['text'][:50]}... ({post['likes']} likes)\n"  # Limit text to 50 characters
            await update.message.reply_text(highlights)
        else:
            await update.message.reply_text("No 'Today on Base I created' highlights found for today.")

    except Exception as e:
        print(f"Error in today_on_base: {e}")
        await update.message.reply_text("An error occurred while fetching highlights.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming messages and passes them to the agent."""
    global theo
    if theo:
        response = await theo.handle_message(update.message.text)
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("THEO agent is not initialized.")

async def monitor_farcaster_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers the MonitorFarcaster action."""
    global monitor_farcaster_action
    await update.message.reply_text("Running MonitorFarcaster action...")
    await monitor_farcaster_action.run()

async def update_leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers the UpdateLeaderboard action."""
    global update_leaderboard_action
    await update.message.reply_text("Running UpdateLeaderboard action...")
    await update_leaderboard_action.run()

async def highlight_creator_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers the HighlightCreator action."""
    global highlight_creator_action
    await update.message.reply_text("Running HighlightCreator action...")
    await highlight_creator_action.run()

async def main():
    global theo
    # Initialize database tables
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
    
    # Set up Telegram bot application
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if telegram_token is None:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        return
    application = ApplicationBuilder().token(telegram_token).build()

    # Add handlers for commands and messages
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("todayonbase", today_on_base))
    application.add_handler(CommandHandler("monitor", monitor_farcaster_command))
    application.add_handler(CommandHandler("update", update_leaderboard_command))
    application.add_handler(CommandHandler("highlight", highlight_creator_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Start polling for updates from Telegram
    print("Starting Telegram bot polling...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False
    )

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