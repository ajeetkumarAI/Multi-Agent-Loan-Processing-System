from __future__ import annotations

import json
import secrets

def simulate_credit_bureau_data(user_email: str) -> str:
    """Generate deterministic-shaped demo credit data for an applicant."""
    seed = sum(map(ord, user_email))
    return json.dumps({
        "credit_score": 580 + seed % 271,
        "credit_utilization": 10 + seed % 81,
        "late_payments_12m": seed % 3,
        "monthly_debt_payments": 200 + secrets.randbelow(1801),
    })


def calculate_underwriting_metrics(
    user_data: dict, credit_data: dict, loan_amount: float
) -> str:
    """Calculate DTI, risk score, and a preliminary underwriting decision."""
    monthly_income = float(user_data.get("income", 0)) / 12
    credit_score = int(credit_data.get("credit_score", 650))
    monthly_debt = float(credit_data.get("monthly_debt_payments", user_data.get("current_debt", 0)))
    utilization = float(credit_data.get("credit_utilization", 0))
    payment = float(loan_amount) * 0.02
    dti = ((monthly_debt + payment) / monthly_income * 100) if monthly_income else 999
    risk_score = 0
    risk_score += 40 if credit_score >= 700 else 20 if credit_score >= 600 else 0
    risk_score += 30 if dti <= 40 else 0
    risk_score += 20 if utilization <= 50 else 0
    risk_score += 10 if credit_data.get("late_payments_12m", 0) == 0 else 0
    decision = "APPROVED" if risk_score >= 70 and dti <= 40 and credit_score >= 600 else (
        "CONDITIONAL" if risk_score >= 50 else "DECLINED"
    )
    return json.dumps({"new_dti": round(dti, 1), "monthly_payment": round(payment, 2),
                       "credit_score": credit_score, "risk_score": risk_score,
                       "decision": decision})
