from agno.agent import Agent
from agno.models.openai import OpenAIChat

from config import AgentConfig
from ..tools import (
    calculate_underwriting_metrics,
    fetch_documents_from_session,
    fetch_user_from_session,
    simulate_credit_bureau_data,
)


config = AgentConfig()
model = OpenAIChat(id=config.model_id, temperature=config.temperature, top_p=config.top_p)

PROCESSING_AGENT_PROMPT = """You are the financial processing agent. Fetch user data and all documents first. Extract income, debt, credit, and account evidence, then call the underwriting and credit tools. Provide DTI, risk analysis, inconsistencies, and a preliminary decision."""

processing_assistant = Agent(
    instructions=PROCESSING_AGENT_PROMPT,
    tools=[fetch_user_from_session, fetch_documents_from_session,
           simulate_credit_bureau_data, calculate_underwriting_metrics],
    name="Processing Agent",
    model=model,
)
