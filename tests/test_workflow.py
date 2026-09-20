import unittest

from loan_processing_system import HumanReviewOutcome, LoanApplication, LoanProcessingWorkflow
from loan_processing_system.workflow import FinancialCalculationTool


class LoanProcessingWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = LoanProcessingWorkflow()
        self.application = LoanApplication(
            customer_id="CUST-42",
            name="Jamie Borrower",
            email="jamie@example.com",
            annual_income=96000,
            monthly_debt=800,
            loan_amount=12000,
            loan_term_months=24,
            purpose="debt_consolidation",
            documents=["government_id", "pay_stub", "bank_statement"],
            credit_score=710,
        )

    def test_process_runs_agents_in_expected_order(self) -> None:
        package = self.workflow.process(self.application)

        self.assertEqual(
            [result["agent_name"] for result in package["agent_results"]],
            [
                "customer_information_collection",
                "document_verification",
                "financial_analysis",
                "underwriting",
                "risk_assessment",
                "compliance_review",
            ],
        )
        self.assertEqual(package["agent_recommendation"], "approve")

    def test_process_requires_human_review_before_final_decision(self) -> None:
        package = self.workflow.process(self.application)

        self.assertTrue(package["human_review_required"])
        self.assertEqual(package["final_decision"], "pending_human_review")
        self.assertIsNone(package["human_review"])

    def test_human_review_can_finalize_decision_package(self) -> None:
        review = HumanReviewOutcome(
            reviewer="underwriting.manager@example.com",
            decision="approve",
            notes="Verified income and supporting documents.",
        )

        package = self.workflow.process(self.application, human_review=review)

        self.assertEqual(package["final_decision"], "approve")
        self.assertEqual(package["human_review"]["reviewer"], review.reviewer)

    def test_human_review_can_downgrade_approved_recommendation(self) -> None:
        package = self.workflow.process(
            self.application,
            human_review=HumanReviewOutcome(
                reviewer="underwriting.manager@example.com",
                decision="manual_review",
                notes="Escalating for additional checks.",
            ),
        )

        self.assertEqual(package["agent_recommendation"], "approve")
        self.assertEqual(package["final_decision"], "manual_review")

    def test_human_review_cannot_override_decline_to_approval(self) -> None:
        risky_application = LoanApplication(
            customer_id="CUST-99",
            name="Casey Compliance",
            email="casey@example.com",
            annual_income=50000,
            monthly_debt=1500,
            loan_amount=30000,
            loan_term_months=24,
            purpose="expansion",
            documents=["government_id", "pay_stub"],
            credit_score=605,
            sanctions_hit=True,
        )

        with self.assertRaisesRegex(ValueError, "cannot override a workflow decline"):
            self.workflow.process(
                risky_application,
                human_review=HumanReviewOutcome(
                    reviewer="compliance.lead@example.com",
                    decision="manual_review",
                ),
            )

        with self.assertRaisesRegex(ValueError, "cannot override a workflow decline"):
            self.workflow.process(
                risky_application,
                human_review=HumanReviewOutcome(
                    reviewer="compliance.lead@example.com",
                    decision="approve",
                ),
            )

        with self.assertRaisesRegex(ValueError, "cannot override a workflow decline"):
            self.workflow.process(
                risky_application,
                human_review=HumanReviewOutcome(
                    reviewer="compliance.lead@example.com",
                    decision="approved",
                ),
            )

    def test_human_review_rejects_unknown_decision_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be one of"):
            self.workflow.process(
                self.application,
                human_review=HumanReviewOutcome(
                    reviewer="underwriting.manager@example.com",
                    decision="hold",
                ),
            )

    def test_missing_documents_and_high_risk_trigger_manual_review(self) -> None:
        application = LoanApplication(
            customer_id="CUST-77",
            name="Riley Risk",
            email="riley@example.com",
            annual_income=60000,
            monthly_debt=1800,
            loan_amount=36000,
            loan_term_months=24,
            purpose="small_business",
            documents=["government_id"],
            credit_score=610,
            consent_provided=False,
        )

        package = self.workflow.process(application)
        results = {result["agent_name"]: result for result in package["agent_results"]}

        self.assertEqual(package["agent_recommendation"], "manual_review")
        self.assertIn("pay_stub", results["document_verification"]["findings"]["missing_documents"])
        self.assertGreater(results["financial_analysis"]["findings"]["debt_to_income_ratio"], 0.45)
        self.assertEqual(results["risk_assessment"]["findings"]["risk_tier"], "high")
        self.assertIn("missing_customer_consent", results["compliance_review"]["findings"]["issues"])

    def test_document_verification_requires_identity_check(self) -> None:
        package = self.workflow.process(
            LoanApplication(
                customer_id="CUST-55",
                name="Pat Identity",
                email="pat@example.com",
                annual_income=90000,
                monthly_debt=1000,
                loan_amount=10000,
                loan_term_months=24,
                purpose="medical",
                documents=["government_id", "pay_stub", "bank_statement"],
                credit_score=720,
                id_verified=False,
            )
        )

        results = {result["agent_name"]: result for result in package["agent_results"]}
        self.assertFalse(results["document_verification"]["findings"]["identity_verified"])
        self.assertFalse(results["document_verification"]["findings"]["all_documents_verified"])
        self.assertEqual(results["underwriting"]["recommendation"], "manual_review")

    def test_financial_calculation_handles_zero_income_and_non_positive_term(self) -> None:
        analysis = FinancialCalculationTool().analyze(
            annual_income=0,
            monthly_debt=500,
            loan_amount=12000,
            loan_term_months=0,
        )

        self.assertEqual(analysis["monthly_income"], 0.0)
        self.assertEqual(analysis["estimated_payment"], 12000.0)
        self.assertEqual(analysis["debt_to_income_ratio"], 1.0)

        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            FinancialCalculationTool().analyze(
                annual_income=50000,
                monthly_debt=500,
                loan_amount=12000,
                loan_term_months=-12,
            )

    def test_non_hard_decline_can_still_be_resolved_by_human_review(self) -> None:
        package = self.workflow.process(
            LoanApplication(
                customer_id="CUST-88",
                name="Jordan Consent",
                email="jordan@example.com",
                annual_income=85000,
                monthly_debt=700,
                loan_amount=15000,
                loan_term_months=36,
                purpose="education",
                documents=["government_id", "pay_stub", "bank_statement"],
                credit_score=700,
                consent_provided=False,
            ),
            human_review=HumanReviewOutcome(
                reviewer="reviewer@example.com",
                decision="manual_review",
            ),
        )

        self.assertEqual(package["agent_recommendation"], "manual_review")
        self.assertEqual(package["final_decision"], "manual_review")


if __name__ == "__main__":
    unittest.main()
