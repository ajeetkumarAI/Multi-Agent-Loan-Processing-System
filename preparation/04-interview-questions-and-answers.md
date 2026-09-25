# LoanAssist: End-to-End Interview Preparation

This document is a detailed interview guide for explaining LoanAssist to a senior engineering panel or a FAANG interviewer. It covers the business problem, complete request lifecycle, data model, agents, tools, orchestration, storage, reliability, security, scaling, tradeoffs, and likely questions.

## 1. The 90-Second Project Explanation

> LoanAssist is a category-aware multi-agent loan-processing platform concept. It accepts structured application data and unstructured loan documents, classifies and extracts evidence, selects the correct SOP for the loan category, performs deterministic validation and financial calculations, and prepares an explainable package for human underwriting review.
>
> The workflow is divided into focused agents: Concierge, Document Verification, Processing, and Compliance. The supervisor agent coordinates them, while deterministic tools perform calculations and storage operations. For example, a student loan uses enrollment and tuition checks, while a business loan uses registration, revenue, cash-flow, and use-of-funds checks.
>
> The system is intentionally human-in-the-loop. Agents can identify missing documents, calculate DTI, flag risk, and prepare recommendations, but they do not make an unreviewed final lending decision. The current repository is a local Agno demo with in-memory storage; the target production design adds durable storage, OCR/DOCX ingestion, asynchronous processing, notifications, audit logs, and an operations dashboard.

## 2. Business Problem

Loan processing combines structured data, PDFs, scanned forms, payslips, credit reports, bank statements, appraisal reports, and policy documents. The traditional process requires credit teams to:

1. Collect documents from applicants.
2. Open files manually.
3. Identify document types.
4. Copy values into a lending system.
5. Check whether required evidence is complete.
6. Compare evidence with the application.
7. Calculate income, debt-to-income ratio, payment capacity, and risk.
8. Apply a product-specific SOP.
9. Request missing information.
10. Prepare a review package for an underwriter.

This process is slow, repetitive, difficult to audit, and vulnerable to transcription mistakes. A generic checklist also creates problems because the evidence required for a student loan is different from the evidence required for a business, mortgage, medical, or debt-consolidation loan.

## 3. What the System Solves

LoanAssist automates the preparation work while preserving human authority:

- Accepts a web form or uploaded application documents.
- Associates every document with an application and applicant.
- Classifies documents such as identity, income, credit, bank, appraisal, or business records.
- Extracts structured fields and preserves source-document references.
- Selects a category-specific SOP.
- Runs required-document and data-quality checks.
- Performs deterministic financial calculations using tools.
- Runs independent specialist checks in parallel in the target architecture.
- Produces pass/fail results with reasons and evidence references.
- Requests missing information through a notification workflow.
- Presents a dashboard and human-review package.

## 4. Requirements

### Functional Requirements

- Create an application.
- Capture applicant, loan, income, employment, and purpose data.
- Accept PDF, DOCX, image, and text documents in the target architecture.
- Classify documents by type.
- Extract data into structured JSON and review-friendly formats.
- Select a loan-category SOP.
- Determine which documents are required for that SOP.
- Validate documents and extracted fields.
- Calculate DTI, payment, risk, and affordability metrics.
- Return a preliminary pass, fail, or conditional result with reasons.
- Send missing-document or clarification requests.
- Allow a human reviewer to inspect evidence and override a recommendation.
- Preserve an audit trail.

### Non-Functional Requirements

- Explainability: every result must have a reason and evidence reference.
- Reliability: retries must not create duplicate applications or documents.
- Security: PII and financial documents must be protected.
- Availability: intake should remain available even if a downstream agent is delayed.
- Scalability: document processing should scale independently from the dashboard.
- Observability: operators need status, latency, errors, and queue visibility.
- Reproducibility: deterministic calculations must return the same result for the same inputs and policy version.
- Human control: final regulated decisions require an authorized reviewer.

## 5. Complete End-to-End Request Flow

```text
1. Applicant submits web form or application file
   |
2. API creates application_id and stores an intake event
   |
3. Concierge validates required fields and associates documents
   |
4. Document ingestion stores immutable originals
   |
5. Classification identifies document type and confidence
   |
6. Extraction reads PDF, DOCX, image, or scanned content
   |
7. Structured evidence is stored with source/page references
   |
8. SOP resolver selects the loan-category procedure and version
   |
9. Pre-check compares required evidence with the SOP
   |\
   | missing or failed                         passed
   v                                           v
10. Notification request                  10. Specialist checks
    is created                                run in parallel
    |                                           |
11. Applicant receives                       Income, Credit,
    missing-item request                      Appraisal, Identity/Fraud
    |                                           |
12. Applicant resubmits                       v
    or clarifies                         11. Underwriting combines results
                                                |
                                                v
                                           12. Compliance review
                                                |
                                                v
                                           13. Decision package
                                                |
                                                v
                                           14. Dashboard and human review
                                                |
                                                v
                                           15. Final decision and audit event
```

### Step 1: Intake

The applicant can enter data using a web form or upload a completed application form. The intake layer should validate basic syntax but should not make credit decisions.

Example input fields:

```json
{
  "applicant": {
    "name": "Taylor Applicant",
    "email": "taylor@example.com"
  },
  "loan": {
    "category": "home_improvement",
    "amount": 18000,
    "term_months": 36,
    "purpose": "home improvement"
  },
  "income": {
    "annual_income": 85000,
    "employment_length_years": 5,
    "monthly_debt": 1200
  }
}
```

The system creates an `application_id` immediately. Every later document, agent run, check, notification, and review action references this ID.

### Step 2: Document Ingestion

Documents should be stored as immutable originals. The system should not overwrite the original file when a new extraction or classification is generated.

Ingestion metadata:

- `application_id`
- `document_id`
- Original filename
- MIME type
- File size
- Content hash, for duplicate detection
- Storage location
- Upload timestamp
- Upload source
- Applicant association
- Current processing status

The upload endpoint should return quickly with `202 Accepted` and process large files asynchronously instead of making the user wait for OCR and extraction.

### Step 3: Classification

A classification component identifies the document type:

- Application form
- Identity proof
- Payslip or income document
- Bank statement
- Credit report
- Appraisal report
- Business registration
- Business financial statement
- Tuition or enrollment evidence
- Contractor quote
- Medical invoice
- Debt statement

Classification should return:

```json
{
  "document_id": "doc-123",
  "document_type": "income_document",
  "confidence": 0.97,
  "status": "classified",
  "reason": "Detected employer, salary, pay-period, and net-pay fields."
}
```

If confidence is below a threshold, the document should be routed to manual classification or a clarification task. It should not silently be treated as the wrong document type.

### Step 4: Extraction

The extraction layer handles different file types:

- Digital PDF: text extraction and layout parsing.
- Scanned PDF or image: OCR plus layout detection.
- DOCX: paragraphs, tables, headers, and metadata.
- Text: direct decoding with format validation.

The output should contain both normalized fields and evidence references:

```json
{
  "document_id": "doc-123",
  "document_type": "income_document",
  "extraction_status": "success",
  "fields": {
    "employer": "Example Corp",
    "gross_pay": 7083.33,
    "pay_frequency": "monthly",
    "employment_start_date": "2021-04-01"
  },
  "evidence": [
    {
      "field": "gross_pay",
      "value": 7083.33,
      "page": 1,
      "text_span": "Gross pay $7,083.33",
      "confidence": 0.98
    }
  ]
}
```

The reviewer should be able to inspect the original file, a table view, Markdown, and JSON. This is important because a model-generated summary alone is not sufficient evidence for a regulated workflow.

### Step 5: SOP Resolution

The SOP resolver maps the normalized loan category to a versioned policy definition.

Examples:

- Education: enrollment, tuition, eligible costs, borrower/co-signer affordability.
- Business: registration, ownership, revenue, cash flow, financial statements, use of funds.
- Home improvement: property authorization, contractor quote, project cost, affordability.
- Debt consolidation: creditor statements, payoff details, post-loan DTI.
- Medical: provider estimate, medical expense, affordability.
- Mortgage/home purchase: property details, appraisal, title, income, assets, liabilities.

An SOP should be versioned and immutable for a decision run:

```json
{
  "sop_id": "home_improvement_v3",
  "category": "home_improvement",
  "effective_from": "2026-01-01",
  "required_documents": [
    "identity_proof",
    "income_document",
    "contractor_quote",
    "property_authorization"
  ],
  "checks": [
    "identity.required",
    "income.matches_application",
    "project.amount_supported",
    "property.authorization_present"
  ]
}
```

The decision must record the SOP version used. If policy changes later, an old decision must still be reproducible.

### Step 6: SOP Pre-check

The pre-check is deterministic wherever possible. It checks:

- Required document presence.
- Document classification confidence.
- Extraction status.
- Required fields present.
- Application-to-document consistency.
- Date validity and freshness.
- Numeric ranges.
- Duplicate or conflicting evidence.
- Category-specific requirements.

Example result:

```json
{
  "check_id": "income.matches_application",
  "status": "fail",
  "reason": "Extracted annualized income is $72,000 but application income is $85,000.",
  "evidence_ids": ["doc-income-1", "application-42"],
  "severity": "high",
  "review_required": true
}
```

The system should distinguish:

- `pass`: evidence meets the requirement.
- `fail`: evidence contradicts or violates the requirement.
- `missing`: evidence was not supplied.
- `needs_review`: evidence exists but confidence or consistency is insufficient.
- `not_applicable`: the check does not apply to this product.

### Step 7: Customer Follow-up

Failed and missing checks should create a customer-action task instead of only displaying a generic failure.

Example message payload:

```json
{
  "application_id": "app-42",
  "recipient": "taylor@example.com",
  "items": [
    {
      "type": "missing_document",
      "document": "contractor_quote",
      "reason": "Required by the home-improvement SOP to support the requested amount."
    }
  ],
  "expires_at": "2026-10-10"
}
```

The notification service must be idempotent. Retrying a job should not send ten copies of the same email. Use a notification key such as `(application_id, check_id, version)`.

### Step 8: Parallel Specialist Processing

After pre-checks pass, independent specialist work can run concurrently:

- **Income Agent**: income normalization, employer consistency, pay frequency, employment duration, income stability.
- **Credit Agent**: credit score, utilization, payment history, liabilities, hard-fail indicators.
- **Appraisal Agent**: property/project value, loan-to-value inputs, appraisal freshness, comparable evidence.
- **Identity/Fraud Agent**: identity match, duplicate applications, suspicious patterns, sanctions screening integration.

Each agent should return a structured result rather than free-form text only:

```json
{
  "agent": "credit",
  "status": "completed",
  "decision": "pass",
  "findings": [],
  "exceptions": [],
  "evidence_ids": ["doc-credit-1"],
  "confidence": 0.94,
  "policy_version": "credit-policy-v4"
}
```

The orchestration layer waits for required specialists, applies timeouts, and marks unavailable results as `needs_review` rather than pretending they passed.

### Step 9: Underwriting

Underwriting combines deterministic calculations and specialist outputs:

- Monthly income.
- Existing monthly debt.
- Proposed payment.
- New DTI.
- Credit score and utilization.
- Loan-to-income or loan-to-value where applicable.
- Reserves or cash-flow coverage.
- Product-specific policy thresholds.

The language model can explain the result, but the source of truth for numeric policy decisions should be versioned code or a policy engine.

### Step 10: Compliance

Compliance reviews:

- Required-document completeness.
- Identity and authorization.
- Consistency across documents.
- Fair-lending and prohibited-factor controls.
- Reg B, TILA, privacy, and product-specific requirements as applicable.
- Reason codes for pass, fail, conditional, and manual-review outcomes.

Compliance should not silently correct missing evidence. It should expose the gap and route it to human review or customer follow-up.

### Step 11: Human Review

The dashboard should show:

- Application ID.
- Applicant name and contact.
- Loan category and requested amount.
- Creation date and current status.
- Number of documents received.
- Number of checks passed, failed, missing, and needing review.
- Preliminary agent decision.
- Human-review status.
- Outstanding customer actions.

A reviewer opens the complete package, sees source evidence, reviews agent reasons, and records an approval, decline, conditional approval, or request for more information. Any override must record the reviewer, timestamp, reason, and policy context.

## 6. Agent Architecture

### Why Multiple Agents?

A single agent with every instruction and tool has a large context, broad permissions, and weak ownership boundaries. Focused agents provide:

- Smaller prompts.
- Scoped tools and permissions.
- Easier testing.
- Clearer observability.
- Independent model or prompt upgrades.
- Better failure isolation.

### Current Agents

| Agent | Current responsibility | Tools |
| --- | --- | --- |
| Concierge | Confirm applicant and loan context. | `store_user_info`, `upload_file` |
| Document Verification | Retrieve applicant/documents and identify missing evidence. | `fetch_user_from_session`, `fetch_documents_from_session` |
| Processing | Financial analysis, credit simulation, underwriting metrics, SOP context. | Financial tools, document tools, `get_loan_sop` |
| Compliance | Consolidate findings for human review. | Review-only or SOP lookup |

### Target Agents

The production-style architecture adds Classification, Extraction, Notification, Income, Credit, Appraisal, Identity/Fraud, and Underwriting agents. These should communicate through structured state, not by relying only on natural-language handoffs.

## 7. Orchestration Design

### Current Demo Orchestration

The local demo uses an Agno supervisor with specialist agents exposed as tools. The supervisor receives an explicit prompt containing the application and SOP context and calls `run()`.

This is useful for demonstrating agent collaboration, but it is not a durable workflow engine. In-memory state disappears when the process stops, and the model is responsible for following the requested order.

### Target Orchestration

A production workflow should use a durable state machine or workflow engine:

```text
RECEIVED
  -> INGESTING
  -> CLASSIFYING
  -> EXTRACTING
  -> SOP_CHECKING
  -> WAITING_FOR_CUSTOMER (if missing)
  -> SPECIALIST_PROCESSING
  -> UNDERWRITING
  -> COMPLIANCE_REVIEW
  -> WAITING_FOR_HUMAN
  -> APPROVED / DECLINED / CONDITIONAL
```

State transitions should be persisted and guarded. A worker should be able to resume after a crash without rerunning completed work.

### Idempotency

Every operation needs an idempotency key:

- Upload: content hash + application ID.
- Classification: document ID + classifier version.
- Extraction: document ID + extractor version.
- SOP check: application ID + SOP version + evidence revision.
- Notification: application ID + check ID + notification version.
- Agent run: application ID + stage + input revision.

## 8. Tool Design

Tools should be narrow, deterministic, typed, observable, and safe to retry.

### Storage Tools

- `create_application()`
- `store_user_info()`
- `upload_document()`
- `fetch_application()`
- `fetch_documents()`
- `fetch_extraction()`
- `get_session_status()` for the demo

### Document Tools

- `classify_document()`
- `extract_pdf_text()`
- `extract_docx_content()`
- `run_ocr()`
- `normalize_fields()`
- `attach_evidence_reference()`

### Financial Tools

- `simulate_credit_bureau_data()` for demo-only data.
- `calculate_underwriting_metrics()`.
- `calculate_dti()`.
- `calculate_payment()`.
- `calculate_ltv()`.
- `calculate_debt_service_coverage()` for business loans.

### Policy Tools

- `get_loan_sop()`.
- `get_sop_version()`.
- `run_required_document_checks()`.
- `run_field_consistency_checks()`.
- `get_reason_code()`.

### Notification Tools

- `create_customer_request()`.
- `send_email()`.
- `send_sms_or_portal_notification()`.
- `close_customer_request()`.

Agents should never receive a database connection or unrestricted administrative tool. They should call safe functions with validation and authorization inside the tool layer.

## 9. Database Design

The current demo uses in-memory storage. A production system needs durable storage.

### Relational Tables

#### `applications`

- `application_id` primary key
- `applicant_id`
- `loan_category`
- `requested_amount`
- `term_months`
- `purpose`
- `status`
- `sop_id`
- `sop_version`
- `created_at`
- `updated_at`

#### `applicants`

- `applicant_id` primary key
- `name`
- `email`
- `contact_hash` or protected contact reference
- `created_at`

#### `documents`

- `document_id` primary key
- `application_id` foreign key
- `document_type`
- `storage_uri`
- `content_hash`
- `mime_type`
- `classification_status`
- `classification_confidence`
- `extraction_status`
- `extraction_version`
- `created_at`

#### `extractions`

- `extraction_id` primary key
- `document_id` foreign key
- `schema_version`
- `structured_json`
- `markdown_content`
- `extraction_confidence`
- `created_at`

#### `evidence`

- `evidence_id` primary key
- `document_id`
- `field_name`
- `field_value`
- `page_number`
- `text_span`
- `confidence`
- `created_at`

#### `sop_definitions`

- `sop_id` primary key
- `category`
- `version`
- `definition_json`
- `effective_from`
- `effective_to`
- `is_active`

#### `validation_checks`

- `check_id` primary key
- `application_id`
- `sop_id`
- `check_code`
- `status`
- `reason_code`
- `reason_text`
- `evidence_ids`
- `created_at`

#### `agent_runs`

- `run_id` primary key
- `application_id`
- `agent_name`
- `stage`
- `input_revision`
- `status`
- `output_json`
- `error_code`
- `started_at`
- `completed_at`

#### `customer_requests`

- `request_id` primary key
- `application_id`
- `request_type`
- `items_json`
- `status`
- `notification_key`
- `sent_at`
- `resolved_at`

#### `human_reviews`

- `review_id` primary key
- `application_id`
- `reviewer_id`
- `decision`
- `reason`
- `created_at`

#### `audit_events`

- `event_id` primary key
- `application_id`
- `actor_type`
- `actor_id`
- `event_type`
- `payload_json`
- `created_at`

### Why Relational Storage?

Application status, SOP checks, agent runs, customer requests, and human reviews have strong relationships and need transactional updates. A relational database is a good source of truth for workflow state and audit records.

Object storage should hold large originals such as PDFs, DOCX files, and images. Search indexes or a document store can support extracted text, but the relational database should retain the authoritative metadata and status.

## 10. APIs

### Application APIs

```text
POST   /applications
GET    /applications/{application_id}
PATCH  /applications/{application_id}
POST   /applications/{application_id}/submit
```

### Document APIs

```text
POST   /applications/{application_id}/documents
GET    /applications/{application_id}/documents
GET    /documents/{document_id}/original
GET    /documents/{document_id}/extraction
GET    /documents/{document_id}/json
```

### Review APIs

```text
GET    /applications/{application_id}/checks
GET    /applications/{application_id}/agent-runs
GET    /applications/{application_id}/review-package
POST   /applications/{application_id}/human-review
```

### Customer Follow-up APIs

```text
GET    /applications/{application_id}/customer-requests
POST   /customer-requests/{request_id}/resubmit
POST   /customer-requests/{request_id}/clarification
```

## 11. Reliability and Failure Handling

### Failure Examples

- Unsupported file format.
- Corrupt PDF.
- OCR timeout.
- Low classification confidence.
- Extraction returns missing fields.
- Credit service unavailable.
- Appraisal unavailable.
- Agent timeout.
- Duplicate upload.
- Customer submits an outdated document.
- Policy version changes during processing.

### Handling Strategy

- Validate file type and size at ingress.
- Hash documents for duplicate detection.
- Use queues for expensive processing.
- Retry transient failures with exponential backoff.
- Do not retry permanent validation failures.
- Use dead-letter queues for exhausted jobs.
- Persist stage status before and after every action.
- Use timeouts for all model and external-service calls.
- Mark unavailable evidence as `needs_review`, never as `pass`.
- Support human reprocessing from a selected failed stage.
- Preserve the original document and every extraction version.

## 12. Security and Compliance

Loan applications contain sensitive personal and financial information.

Controls should include:

- Authentication and role-based authorization.
- Separate applicant, analyst, underwriter, compliance, and administrator roles.
- Encryption in transit and at rest.
- Secret storage outside source control.
- PII minimization in model prompts.
- Redaction of unnecessary account and identity numbers.
- Malware scanning for uploads.
- Content-type validation instead of trusting file extensions.
- Tenant isolation if multiple institutions use the platform.
- Retention and deletion policies.
- Immutable audit history for decisions and overrides.
- Fair-lending and bias testing.
- Human approval gates for regulated outcomes.

## 13. Observability

Track metrics by application, document, agent, SOP version, and model version:

- Intake-to-review latency.
- Queue depth.
- Document classification accuracy.
- Extraction confidence.
- Extraction failure rate.
- SOP pass/fail/missing counts.
- Agent latency and token cost.
- Agent retry count.
- Notification delivery rate.
- Human override rate.
- Applications stuck in each state.
- Decision package generation time.

Use correlation IDs such as `application_id`, `document_id`, and `run_id` in logs. Never log raw PII or complete document contents.

## 14. Testing Strategy

### Unit Tests

- SOP category resolution.
- Required-document logic.
- DTI, payment, LTV, and risk calculations.
- File validation.
- PDF/DOCX extraction adapters.
- Idempotency keys.
- Notification deduplication.

### Agent Tests

Mock tools and verify that each agent:

- Uses the correct tools.
- Returns a structured result.
- Handles missing evidence.
- Does not invent evidence.
- Escalates low-confidence cases.
- Preserves evidence references.

### Workflow Tests

Test complete scenarios:

1. Complete home-improvement application.
2. Student loan missing enrollment proof.
3. Business loan with inconsistent revenue.
4. Credit report unavailable.
5. Corrupt PDF.
6. Duplicate document.
7. Applicant clarification and resubmission.
8. Human reviewer override.
9. Agent timeout and retry.
10. Policy version change during processing.

### Evaluation Tests

Use a labeled document set to measure classification and extraction precision/recall. Test decision consistency across repeated runs and compare model explanations to deterministic tool results.

## 15. Performance and Scaling

The system is mostly I/O-bound during document processing and model calls.

Scale independently:

- API servers for intake and dashboard traffic.
- Ingestion workers for file validation.
- OCR/extraction workers for CPU-heavy processing.
- Agent workers for model calls.
- Notification workers for email delivery.
- Database read replicas for dashboard queries.
- Object storage for large files.

Partition queue work by application ID so two workers do not process the same stage concurrently. Use optimistic locking or a state-transition version to prevent stale updates.

## 16. Design Tradeoffs

### Agno versus a traditional workflow engine

Agno makes specialist-agent composition convenient and is appropriate for the demo. A production system still needs durable workflow state, queues, retries, and explicit transitions. The best design may combine Agno for agent execution with a workflow engine for orchestration.

### In-memory storage versus a database

In-memory storage is simple for a local demo but loses data on restart and cannot support multiple workers. A database is required for production state, auditability, and concurrency control.

### LLM reasoning versus deterministic rules

LLMs are useful for document interpretation, summarization, and routing ambiguous cases. Numeric underwriting calculations and policy gates should be deterministic, versioned, and independently testable.

### Serial versus parallel processing

Serial processing is easier to reason about but slower. Once the SOP pre-check passes, independent Income, Credit, Appraisal, and Identity tasks can run in parallel. The system must still define dependencies and timeout behavior.

### Automatic decision versus human review

Fully automatic decisions may reduce latency but increase regulatory and model risk. Human-in-the-loop review provides a control point for exceptions, low confidence, adverse action explanations, and policy overrides.

## 17. Current Repository Versus Target System

The current repository is a local demonstration, not a production lending platform.

### Implemented in the demo

- Agno supervisor and four specialist agents.
- Generic web-form intake through the local demo interface.
- Explicit PDF/text upload categories.
- In-memory applicant and document storage.
- PDF text extraction.
- Category-specific SOP definitions.
- Financial calculation tools.
- Human-review package output.

### Planned for the target product

- PDF application and DOCX application ingestion.
- OCR and layout-aware IDP.
- Persistent relational database and object storage.
- Versioned structured extraction contracts.
- Explicit check records with reason codes.
- Notification Agent and customer follow-up.
- Parallel Income, Credit, Appraisal, and Identity/Fraud agents.
- Operations dashboard.
- Authentication, authorization, security controls, audit logs, and monitoring.

## 18. Interview Questions and Strong Answers

### Q1. Walk me through the request from upload to decision.

**Answer:** The applicant submits structured data or a document. The system creates an application ID, stores immutable originals, classifies each document, extracts structured fields with evidence references, resolves the SOP based on loan category, and runs deterministic pre-checks. Missing or failed evidence creates a customer request. If the package is complete, independent specialist agents evaluate income, credit, appraisal, and identity in parallel. Underwriting combines their results, Compliance prepares a reasoned package, and an authorized human reviewer makes the final decision. Every stage emits a persisted status and audit event.

### Q2. Why should an LLM not calculate the final DTI itself?

**Answer:** LLM output is probabilistic and can make arithmetic or policy mistakes. I would use the model to identify inputs and explain findings, but call deterministic, versioned tools for payment, DTI, LTV, and risk calculations. The tool output becomes the source of truth and is stored with the policy version and input evidence.

### Q3. How do you prevent an agent from approving a loan without documents?

**Answer:** Approval is not controlled by prose alone. The workflow state machine requires required-document checks to pass before underwriting can produce an approval candidate. The policy engine returns explicit check results, and missing or low-confidence evidence forces `needs_review`. The Compliance stage and human gate also reject unsupported final decisions.

### Q4. How do you guarantee the correct SOP for a business loan?

**Answer:** I normalize the loan category against a controlled catalog and resolve a versioned SOP definition. The selected SOP ID and version are persisted on the application. Every check references that version, so the decision can be reproduced even after policy changes.

### Q5. How would you process ten thousand applications per hour?

**Answer:** I would separate synchronous intake from asynchronous processing. The API stores the application and publishes document jobs to a queue. Classification, extraction, and specialist workloads use independent worker pools with autoscaling. Large documents go to object storage. Application state is stored transactionally, and dashboard reads use indexed queries or read replicas. Partitioning by application ID and idempotency keys prevent duplicate stage execution.

### Q6. How would you handle an OCR service outage?

**Answer:** The extraction job would move to a retryable state with exponential backoff. After the retry budget is exhausted, it would go to a dead-letter queue and mark the document as `extraction_failed`. The application remains visible in the dashboard, and an operator can retry from that stage or request a clearer document. We never mark the evidence as passed because the service was unavailable.

### Q7. What data belongs in SQL and what belongs in object storage?

**Answer:** SQL stores application state, applicant references, document metadata, SOP versions, validation checks, agent runs, notifications, human reviews, and audit events. Object storage stores the immutable PDF, DOCX, image, and large extracted artifacts. SQL stores the object URI, content hash, and access metadata.

### Q8. How do you make retries safe?

**Answer:** Every stage has an idempotency key based on application, document revision, stage, and version. Before doing work, the worker checks whether the same operation already completed. Database state transitions use optimistic locking. Notifications use a unique key so retries do not send duplicates.

### Q9. What happens when two documents disagree about income?

**Answer:** The consistency checker creates a failed or needs-review check with both evidence IDs and the conflicting values. It does not pick one silently. The Notification Agent can request clarification, while the underwriter sees the conflict and source documents.

### Q10. How would you evaluate extraction quality?

**Answer:** I would create a labeled corpus of representative documents across categories and measure field-level precision, recall, and exact-match accuracy. I would track confidence calibration, document classification accuracy, and disagreement rates. Critical fields such as income, loan amount, identity, and debt would have stricter thresholds and mandatory human verification.

### Q11. How do you prevent prompt injection from uploaded documents?

**Answer:** Document text is untrusted input. It must be isolated from system instructions, passed as data, and never allowed to redefine tools, policies, or workflow state. Tool permissions are scoped, model outputs are validated against schemas, and extracted values are checked by deterministic rules.

### Q12. How would you implement human review?

**Answer:** The dashboard shows the application summary, original documents, extracted fields, evidence references, SOP checks, specialist outputs, risks, and recommendation. The reviewer chooses approve, decline, conditional, or request-information. The decision and reason are persisted with reviewer identity, timestamp, and the exact package version reviewed.

### Q13. What is the most difficult technical part?

**Answer:** The hardest part is not calling the model; it is building reliable evidence lineage across messy documents, changing SOPs, asynchronous processing, retries, and human overrides. The system must always answer: which source document produced this field, which policy version evaluated it, which agent made the finding, and why did the final reviewer decide?

### Q14. Why does the demo use in-memory storage?

**Answer:** It keeps the demonstration easy to run and makes the agent/tool interaction visible without requiring infrastructure. It is intentionally not production-ready because it loses state on restart, cannot coordinate multiple workers, and is not suitable for sensitive financial data.

### Q15. What would you build next?

**Answer:** I would first add a durable application/document schema and a queue-backed state machine. Then I would add DOCX/OCR extraction with evidence references, explicit SOP check records, notification and resubmission flow, parallel specialist agents, and the operations dashboard. I would add security, audit logging, evaluation datasets, and load tests before considering production use.

## 19. Final Interview Closing Statement

> The key design decision in LoanAssist is to separate probabilistic reasoning from deterministic control. Agents interpret documents, route work, summarize evidence, and surface exceptions. Tools and policy checks calculate metrics and enforce required conditions. A durable workflow records every transition, and a human reviewer owns the final lending decision. That separation makes the system more explainable, testable, auditable, and safer to scale than a single unconstrained LLM prompt.
