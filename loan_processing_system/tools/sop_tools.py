from __future__ import annotations

from typing import Any


LOAN_SOPS: dict[str, dict[str, Any]] = {
    "student_loan": {
        "label": "Student loan",
        "required_documents": [
            "government-issued identity document",
            "proof of enrollment or admission",
            "tuition invoice or education-cost statement",
            "income or co-signer evidence, when applicable",
        ],
        "checks": [
            "Verify the school and enrollment or admission status.",
            "Confirm the requested amount is tied to eligible education costs.",
            "Review borrower or co-signer income and repayment capacity.",
            "Flag unclear education purpose, identity mismatch, or missing enrollment evidence.",
        ],
        "decision_focus": "Enrollment, eligible education use, affordability, and co-signer risk.",
    },
    "business_loan": {
        "label": "Business loan",
        "required_documents": [
            "government-issued identity document",
            "business registration or license",
            "business bank statements",
            "business tax returns or financial statements",
            "business plan or use-of-funds statement",
        ],
        "checks": [
            "Verify the business identity, ownership, and operating status.",
            "Cross-check revenue, cash flow, debt obligations, and requested use of funds.",
            "Review business and personal guarantor repayment capacity.",
            "Flag inconsistent financial statements, unsupported projections, or sanctions concerns.",
        ],
        "decision_focus": "Business legitimacy, cash flow, use of funds, and repayment capacity.",
    },
    "home_improvement": {
        "label": "Home improvement loan",
        "required_documents": [
            "government-issued identity document",
            "income verification",
            "contractor estimate or project quote",
            "proof of property ownership or authorization",
        ],
        "checks": [
            "Verify the project purpose and estimated cost.",
            "Confirm borrower income, debt, and repayment capacity.",
            "Check that the applicant is authorized to complete the property work.",
        ],
        "decision_focus": "Project legitimacy, property authorization, and affordability.",
    },
    "debt_consolidation": {
        "label": "Debt consolidation loan",
        "required_documents": [
            "government-issued identity document",
            "income verification",
            "current creditor statements",
            "authorization or payoff details for consolidated debts",
        ],
        "checks": [
            "Verify each debt being consolidated and the requested payoff amount.",
            "Recalculate debt-to-income after the proposed payment.",
            "Confirm the use of funds is limited to the disclosed debts.",
        ],
        "decision_focus": "Verified liabilities, post-loan DTI, and controlled use of funds.",
    },
    "education": {
        "label": "Education loan",
        "required_documents": [
            "government-issued identity document",
            "proof of enrollment or admission",
            "tuition or education-cost statement",
            "income or co-signer evidence, when applicable",
        ],
        "checks": [
            "Apply the student-loan SOP for enrollment and eligible education costs.",
            "Verify borrower or co-signer repayment capacity.",
        ],
        "decision_focus": "Education purpose, enrollment evidence, and affordability.",
    },
    "small_business": {
        "label": "Small business loan",
        "required_documents": [
            "government-issued identity document",
            "business registration or license",
            "business bank statements",
            "business financial statements",
            "use-of-funds statement",
        ],
        "checks": [
            "Apply the business-loan SOP for business identity and cash flow.",
            "Verify use of funds and borrower or guarantor repayment capacity.",
        ],
        "decision_focus": "Business legitimacy, cash flow, use of funds, and repayment capacity.",
    },
    "medical": {
        "label": "Medical loan",
        "required_documents": [
            "government-issued identity document",
            "income verification",
            "provider estimate or medical invoice",
            "insurance or out-of-pocket cost evidence, when applicable",
        ],
        "checks": [
            "Verify the provider estimate or medical expense.",
            "Confirm the requested amount and borrower affordability.",
        ],
        "decision_focus": "Verified medical expense, privacy-aware documentation, and affordability.",
    },
    "other": {
        "label": "Other personal loan",
        "required_documents": [
            "government-issued identity document",
            "income verification",
            "purpose and use-of-funds statement",
            "supporting evidence for the stated purpose",
        ],
        "checks": [
            "Verify the stated purpose and requested use of funds.",
            "Confirm identity, income, debt, and repayment capacity.",
        ],
        "decision_focus": "Purpose verification, use of funds, identity, and affordability.",
    },
}


def get_loan_sop(loan_purpose: str) -> dict[str, Any]:
    """Return the operating procedure for a normalized loan category."""
    category = loan_purpose.strip().lower().replace(" ", "_")
    if category == "student":
        category = "student_loan"
    if category == "business":
        category = "business_loan"
    return {
        "category": category if category in LOAN_SOPS else "other",
        **LOAN_SOPS.get(category, LOAN_SOPS["other"]),
    }


def evaluate_sop_documents(
    loan_purpose: str,
    document_types: list[str] | set[str],
) -> dict[str, Any]:
    """Return deterministic document checks for the selected loan category."""
    sop = get_loan_sop(loan_purpose)
    available = set(document_types)
    required = {"government-issued identity document", "income verification"}
    category_requirements = {
        "education": {"proof of enrollment or admission", "tuition or education-cost statement"},
        "student_loan": {"proof of enrollment or admission", "tuition invoice or education-cost statement"},
        "business_loan": {"business registration or license", "business bank statements"},
        "small_business": {"business registration or license", "business bank statements"},
        "home_improvement": {"contractor estimate or project quote", "proof of property ownership or authorization"},
        "debt_consolidation": {"current creditor statements", "authorization or payoff details for consolidated debts"},
        "medical": {"provider estimate or medical invoice"},
        "other": {"purpose and use-of-funds statement"},
    }
    required.update(category_requirements.get(sop["category"], set()))

    aliases = {
        "identity_proof": "government-issued identity document",
        "income_document": "income verification",
        "bank_statement": "business bank statements",
        "credit_report": "current creditor statements",
    }
    satisfied = {aliases.get(document_type, document_type) for document_type in available}
    checks = []
    for requirement in sorted(required):
        if requirement in satisfied:
            checks.append({"requirement": requirement, "status": "pass", "reason": "Evidence provided."})
        else:
            checks.append({
                "requirement": requirement,
                "status": "missing",
                "reason": f"Required by the {sop['label']} SOP.",
            })
    missing = [check["requirement"] for check in checks if check["status"] == "missing"]
    return {
        "category": sop["category"],
        "status": "pass" if not missing else "missing",
        "checks": checks,
        "missing_items": missing,
        "reason": "All required evidence is present." if not missing else "Required evidence is missing.",
    }


def build_customer_document_request(
    applicant_email: str,
    application_id: str,
    sop_check: dict[str, Any],
) -> dict[str, Any] | None:
    """Build an idempotent follow-up payload when the SOP gate fails."""
    if not sop_check["missing_items"]:
        return None
    return {
        "application_id": application_id,
        "recipient": applicant_email,
        "status": "open",
        "request_key": f"{application_id}:{sop_check['category']}:documents",
        "missing_items": sop_check["missing_items"],
        "message": "Please provide the missing documents so the loan review can continue.",
    }
