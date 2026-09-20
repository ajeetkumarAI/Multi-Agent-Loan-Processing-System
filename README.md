# Multi-Agent-Loan-Processing-System

A lightweight Agno-based multi-agent loan processing system organized around four sequential stages: concierge intake, document verification, processing, and compliance review.

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
