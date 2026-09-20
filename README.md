# Multi-Agent-Loan-Processing-System

A lightweight AI-style multi-agent loan processing system that automates customer onboarding, document verification, financial analysis, underwriting, risk assessment, and compliance review through a sequential workflow and human-reviewed final decision package.

## Workflow

The implementation uses specialized agents that run in order:

1. Customer information collection
2. Document verification
3. Financial analysis
4. Underwriting
5. Risk assessment
6. Compliance review
7. Decision-package generation for human review

## Agent Tools

- **Data retrieval tool** for customer profile assembly
- **Document processing tool** for required document verification
- **Financial calculation tool** for payment and debt-to-income analysis
- **Credit analysis tool** for risk-tier assessment
- **Decision-package generation tool** for assembling the final review payload

## Run the demo

```bash
cd /home/runner/work/Multi-Agent-Loan-Processing-System/Multi-Agent-Loan-Processing-System
python -m loan_processing_system
```

## Run tests

```bash
cd /home/runner/work/Multi-Agent-Loan-Processing-System/Multi-Agent-Loan-Processing-System
python -m unittest discover -s tests -p 'test*.py'
```
