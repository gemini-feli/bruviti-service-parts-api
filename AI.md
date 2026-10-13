# AI Tool Usage Disclosure

## 1. Overview

AI tools were used as development assistants to support problem understanding, implementation, testing, and documentation for the Service Parts Catalogue API.

The objective was to use AI-assisted development efficiently while emphasizing deterministic solutions, data accuracy, reproducibility, and compliance with the assignment requirements.

## 2. AI Tools Used

### ChatGPT (OpenAI)

ChatGPT was used during the development process for technical guidance, implementation assistance, and verification support.

**Key contributions:**

- **Requirement interpretation:** Clarifying API specifications, reconciliation rules, expected outputs, and edge cases.
- **Solution architecture:** Structuring the application into data ingestion, normalization, catalogue reconstruction, graph processing, API services, and testing.
- **Implementation assistance:** Generating and refining Python code for CSV processing, cycle detection, quantity propagation, assembly-path discovery, serial compatibility, and FastAPI endpoints.
- **Testing and debugging:** Assisting with synthetic test-data creation, Pytest implementation, edge-case identification, and interpretation of execution results.
- **Interface development:** Supporting the implementation of a lightweight HTML, CSS, and JavaScript dashboard for interacting with the APIs.
- **Technical documentation:** Assisting in organizing and refining the project documentation, including design decisions, reconciliation assumptions, and testing methodology.

### Claude (Anthropic)

Claude was used primarily during the initial problem-analysis phase to understand the assignment from a practical, scenario-based perspective.

**Key contributions:**

- Interpreting the service parts catalogue use case in the context of industrial equipment maintenance.
- Exploring realistic field-service scenarios involving part identification, assembly location, on-site replaceability, and machine serial-number compatibility.
- Clarifying how the provided engineering and service datasets relate to the operational requirements of a maintenance technician.

This helped establish the practical context of the problem before proceeding with implementation.

## 3. Development and Validation Approach

AI-assisted suggestions and generated code were integrated into the project and evaluated through local execution and testing.

The verification process included:

- Examining and reconciling the three supplied CSV datasets.
- Checking catalogue counts, part statuses, revision selection, quantities, and assembly relationships against expected results.
- Developing an independent synthetic dataset to test duplicate records, circular relationships, disconnected components, missing metadata, and shared parts.
- Executing **35 automated tests**, covering catalogue logic, API behavior, serial compatibility, and error handling.
- Manually exercising the FastAPI endpoints and interactive dashboard.
- Maintaining the implementation and documentation through Git version control.

All 35 automated tests passed during the latest local verification. This establishes confidence in the tested scenarios while recognizing that additional unseen datasets may expose further edge cases.

## 4. Technical Approach and AI Independence

Although AI tools assisted with development, **the deployed application does not depend on AI-generated responses or external inference services**.

A rule-based approach was adopted because the problem provides explicit business rules requiring precise and reproducible outputs.

The implementation uses:

- **Data normalization and reconciliation** to resolve inconsistencies between source files.
- **Directed graph representation** to preserve machine assembly relationships.
- **Depth-first search** to identify and exclude cyclic relationships.
- **Topological processing** to calculate quantities across shared assemblies.
- **Deterministic filtering and range checks** to evaluate part status and serial applicability.

These techniques allow the service to process supplied data locally and return structured results without model training or probabilistic inference.

## 5. Responsible AI Usage

AI tools served as assistants for understanding, coding, testing, and documenting the solution.

Generated code and recommendations were not treated as automatically correct; the implementation was exercised against the provided dataset and independent test cases, with the observed results reviewed during development.

The application makes no request-time calls to ChatGPT, Claude, or other AI services. It requires no GPU, paid API, model training, or external inference infrastructure.

Implementation assumptions, trade-offs, and known limitations are documented separately in `DATA.md` and `NOTES.md`.

**AI assistance was used to accelerate development, while correctness, reproducibility, and explainability remained central to the engineering approach.**
