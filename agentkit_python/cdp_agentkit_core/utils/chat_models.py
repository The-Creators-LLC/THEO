import os
from typing import Dict, Tuple, Type
import yaml
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel

def get_chat_model(model_id: str) -> Tuple[BaseChatModel, Dict[str, str]]:
    """
    Returns the chat model and its parameters based on the provided model ID.

    Args:
        model_id: The ID of the chat model.

    Returns:
        A tuple containing the chat model object and its parameters.
    """
    config_path = Path(__file__).parent / "chat_models.yaml"
    try:
        with open(config_path, "r") as file:
            chat_models_config = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: Could not find chat_models.yaml at {config_path}")
        chat_models_config = {}
    
    model_params = chat_models_config.get(model_id)

    if model_params is None:
        raise ValueError(f"Invalid chat model ID: {model_id}")

    model_type = model_params.pop("type", "gemini")  # Default to "gemini" if type is not specified

    if model_type == "gemini":
        # Use ChatGoogleGenerativeAI for Gemini models
        return get_gemini_model(model_params), model_params
    else:
        raise ValueError(f"Invalid chat model type: {model_type}")

def get_gemini_model(params: Dict[str, str]) -> ChatGoogleGenerativeAI:
    """
    Returns a Gemini chat model based on the provided parameters.

    Args:
        params: The parameters for the Gemini model.

    Returns:
        A ChatGoogleGenerativeAI object.
    """
    # Ensure the GEMINI_API_KEY is set in the environment variables
    if "GEMINI_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY environment variable not set.")

    return ChatGoogleGenerativeAI(model=params["model_name"], google_api_key=os.environ["GEMINI_API_KEY"], convert_system_message_to_human=True)