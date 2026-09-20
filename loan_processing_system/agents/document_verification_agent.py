from agno.agent import Agent
from agno.models.openai import OpenAIChat

from config import AgentConfig
from ..tools import fetch_documents_from_session, fetch_user_from_session


config = AgentConfig()
model = OpenAIChat(id=config.model_id, temperature=config.temperature, top_p=config.top_p)

DOCUMENT_VERIFICATION_AGENT_PROMPT = """You are a document verification agent. Fetch the applicant and every uploaded document, extract relevant identity, income, bank, and credit information, compare it with the application, and report missing or inconsistent evidence."""

document_verification_assistant = Agent(
    instructions=DOCUMENT_VERIFICATION_AGENT_PROMPT,
    tools=[fetch_documents_from_session, fetch_user_from_session],
    name="Document Verification Agent",
    model=model,
)
