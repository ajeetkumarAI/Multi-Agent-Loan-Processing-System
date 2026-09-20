from agno.agent import Agent
from agno.models.openai import OpenAIChat

from config import AgentConfig
from ..tools import store_user_info, upload_file


config = AgentConfig()
model = OpenAIChat(id=config.model_id, temperature=config.temperature, top_p=config.top_p)

CONCIERGE_AGENT_PROMPT = """You are a concierge loan agent. Store applicant information and uploaded documents with your tools. Answer only fact-based questions about loan requirements and explain when a human representative is needed."""

concierge_assistant = Agent(
    tools=[store_user_info, upload_file],
    name="Concierge Agent",
    model=model,
    instructions=CONCIERGE_AGENT_PROMPT,
)
