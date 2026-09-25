# Problem Statement and Pain Points

## Problem Statement

Loan applications arrive through multiple channels and contain a mixture of structured fields and unstructured documents. Credit teams must manually collect, classify, read, validate, and reconcile this information before an underwriter can make a decision.

This creates delays, inconsistent checks, repeated customer follow-ups, and limited visibility into why an application passed or failed a review stage.

## Current Manual Process

```text
Application received
    -> Documents collected by email or portal
    -> Analyst opens each file
    -> Data copied into a lending system
    -> Required-document checklist reviewed
    -> Income and debt calculated manually
    -> Credit and appraisal information checked
    -> Compliance review performed
    -> Missing information requested
    -> Application returned to queue
    -> Underwriter reviews a final package
```

## Pain Points

### 1. Fragmented intake

Applications may arrive as web forms, PDFs, DOCX files, email attachments, or scanned documents. Staff must consolidate information before analysis can begin.

### 2. Manual document classification

A reviewer must determine whether a file is an identity document, payslip, bank statement, credit report, appraisal, business record, or another document type.

### 3. Re-keying and transcription risk

Copying names, income, debt, loan amounts, dates, and account information between documents and systems creates avoidable errors.

### 4. Loan-category mismatch

A generic checklist does not work for every loan. Student loans need enrollment and tuition evidence; business loans need registration and cash-flow evidence; home-improvement loans may need property authorization and contractor estimates.

### 5. Slow missing-document follow-up

Applicants may receive vague requests such as "send more documents" instead of a precise list of missing evidence and the reason it is required.

### 6. Repeated calculations

Teams repeatedly calculate income, payment capacity, debt-to-income ratio, credit risk, and affordability instead of focusing on exceptions.

### 7. Sequential bottlenecks

One team may wait for another team to finish reviewing a document even when income, credit, and appraisal checks could happen in parallel.

### 8. Weak audit trail

It can be difficult to reconstruct which document was used, which SOP rule was applied, why a check failed, and who made the final decision.

### 9. Limited operational visibility

Managers may not have a single dashboard showing application age, document counts, passed and failed checks, pending requests, and human-review status.

### 10. Compliance and privacy risk

Sensitive financial data requires controlled access, retention rules, encryption, and careful handling of model prompts and outputs.

## Impact

These pain points lead to:

- Longer application turnaround times
- Higher operations cost
- More conditional approvals and repeated touches
- Customer frustration
- Inconsistent decisions
- Increased audit preparation effort
- Greater risk of missing evidence or applying the wrong procedure

## Root Cause

The core issue is not simply the absence of automation. It is the lack of a coordinated workflow that connects intake, document intelligence, category-specific SOPs, deterministic financial tools, notifications, and human review in one traceable process.
