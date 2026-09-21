# Multi-Agent-Loan-Processing-System

A lightweight Agno-based multi-agent loan processing system organized around four sequential stages: concierge intake, document verification, processing, and compliance review.

## Architecture

```text
                 ┌────────────────────────┐
                 │   LoanAssist (Agno     │
                 │   supervisor Agent)    │
                 └───────────┬────────────┘
                             │ delegates in order
         ┌───────────────────┼───────────────────┬───────────────────┐
         ▼                   ▼                   ▼                   ▼
  ┌─────────────┐   ┌──────────────────┐   ┌─────────────┐   ┌─────────────┐
  │  Concierge  │   │Document           │   │ Processing  │   │ Compliance  │
  │  Agent      │──▶│Verification Agent │──▶│ Agent       │──▶│ Agent       │
  └──────┬──────┘   └─────────┬─────────┘   └──────┬──────┘   └──────┬──────┘
         │                    │                     │                 │
         ▼                    ▼                     ▼                 ▼
  store_user_info,     fetch_documents_from_  simulate_credit_    (review-only,
  upload_file          session,                bureau_data,        no tools)
                        fetch_user_from_        calculate_
                        session                 underwriting_metrics
                             │
                             ▼
                    in-memory SESSION_STORAGE
                    (users, documents)
```

- **`app.py`** — Streamlit UI for application intake, document upload, and
  triggering the review; renders the human-review package.
- **`loan_processing_system/__main__.py`** — builds the `LoanAssist` Agno
  `Agent`, which orchestrates the four specialist agents as tools and is
  invoked via `.run(prompt)`.
- **`loan_processing_system/agents/`** — one Agno `Agent` per stage
  (concierge, document verification, processing, compliance), each with its
  own instructions and a scoped set of tools.
- **`loan_processing_system/tools/storage_tools.py`** — in-memory session
  store (`SESSION_STORAGE`) plus functions to save/fetch applicants and
  documents, and extract text from uploaded PDFs.
- **`loan_processing_system/tools/financial_tools.py`** — credit bureau
  simulation and underwriting/DTI/risk-score calculations.
- **`config.py`** — `AgentConfig` reads `MODEL_ID`, `TEMPERATURE`, and
  `TOP_P` from the environment for the OpenAI model used by every agent.

Data flows one way: the UI writes the applicant/documents into session
storage, the supervisor delegates to each specialist agent in sequence, and
each agent reads from session storage and/or calls its tools before handing
off to the next stage. No agent can clear session storage during a review.

### Runtime Architecture

The application has four layers:

1. **Presentation layer**
  - `app.py` runs the Streamlit interface.
  - Applicants enter identity, financial, employment, and loan-purpose data.
  - Supporting PDF or text files can be uploaded before processing.
  - Streamlit session state preserves the submitted application and review
    package across reruns.

2. **Orchestration layer**
  - `LoanAssist` is the top-level Agno supervisor agent.
  - It receives the submitted application and delegates work to the four
    specialist agents.
  - The supervisor is limited to specialist-agent tools during a review and
    cannot clear or overwrite session storage.

3. **Specialist-agent layer**
  - Each specialist has its own system instructions and only the tools it
    needs.
  - Agents communicate through the supervisor's ordered prompt and shared
    session storage rather than directly mutating one another's state.

4. **Tool and storage layer**
  - `storage_tools.py` stores applicant records and uploaded documents in
    the in-memory `SESSION_STORAGE` object.
  - PDF content is extracted when documents are fetched by the verification
    or processing agent.
  - `financial_tools.py` provides credit-data simulation and underwriting
    calculations.

### Agent Workflow

```text
1. Streamlit intake
  |
  | store_user_info() and upload_file()
  v
2. Concierge Agent
  | Confirms the applicant profile and loan request.
  v
3. Document Verification Agent
  | Fetches the applicant and all documents, extracts text, and reports
  | missing, inconsistent, or unverifiable evidence.
  v
4. Processing Agent
  | Reads the verified application package, obtains or simulates credit data,
  | calculates payment and DTI metrics, and prepares a preliminary assessment.
  v
5. Compliance Agent
  | Consolidates the findings, identifies regulatory or documentation risks,
  | and prepares a human-review package.
  v
6. Streamlit human-review output
  | Shows submitted data, findings, risks, missing items, recommendation,
  | and next steps. A human reviewer makes the final lending decision.
```

#### Agent Responsibilities

| Agent | Responsibility | Tools |
| --- | --- | --- |
| Concierge Agent | Capture and confirm applicant information and documents. | `store_user_info`, `upload_file` |
| Document Verification Agent | Retrieve documents, extract text, and validate application evidence. | `fetch_user_from_session`, `fetch_documents_from_session` |
| Processing Agent | Analyze income, debt, credit risk, DTI, and preliminary underwriting outcome. | `simulate_credit_bureau_data`, `calculate_underwriting_metrics`, document tools |
| Compliance Agent | Review the complete package and identify missing evidence or compliance concerns. | None; review-only |

#### Decision Boundary

The system intentionally stops at a **preliminary recommendation**. It does
not issue an autonomous final approval or decline. The final decision belongs
to a qualified human reviewer after reviewing the agent findings and required
supporting documents.

## Workflow

The implementation uses specialized agents that run in order:

1. Concierge agent: collects the customer profile
2. Document verification
3. Processing agent: runs financial analysis, underwriting, and risk assessment
4. Compliance agent: checks consent, identity, and sanctions status
5. Decision-package generation for human review

## Agent Tools

- **Storage tools** for customer profile assembly and document verification
- **Financial tools** for payment, debt-to-income, and risk-tier analysis
- **Agno Agent supervisor** for coordinating the four specialist agents

## Project structure

```text
loan_processing_system/
├── agents/                         # Concierge, verification, processing, compliance
└── tools/                          # Session storage and financial tools
config.py                           # Agno model configuration
```

## Run the demo

```bash
python -m loan_processing_system
```

Set `OPENAI_API_KEY` before running the demo. `MODEL_ID`, `TEMPERATURE`, and `TOP_P` can be used to configure the OpenAI model through the environment.

## Run the Streamlit app

```bash
streamlit run app.py
```

The app provides application intake, document upload, session status, agent processing, and a human-review package. Set `OPENAI_API_KEY` before starting it.

## Run tests

```bash
python -m unittest discover -s tests -p 'test*.py'
```

## Application Screenshot

![LoanAssist human-review package](assets/app_ui_6.png)
