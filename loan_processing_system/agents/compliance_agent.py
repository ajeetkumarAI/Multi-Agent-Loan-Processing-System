from agno.agent import Agent
from agno.models.openai import OpenAIChat

from config import AgentConfig
from ..tools import get_loan_sop


config = AgentConfig()
model = OpenAIChat(id=config.model_id, temperature=config.temperature, top_p=config.top_p)

COMPLIANCE_AGENT_PROMPT = """You are a compliance and human-review agent. Consolidate the application, document verification, and underwriting findings. Flag missing documentation, identity or sanctions concerns, and regulatory risks. Prepare a clear final decision package for a human loan officer. Never make an unreviewed final approval."""

compliance_assistant = Agent(
    instructions=COMPLIANCE_AGENT_PROMPT,
    tools=[get_loan_sop],
    name="Compliance Agent",
    model=model,
)
