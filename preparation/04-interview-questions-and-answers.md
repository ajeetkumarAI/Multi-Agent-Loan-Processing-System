# Interview Questions and Answers

## 1. What problem does LoanAssist solve?

LoanAssist reduces the manual work required to collect loan applications, classify documents, extract evidence, apply category-specific SOPs, run financial checks, and prepare a review package. It is designed to move operations teams from repetitive processing to exception-based review.

## 2. Why use multiple agents instead of one large agent?

Each stage has a focused responsibility and a limited tool set. Concierge handles intake, Document Verification handles evidence, Processing handles financial analysis, and Compliance handles final review. This separation improves prompts, permissions, testing, observability, and future replacement of individual stages.

## 3. What is the role of the supervisor agent?

The Agno `LoanAssist` supervisor coordinates the specialist agents in order. It receives the application context, delegates each stage, and asks the agents to produce a consolidated human-review package.

## 4. How are student and business loans handled differently?

The SOP resolver selects a different procedure for each category. Student loans emphasize enrollment, tuition, eligible education costs, and co-signer affordability. Business loans emphasize registration, ownership, revenue, cash flow, financial statements, and use of funds.

## 5. What happens when required documents are missing?

The SOP pre-check identifies the missing document and records the reason. In the target architecture, a Notification Agent sends a clear customer request for the missing document or clarification. The current MVP displays the missing items in the human-review package.

## 6. How does document extraction work?

The current demo extracts text from PDF files with PyPDF2 and supports text files. The target architecture should add DOCX parsing, OCR for scanned documents, document classification, confidence scores, structured field extraction, and references back to the original page and document.

## 7. Can the applicant upload a completed application form?

The target design supports web-form intake, PDF application upload, and DOCX application upload. The current demo supports structured web-form intake and explicit PDF/text document uploads; DOCX ingestion is a planned extension. The demo interface is only for illustrating the workflow.

## 8. How do you prevent the wrong SOP from being applied?

Loan purpose is normalized and resolved through a controlled SOP catalog. The selected category, required documents, checks, and decision focus are included in the processing context. A production implementation should reject unsupported categories instead of silently falling back to a generic procedure.

## 9. How are financial calculations kept reliable?

Calculations such as payment estimates, DTI, and risk scores belong in deterministic Python tools rather than being invented by the language model. The agent supplies validated inputs, calls the tool, and explains the returned result.

## 10. Does the system make the final approval decision?

No. It produces a preliminary recommendation and human-review package. A qualified reviewer must approve, decline, or override the recommendation according to lending policy and applicable regulations.

## 11. How would you process income, credit, and appraisal evidence in parallel?

After the SOP pre-check passes, the orchestration layer can start separate Income, Credit, Appraisal, and identity/fraud tasks concurrently. Each returns a structured result with status, findings, evidence IDs, exceptions, and confidence. Underwriting and Compliance consume the combined results after all required tasks complete.

## 12. What would the dashboard show?

The dashboard should show application ID, applicant, loan category, amount requested, creation date, processing status, documents received, documents passed, documents failed, pending customer requests, preliminary decision, and human-review status. Clicking an application should open the complete evidence and audit trail.

## 13. How do you handle auditability?

Store every important event: document received, classification result, extracted fields, SOP selected, validation result, agent output, notification sent, reviewer action, and final decision. Each event should include timestamps, actor or agent name, evidence references, and reason codes.

## 14. What are the main production risks?

The main risks are incorrect extraction, wrong document classification, missing evidence, model hallucination, privacy leakage, unfair decisioning, and unsupported automated approval. Controls include deterministic tools, confidence thresholds, human gates, PII protection, audit logs, fairness testing, and policy validation.

## 15. Why is the current storage only in memory?

In-memory storage keeps the MVP simple and easy to run locally. It resets when the process restarts and is not suitable for production. A production system should use encrypted persistent storage with application-level access control and retention policies.

## 16. How would you test the workflow?

Test each tool independently, then test each agent with mocked tool results, then test the orchestration flow with complete, incomplete, inconsistent, and unsupported applications. Include document-format tests, SOP-category tests, deterministic calculation tests, security tests, and human-review override tests.

## 17. How would you measure success?

Measure time to review-ready package, document classification accuracy, extraction accuracy, missing-document turnaround, manual touches per application, percentage of applications requiring rework, compliance exception rate, reviewer override rate, and customer follow-up resolution time.

## 18. How does this compare with the AWS sample?

The architecture follows the same four-stage concept: Concierge, Document Verification, Processing, and Compliance. This project intentionally uses Agno with an OpenAI model instead of the sample's Strands and Amazon Bedrock stack. The category-specific SOP and extended parallel-agent design add a practical product layer on top of that base pattern.

## 19. What would you implement next?

The highest-value next steps are persistent storage, DOCX and OCR ingestion, structured extraction contracts, explicit SOP pass/fail records, a Notification Agent, parallel Income/Credit/Appraisal agents, an operations dashboard, and authentication with audit logging.

## 20. What is the most important design principle?

AI should handle document-heavy preparation and explainable checks, while deterministic business rules and qualified humans control regulated lending decisions.
