from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import streamlit as st

from loan_processing_system.__main__ import build_loan_assistant
from loan_processing_system.tools import (
    clear_session_storage,
    build_customer_document_request,
    evaluate_sop_documents,
    fetch_documents_from_session,
    get_loan_sop,
    get_session_status,
    store_user_info,
    upload_file,
)


st.set_page_config(
    page_title="LoanAssist | Multi-Agent Review",
    page_icon="L",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink:#18201f; --muted:#65716d; --mint:#d7f2df; --green:#2c7656; --cream:#f5f3ed; --line:#d8ded8; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3, h4, p, label, [data-testid="stMarkdownContainer"] { color: var(--ink); }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: 0; }
    [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { color: var(--ink) !important; }
    [data-baseweb="input"], [data-baseweb="select"] > div { background: #ffffff !important; border-color: #aebbb2 !important; }
    [data-baseweb="input"] input, [data-baseweb="select"] input { color: var(--ink) !important; }
    [data-baseweb="select"] span { color: var(--ink) !important; }
    [data-testid="stFileUploader"] section { background: #ffffff; border-color: #aebbb2; }
    .stApp { background: var(--cream); }
    [data-testid="stSidebar"] { background: #e6efe8; border-right: 1px solid var(--line); }
    .hero { padding: 1.4rem 0 1.8rem; border-bottom: 1px solid var(--line); margin-bottom: 1.5rem; }
    .eyebrow { color: var(--green); font-size: .75rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
    .hero-title { color: var(--ink); font-family: 'Space Grotesk', sans-serif; font-size: clamp(2rem, 4vw, 3.7rem); line-height: 1; margin: .45rem 0 .7rem; font-weight: 700; }
    .hero p { color: var(--muted); max-width: 680px; font-size: 1.02rem; }
    .metric { background: white; border: 1px solid var(--line); padding: 1rem; border-radius: 8px; }
    .metric-label { color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; }
    .metric-value { font-family: 'Space Grotesk'; font-size: 1.65rem; font-weight: 700; margin-top: .25rem; }
    section[data-testid="stSidebar"] h2 { font-size: 1.05rem; }
    .stButton > button { border-radius: 6px; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)


def metric(label: str, value: str) -> None:
    st.markdown(
        f'<div class="metric"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div></div>',
        unsafe_allow_html=True,
    )


def reset_application() -> None:
    clear_session_storage()
    for key in (
        "review",
        "submitted_application",
        "applicant_name",
        "applicant_email",
        "annual_income",
        "current_debt",
        "requested_loan",
        "employment_length",
        "loan_purpose",
        "prior_default",
        "document_identity_proof",
        "document_income_document",
        "document_bank_statement",
        "document_credit_report",
    ):
        st.session_state.pop(key, None)


def main() -> None:
    saved_application = st.session_state.get("submitted_application")
    if not saved_application:
        st.session_state.pop("review", None)
    if saved_application:
        store_user_info(saved_application)

    st.markdown(
        '<div class="hero"><div class="eyebrow">Agno multi-agent workflow</div>'
        '<div class="hero-title">LoanAssist: Multi-Agent Loan Review</div>'
        '<p>Move one application through concierge intake, document verification, financial processing, and compliance review.</p></div>',
        unsafe_allow_html=True,
    )

    st.subheader("Application intake")
    first_row, second_row = st.columns(2)
    with first_row:
        name = st.text_input("Applicant name *", value="Taylor Applicant", key="applicant_name")
        income = st.number_input("Annual income", min_value=0.0, value=85000.0, step=1000.0, key="annual_income")
        loan_amount = st.number_input("Requested loan", min_value=0.0, value=18000.0, step=1000.0, key="requested_loan")
        purpose = st.selectbox("Loan purpose", ["home improvement", "debt consolidation", "education", "small business", "medical", "other"], key="loan_purpose")
    with second_row:
        email = st.text_input("Email *", value="taylor@example.com", key="applicant_email")
        debt = st.number_input("Current monthly debt", min_value=0.0, value=1200.0, step=100.0, key="current_debt")
        employment = st.number_input("Employment length (years)", min_value=0.0, value=5.0, step=0.5, key="employment_length")
        loan_default = st.selectbox("Prior loan default", ["no", "yes"], key="prior_default")

    st.markdown("**Supporting documents by category**")
    document_columns = st.columns(4)
    document_uploads: dict[str, list] = {}
    document_labels = {
        "identity_proof": "Identity proof",
        "income_document": "Income proof",
        "bank_statement": "Bank statement",
        "credit_report": "Credit report",
    }
    for column, (document_type, label) in zip(document_columns, document_labels.items()):
        with column:
            document_uploads[document_type] = st.file_uploader(
                label,
                type=["pdf", "txt"],
                accept_multiple_files=False,
                key=f"document_{document_type}",
            )
    action_row = st.columns([1, 1, 3])
    with action_row[0]:
        process = st.button("Run loan review", type="primary", use_container_width=True)
    with action_row[1]:
        st.button("Clear session", use_container_width=True, on_click=reset_application)

    status = get_session_status()
    col1, col2, col3 = st.columns(3)
    with col1:
        metric("Stored applicants", str(max(status["users_count"], 1 if saved_application else 0)))
    with col2:
        metric("Stored documents", str(status["documents_count"]))
    with col3:
        metric("Workflow", "4 agents")

    if saved_application:
        st.subheader("Submitted application")
        summary_left, summary_right = st.columns(2)
        with summary_left:
            st.write(f"**Applicant:** {saved_application['name']}")
            st.write(f"**Email:** {saved_application['email']}")
            st.write(f"**Annual income:** ${saved_application['income']:,.2f}")
            st.write(f"**Requested loan:** ${saved_application['loan_amount']:,.2f}")
        with summary_right:
            st.write(f"**Monthly debt:** ${saved_application['current_debt']:,.2f}")
            st.write(f"**Employment:** {saved_application['employment_length']} years")
            st.write(f"**Purpose:** {saved_application['loan_intent']}")
            st.write(f"**Prior default:** {saved_application['loan_default']}")
        with st.expander("Applicable loan SOP", expanded=True):
            st.json(get_loan_sop(saved_application["loan_intent"]))
    else:
        st.subheader("Current application")
        current_left, current_right = st.columns(2)
        with current_left:
            st.write(f"**Applicant:** {name or 'Not entered'}")
            st.write(f"**Email:** {email or 'Not entered'}")
            st.write(f"**Annual income:** ${income:,.2f}")
            st.write(f"**Requested loan:** ${loan_amount:,.2f}")
        with current_right:
            st.write(f"**Monthly debt:** ${debt:,.2f}")
            st.write(f"**Employment:** {employment} years")
            st.write(f"**Purpose:** {purpose}")
            st.write(f"**Prior default:** {loan_default}")
        with st.expander("Applicable loan SOP", expanded=True):
            st.json(get_loan_sop(purpose))

    if process:
        if not name.strip() or not email.strip():
            st.error("Applicant name and email are required.")
            return
        if "@" not in email.strip() or "." not in email.rsplit("@", 1)[-1]:
            st.error("Enter a valid email address.")
            return
        user = {
            "name": name.strip(),
            "email": email.strip(),
            "income": income,
            "employment_length": employment,
            "loan_intent": purpose,
            "loan_amount": loan_amount,
            "current_debt": debt,
            "loan_default": loan_default,
        }
        st.session_state["submitted_application"] = user
        store_user_info(user)
        with tempfile.TemporaryDirectory() as temp_dir:
            files: dict[str, dict[str, str]] = {}
            for document_type, document in document_uploads.items():
                if document is None:
                    continue
                path = Path(temp_dir) / document.name
                path.write_bytes(document.getvalue())
                files[document_type] = {
                    "filename": document.name,
                    "path": str(path),
                    "user_email": email.strip(),
                }
            upload_file(files)
            sop_check = evaluate_sop_documents(purpose, list(files))
            customer_request = build_customer_document_request(
                email.strip(), email.strip(), sop_check
            )
            prompt = (
                f"Process the stored loan application for {email.strip()} through all four agents. "
                "First run concierge, then document verification, processing, and compliance. "
                "Prepare a concise human-review package with findings, risks, missing items, "
                "and a preliminary recommendation. The exact submitted application is: "
                f"{json.dumps(user)}. Apply this category-specific SOP: "
                f"{json.dumps(get_loan_sop(purpose))}. The deterministic SOP pre-check is: "
                f"{json.dumps(sop_check)}. Do not clear or overwrite session storage."
            )
            with st.status("Running the four-agent review...", expanded=True) as review_status:
                response = build_loan_assistant().run(prompt)
                review_status.update(label="Review complete", state="complete")
            agent_review = str(response.content if hasattr(response, "content") else response)
            st.session_state["review"] = (
                "### Submitted application\n\n"
                f"- **Applicant:** {user['name']}\n"
                f"- **Email:** {user['email']}\n"
                f"- **Annual income:** ${user['income']:,.2f}\n"
                f"- **Requested loan:** ${user['loan_amount']:,.2f}\n"
                f"- **Monthly debt:** ${user['current_debt']:,.2f}\n"
                f"- **Employment:** {user['employment_length']} years\n"
                f"- **Purpose:** {user['loan_intent']}\n"
                f"- **Prior default:** {user['loan_default']}\n\n"
                "### SOP pre-check\n\n"
                f"```json\n{json.dumps(sop_check, indent=2)}\n```\n\n"
                + (
                    "### Customer document request\n\n"
                    f"```json\n{json.dumps(customer_request, indent=2)}\n```\n\n"
                    if customer_request
                    else ""
                )
                + "### Agent assessment\n\n"
                f"{agent_review}"
            )
        st.rerun()

    if "review" in st.session_state:
        st.subheader("Human review package")
        st.info("This is a preliminary agent assessment. A qualified human reviewer must make the final lending decision.")
        st.markdown(st.session_state["review"])
        with st.expander("Session document inventory"):
            st.json(fetch_documents_from_session(email.strip()))
    else:
        st.subheader("Ready for an application")
        st.write("Complete the intake form, add any supporting documents, and run the review to see the agent handoffs here.")


if __name__ == "__main__":
    main()
