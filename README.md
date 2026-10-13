# Arcadia Service Parts Catalogue API

**Bruviti Campus Drive 2026 — Use Case 5**

A deterministic, offline-capable service parts catalogue API for the fictional Arcadia Machines AM-700 bottling line.

## 1. Overview

The application reconciles three engineering and service CSV exports to answer four important maintenance questions:

- What is a particular machine part?
- Where does it sit within the machine?
- Is it field-replaceable?
- Does it apply to a specified machine serial number?

The implementation uses rule-based data reconciliation and graph algorithms rather than machine learning or external AI services.

## 2. Technology Stack

- Python 3.13 (tested with Python 3.13.5)
- FastAPI and Uvicorn
- Python standard library (`csv`, `collections`, `heapq`, `pathlib`)
- Pytest and HTTPX for automated testing
- HTML, CSS and JavaScript for the demonstration dashboard

No GPU, model training, external database, API key or paid service is required.

## 3. Quick Start

**Prerequisite:** Python 3.13 and pip must be installed and accessible from the terminal.

From the repository root, run:

```bash
python start.py
```

The startup script automatically:

1. Creates a `.venv` virtual environment if one does not exist.
2. Installs the required Python dependencies from `requirements.txt`.
3. Launches the FastAPI application on port 8000.

The first installation requires access to the Python package index. Once dependencies are installed, API requests and catalogue processing require no network connection.

### Application URLs

| URL | Description |
|---|---|
| `http://localhost:8000/` | Interactive catalogue dashboard |
| `http://localhost:8000/docs` | FastAPI interactive documentation |
| `http://localhost:8000/health` | Readiness check |

A successful health request returns:

```json
{"status": "ok"}
```

Stop the server using `Ctrl+C`.

## 4. Input Data

Place all three CSV files in the `data/` directory:

```text
data/
├── bom.csv
├── parts_master.csv
└── service_parts.csv
```

**bom.csv**

Columns: `parent_pn`, `child_pn`, `quantity`

Describes parent-child assembly relationships and quantities.

**parts_master.csv**

Columns: `part_number`, `revision`, `description`, `category`, `unit_cost`

Provides part descriptions and revision information.

**service_parts.csv**

Columns: `part_number`, `field_replaceable`, `serial_from`, `serial_to`

Specifies field replaceability and machine serial applicability.

The application reads these files on startup. Replacing the CSV files with another export of the same schema does not require modifying or retraining the application. Restart the server to load the new data.

The machine root is `AS-40000`.

## 5. API Endpoints

### GET /health

Returns service readiness.

### GET /api/validation

Returns counts for all machine parts, including `ready`, `missing` and `not_replaceable`.

### GET /api/parts/{part_number}

Returns the requested part's:

- Normalized part number
- Description and latest revision
- Replacement status
- Total quantity per machine
- Sorted immediate parents
- Sorted immediate children and their quantities

Part identifiers are matched without case sensitivity.

### GET /api/parts/{part_number}/paths

Returns all sorted assembly paths from `AS-40000` to the requested part.

### GET /api/serial/{serial}

Returns the number of distinct ready parts applicable to the supplied machine serial number.

Range endpoints are inclusive. A ready part without serial bounds applies to every serial number.

### Error Handling

- Parts outside the machine catalogue return HTTP 404.
- Invalid serial values return HTTP 422.
- Invalid data rows are handled according to the documented reconciliation rules.

## 6. How the Application Works

1. **Data ingestion:** Read and validate all three CSV files.
2. **Normalization:** Standardize part identifiers and relevant field values.
3. **Reconciliation:** Deduplicate relationships and select the latest part revisions.
4. **Graph construction:** Build the reachable machine hierarchy and exclude ancestor-pointing cycle relationships.
5. **Quantity calculation:** Use topological processing to accumulate quantities across assembly paths.
6. **Catalogue generation:** Determine part status, parent-child relationships, and serial applicability.
7. **API delivery:** Serve the preprocessed catalogue through FastAPI.

The machine is represented as a directed graph because individual parts may appear in multiple assemblies.

Catalogue preprocessing occurs at startup, avoiding repeated CSV parsing for each request.

## 7. Testing

The project includes automated tests covering API behavior, graph calculations, data reconciliation, and edge cases.

After running the startup command at least once, open a second terminal and run:

**Windows:**

```bat
.venv\Scripts\python.exe -m pytest tests/ -v
```

**Linux/macOS:**

```bash
.venv/bin/python -m pytest tests/ -v
```

The current test suite contains 35 tests.

Testing includes:

- Duplicate BOM relationships
- Inconsistent capitalization and whitespace
- Missing master records
- Latest revision selection
- Cycle detection and removal
- Disconnected components
- Shared parts and quantity multiplication
- Sorted paths
- Serial boundary inclusivity
- Unknown parts and invalid input
- API response contracts

Tests use a separate synthetic dataset so they do not depend solely on the original supplied export.

For a regression check against the original supplied CSVs, run:

```bash
python check_catalogue.py
```

## 8. Demonstration Interface

The single-page dashboard at `/` supports catalogue validation, part lookup, assembly-path lookup, and serial compatibility checks.

The dashboard communicates with the same FastAPI application using JavaScript `fetch()` requests and displays real API responses.

No external frontend framework or CDN is required.

## 9. Additional Documentation

- `DATA.md`: Input data analysis, reconciliation rules and test design
- `NOTES.md`: Design choices, assumptions, limitations and future improvements
- `AI.md`: AI tools used and their purposes

## 10. Operational Constraints

- Runs locally on port 8000
- No request-time LLM or external API calls
- No GPU or training required
- No API keys or secrets required
- Works with replacement CSV files following the documented schema
- Uses the same FastAPI process for API endpoints and the webpage
