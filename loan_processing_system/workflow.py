from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class LoanApplication:
    customer_id: str
    name: str
    email: str
    annual_income: float
    monthly_debt: float
    loan_amount: float
    loan_term_months: int
    purpose: str
    documents: list[str]
    credit_score: int
    consent_provided: bool = True
    id_verified: bool = True
    sanctions_hit: bool = False
    external_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResult:
    agent_name: str
    status: str
    findings: dict[str, Any]
    recommendation: str


@dataclass(frozen=True)
class HumanReviewOutcome:
    reviewer: str
    decision: str
    notes: str = ""


class DataRetrievalTool:
    def collect_customer_profile(self, application: LoanApplication) -> dict[str, Any]:
        profile = {
            "customer_id": application.customer_id,
            "name": application.name,
            "email": application.email,
            "annual_income": application.annual_income,
            "loan_amount": application.loan_amount,
            "purpose": application.purpose,
        }
        profile.update(application.external_data)
        return profile


class DocumentProcessingTool:
    required_documents = {"government_id", "pay_stub", "bank_statement"}

    def verify(self, documents: list[str]) -> dict[str, Any]:
        provided = set(documents)
        missing = sorted(self.required_documents - provided)
        return {
            "provided_documents": sorted(provided),
            "missing_documents": missing,
            "all_documents_verified": not missing,
        }


class FinancialCalculationTool:
    def analyze(
        self,
        *,
        annual_income: float,
        monthly_debt: float,
        loan_amount: float,
        loan_term_months: int,
    ) -> dict[str, float]:
        monthly_income = annual_income / 12 if annual_income else 0.0
        estimated_payment = loan_amount / max(loan_term_months, 1)
        debt_to_income_ratio = (
            (monthly_debt + estimated_payment) / monthly_income if monthly_income else 1.0
        )
        return {
            "monthly_income": round(monthly_income, 2),
            "estimated_payment": round(estimated_payment, 2),
            "debt_to_income_ratio": round(debt_to_income_ratio, 3),
        }


class CreditAnalysisTool:
    def assess(self, *, credit_score: int, sanctions_hit: bool) -> dict[str, Any]:
        if sanctions_hit:
            tier = "critical"
        elif credit_score >= 740:
            tier = "low"
        elif credit_score >= 680:
            tier = "moderate"
        else:
            tier = "high"
        return {"credit_score": credit_score, "risk_tier": tier}


class DecisionPackageGeneratorTool:
    def generate(
        self,
        *,
        application: LoanApplication,
        agent_results: list[AgentResult],
        recommended_decision: str,
        human_review: HumanReviewOutcome | None,
    ) -> dict[str, Any]:
        decision = LoanProcessingWorkflow.resolve_final_decision(recommended_decision, human_review)
        return {
            "application": asdict(application),
            "agent_results": [asdict(result) for result in agent_results],
            "agent_recommendation": recommended_decision,
            "final_decision": decision,
            "human_review_required": True,
            "human_review": asdict(human_review) if human_review else None,
        }


class CustomerInformationCollectionAgent:
    name = "customer_information_collection"

    def __init__(self, tool: DataRetrievalTool) -> None:
        self.tool = tool

    def run(self, application: LoanApplication, _: dict[str, Any]) -> AgentResult:
        profile = self.tool.collect_customer_profile(application)
        missing_fields = [key for key, value in profile.items() if value in ("", None)]
        return AgentResult(
            agent_name=self.name,
            status="completed" if not missing_fields else "needs_attention",
            findings={"profile": profile, "missing_fields": missing_fields},
            recommendation="continue" if not missing_fields else "collect_missing_information",
        )


class DocumentVerificationAgent:
    name = "document_verification"

    def __init__(self, tool: DocumentProcessingTool) -> None:
        self.tool = tool

    def run(self, application: LoanApplication, _: dict[str, Any]) -> AgentResult:
        verification = self.tool.verify(application.documents)
        return AgentResult(
            agent_name=self.name,
            status="completed" if verification["all_documents_verified"] else "needs_attention",
            findings=verification,
            recommendation="continue" if verification["all_documents_verified"] else "request_documents",
        )


class FinancialAnalysisAgent:
    name = "financial_analysis"

    def __init__(self, tool: FinancialCalculationTool) -> None:
        self.tool = tool

    def run(self, application: LoanApplication, _: dict[str, Any]) -> AgentResult:
        analysis = self.tool.analyze(
            annual_income=application.annual_income,
            monthly_debt=application.monthly_debt,
            loan_amount=application.loan_amount,
            loan_term_months=application.loan_term_months,
        )
        recommendation = "continue" if analysis["debt_to_income_ratio"] <= 0.45 else "manual_review"
        return AgentResult(
            agent_name=self.name,
            status="completed",
            findings=analysis,
            recommendation=recommendation,
        )


class UnderwritingAgent:
    name = "underwriting"

    def run(self, application: LoanApplication, context: dict[str, Any]) -> AgentResult:
        docs_complete = context["document_verification"]["all_documents_verified"]
        dti = context["financial_analysis"]["debt_to_income_ratio"]
        recommendation = "approve" if docs_complete and dti <= 0.45 and application.credit_score >= 680 else "manual_review"
        return AgentResult(
            agent_name=self.name,
            status="completed",
            findings={"documents_complete": docs_complete, "debt_to_income_ratio": dti},
            recommendation=recommendation,
        )


class RiskAssessmentAgent:
    name = "risk_assessment"

    def __init__(self, tool: CreditAnalysisTool) -> None:
        self.tool = tool

    def run(self, application: LoanApplication, context: dict[str, Any]) -> AgentResult:
        assessment = self.tool.assess(
            credit_score=application.credit_score,
            sanctions_hit=application.sanctions_hit,
        )
        if context["financial_analysis"]["debt_to_income_ratio"] > 0.5 and assessment["risk_tier"] != "critical":
            assessment["risk_tier"] = "high"
        return AgentResult(
            agent_name=self.name,
            status="completed",
            findings=assessment,
            recommendation="continue" if assessment["risk_tier"] in {"low", "moderate"} else "manual_review",
        )


class ComplianceReviewAgent:
    name = "compliance_review"

    def run(self, application: LoanApplication, _: dict[str, Any]) -> AgentResult:
        issues = []
        if not application.consent_provided:
            issues.append("missing_customer_consent")
        if not application.id_verified:
            issues.append("identity_not_verified")
        if application.sanctions_hit:
            issues.append("sanctions_screening_hit")
        status = "completed" if not issues else "needs_attention"
        return AgentResult(
            agent_name=self.name,
            status=status,
            findings={"issues": issues, "compliant": not issues},
            recommendation="continue" if not issues else "manual_review",
        )


class LoanProcessingWorkflow:
    def __init__(self) -> None:
        self.customer_information_agent = CustomerInformationCollectionAgent(DataRetrievalTool())
        self.document_verification_agent = DocumentVerificationAgent(DocumentProcessingTool())
        self.financial_analysis_agent = FinancialAnalysisAgent(FinancialCalculationTool())
        self.underwriting_agent = UnderwritingAgent()
        self.risk_assessment_agent = RiskAssessmentAgent(CreditAnalysisTool())
        self.compliance_review_agent = ComplianceReviewAgent()
        self.decision_package_tool = DecisionPackageGeneratorTool()

    def process(
        self,
        application: LoanApplication,
        human_review: HumanReviewOutcome | None = None,
    ) -> dict[str, Any]:
        context: dict[str, Any] = {}
        agent_results: list[AgentResult] = []

        for agent in (
            self.customer_information_agent,
            self.document_verification_agent,
            self.financial_analysis_agent,
            self.underwriting_agent,
            self.risk_assessment_agent,
            self.compliance_review_agent,
        ):
            result = agent.run(application, context)
            agent_results.append(result)
            context[result.agent_name] = result.findings

        recommended_decision = self._recommend_decision(agent_results)
        return self.decision_package_tool.generate(
            application=application,
            agent_results=agent_results,
            recommended_decision=recommended_decision,
            human_review=human_review,
        )

    @staticmethod
    def _recommend_decision(agent_results: list[AgentResult]) -> str:
        results_by_name = {result.agent_name: result for result in agent_results}
        compliance_ok = results_by_name["compliance_review"].findings["compliant"]
        underwriting_recommendation = results_by_name["underwriting"].recommendation
        risk_tier = results_by_name["risk_assessment"].findings["risk_tier"]
        if not compliance_ok:
            return "decline"
        if underwriting_recommendation == "approve" and risk_tier in {"low", "moderate"}:
            return "approve"
        return "manual_review"

    @staticmethod
    def resolve_final_decision(
        recommended_decision: str,
        human_review: HumanReviewOutcome | None,
    ) -> str:
        if human_review is None:
            return "pending_human_review"
        normalized_decision = human_review.decision.lower()
        if recommended_decision == "decline" and normalized_decision == "approved":
            raise ValueError("Human review cannot override a workflow decline with approval.")
        return normalized_decision
