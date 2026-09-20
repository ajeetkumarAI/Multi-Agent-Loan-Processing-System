import unittest

from loan_processing_system.agents import (
    compliance_assistant,
    concierge_assistant,
    document_verification_assistant,
    processing_assistant,
)
from loan_processing_system.tools import (
    clear_session_storage,
    fetch_documents_from_session,
    fetch_user_from_session,
    store_user_info,
)


class AgnoLoanProcessingTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_session_storage()

    def test_four_specialist_agents_are_exposed(self) -> None:
        self.assertEqual(concierge_assistant.name, "Concierge Agent")
        self.assertEqual(document_verification_assistant.name, "Document Verification Agent")
        self.assertEqual(processing_assistant.name, "Processing Agent")
        self.assertEqual(compliance_assistant.name, "Compliance Agent")

    def test_session_tools_store_and_fetch_applicant(self) -> None:
        result = store_user_info({
            "name": "Jamie Borrower",
            "email": "jamie@example.com",
            "income": 96000,
            "employment_length": 5,
            "loan_intent": "education",
            "loan_amount": 12000,
            "current_debt": 800,
            "loan_default": "no",
        })

        self.assertIn("stored successfully", result)
        self.assertEqual(
            fetch_user_from_session("jamie@example.com")["user_data"]["name"],
            "Jamie Borrower",
        )
        self.assertEqual(fetch_documents_from_session("jamie@example.com")["document_count"], 0)


if __name__ == "__main__":
    unittest.main()