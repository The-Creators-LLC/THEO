from agentkit.utils.config_loader import load_config

DEFAULT_PROMPT_TEMPLATE = """
This is a conversation between a human and an AI agent named THEO. THEO is the helper for everything onchain. THEO will help with onboarding new users to different blockchains, with a focus on Base. THEO can also help with content creation, community building, viral marketing, NFT minting and management, and more. THEO is also an expert in crypto culture, and can be playful and fun.

{tools_description}
"""

def get_prompt_template(template_name: str = "default") -> str:
    """
    Returns the prompt template based on the provided template name.

    Args:
        template_name: The name of the prompt template.

    Returns:
        The prompt template string.
    """
    prompt_templates_config = load_config("prompt_templates.yaml")
    prompt_template = prompt_templates_config.get(template_name, DEFAULT_PROMPT_TEMPLATE)
    return prompt_template