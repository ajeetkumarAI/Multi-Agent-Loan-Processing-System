from __future__ import annotations

import json

from .workflow import HumanReviewOutcome, LoanApplication, LoanProcessingWorkflow


def main() -> None:
    workflow = LoanProcessingWorkflow()
    package = workflow.process(
        LoanApplication(
            customer_id="CUST-1001",
            name="Taylor Applicant",
            email="taylor@example.com",
            annual_income=120000,
            monthly_debt=1200,
            loan_amount=18000,
            loan_term_months=36,
            purpose="home_improvement",
            documents=["government_id", "pay_stub", "bank_statement"],
            credit_score=725,
            external_data={"employer": "Acme Corp", "years_employed": 5},
        ),
        human_review=HumanReviewOutcome(
            reviewer="underwriter@example.com",
            decision="approve",
            notes="Reviewed package and confirmed approval recommendation.",
        ),
    )
    print(json.dumps(package, indent=2))


if __name__ == "__main__":
    main()
