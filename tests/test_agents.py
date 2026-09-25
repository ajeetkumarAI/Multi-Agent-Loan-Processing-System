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
    build_customer_document_request,
    evaluate_sop_documents,
    get_loan_sop,
    simulate_credit_bureau_data,
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

    def test_loan_categories_use_different_sops(self) -> None:
        student_sop = get_loan_sop("education")
        business_sop = get_loan_sop("small business")

        self.assertEqual(student_sop["category"], "education")
        self.assertEqual(business_sop["category"], "small_business")
        self.assertNotEqual(student_sop["required_documents"], business_sop["required_documents"])
        self.assertIn("enrollment", " ".join(student_sop["checks"]).lower())
        self.assertIn("business", " ".join(business_sop["checks"]).lower())

    def test_credit_simulation_is_repeatable(self) -> None:
        self.assertEqual(
            simulate_credit_bureau_data("jamie@example.com"),
            simulate_credit_bureau_data("jamie@example.com"),
        )

    def test_missing_documents_have_explicit_status(self) -> None:
        result = fetch_documents_from_session("missing@example.com")
        self.assertEqual(result["status"], "no_documents")

    def test_sop_gate_returns_missing_items_and_customer_request(self) -> None:
        check = evaluate_sop_documents("home improvement", ["identity_proof", "income_document"])
        request = build_customer_document_request("jamie@example.com", "app-1", check)

        self.assertEqual(check["status"], "missing")
        self.assertIn("contractor estimate or project quote", check["missing_items"])
        self.assertEqual(request["request_key"], "app-1:home_improvement:documents")


if __name__ == "__main__":
    unittest.main()