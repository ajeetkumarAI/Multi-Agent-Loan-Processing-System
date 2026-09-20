from __future__ import annotations

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from .agents import (
    compliance_assistant,
    concierge_assistant,
    document_verification_assistant,
    processing_assistant,
)
from .tools import store_user_info
from config import AgentConfig


DEMO_USER = {
    "name": "Taylor Applicant",
    "email": "taylor@example.com",
    "income": 120000.0,
    "employment_length": 5.0,
    "loan_intent": "home improvement",
    "loan_amount": 18000.0,
    "current_debt": 1200.0,
    "loan_default": "no",
}


def build_loan_assistant() -> Agent:
    config = AgentConfig()
    return Agent(
        instructions=(
            "You are LoanAssist. Execute the loan workflow in order: concierge, "
            "document verification, processing, and compliance. Complete each "
            "stage before moving to the next and present a human-review package."
        ),
        tools=[
            concierge_assistant,
            document_verification_assistant,
            processing_assistant,
            compliance_assistant,
        ],
        name="LoanAssist",
        model=OpenAIChat(id=config.model_id, temperature=config.temperature, top_p=config.top_p),
    )


def main() -> None:
    store_user_info(DEMO_USER)
    assistant = build_loan_assistant()
    response = assistant.run(
        "Process the stored loan application for taylor@example.com through all "
        "four agents. No local documents are attached, so report that limitation "
        "and prepare the compliance review for a human officer."
    )
    print(response)


if __name__ == "__main__":
    main()
