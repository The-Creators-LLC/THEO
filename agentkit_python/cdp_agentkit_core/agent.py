import os
from dotenv import load_dotenv
from agentkit_python.cdp_agentkit_core.agent import Agent
from agentkit_python.cdp_agentkit_core.utils.prompt import Prompt
from agentkit_python.cdp_agentkit_core.utils.chat_models import get_chat_model
from typing import Any

# Load environment variables
load_dotenv()

class TheoAgent(Agent):
    """
    The main class for the THEO agent.
    """

    def __init__(self, tools, **kwargs: Any):
        self.chat_model, self.chat_model_params = get_chat_model(model_id="gemini")
        super().__init__(tools=tools, **kwargs)

    async def handle_message(self, prompt: Prompt):
        # Send a welcome message and instructions to the user upon initial interaction
        # For example
        if not self.chat_history:
            welcome_message = (
                "Hello! I'm THEO, your onchain helper. "
                "I track 'Today on Base I created...' posts and help run the daily leaderboard. "
                "Tag me in comments to nominate creators!"
            )
            await self.send_message(welcome_message)
        else:
            await super().handle_message(prompt)