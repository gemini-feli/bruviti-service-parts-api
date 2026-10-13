# Data Analysis and Reconciliation

## 1. Data Sources

The application uses only the three CSV exports supplied for Bruviti Use Case 5:

| Source | Original rows | Purpose |
|---|---:|---|
| bom.csv | 1,287 | Machine assembly relationships |
| parts_master.csv | 950 | Part metadata and revisions |
| service_parts.csv | 854 | Field replaceability and serial applicability |

No external data, database, APIs, or additional product catalogues are used.

The supplied dataset describes the AM-700 machine rooted at `AS-40000`.

## 2. Observed Data Quality Issues

The initial CSV analysis identified the following:

| Issue | Observation | Resolution |
|---|---|---|
| Duplicate BOM relationships | 40 repeated rows | Treat each normalized parent-child pair as a single relationship |
| Inconsistent identifiers | Mixed capitalization and whitespace | Apply `strip().upper()` |
| Multiple revisions | 63 parts have multiple revision values | Select the highest revision |
| Missing metadata | 25 in-machine parts lack master records | Preserve them with `missing` status and null description/revision |
| Missing or negative service permission | Some master parts lack Y service marking | Classify as `not_replaceable` |
| Circular relationship | `AS-40209 → AS-40002` points back to an ancestor | Remove the offending relationship |
| Disconnected parts | 5 BOM-referenced parts are outside the AM-700 graph | Exclude them from catalogue results |

### Results After Initial Reconciliation

- Unique BOM relationships: **1,247**
- Unique parts in the master: **855**
- Unique service-list parts: **854**

After graph construction and reachability filtering:

| Status | Count |
|---|---:|
| Total machine parts | 875 |
| Ready | 483 |
| Missing | 25 |
| Not replaceable | 367 |

These values describe the supplied dataset only. They are not hardcoded in the application.

## 3. Reconciliation Rules

### 3.1 Part Normalization

Part numbers are standardized by removing surrounding whitespace and converting to uppercase.

For example, ` fa-30019 ` and `FA-30019` refer to the same part.

### 3.2 Duplicate BOM Relationships

An identical parent-child relationship represents one engineering fact. Repeated exports must not multiply the quantity.

If conflicting positive quantities exist for the same normalized pair, the implementation selects the most frequently occurring quantity. Ties are resolved using the smallest positive quantity.

This is a deterministic fallback assumption for an ambiguous condition, not an explicitly prescribed engineering rule.

Invalid or nonpositive BOM quantities are skipped and recorded as data problems.

### 3.3 Current Revision

The latest revision is selected using the highest normalized revision value.

When duplicate records share the same latest revision, a deterministic comparison of their metadata is used to avoid depending on input order.

### 3.4 Machine Membership

The catalogue includes only `AS-40000` and parts reachable through its accepted BOM relationships.

The five disconnected BOM parts in the supplied export are:

- AS-40210
- EL-10336
- EL-10337
- ME-20307
- ME-20308

Parts that occur only in the master or service list are also excluded when they are not reachable from the root.

### 3.5 Cycle Handling

An assembly cannot contain itself directly or indirectly.

The implementation uses iterative depth-first traversal and removes relationships pointing to a currently active ancestor.

The supplied data contains the offending relationship:

`AS-40209 → AS-40002`, quantity 1.

This relationship is excluded from the accepted graph.

Traversal order is sorted to keep cycle handling deterministic.

### 3.6 Part Status

Statuses are assigned in this order:

1. `missing`: no parts-master entry exists.
2. `ready`: a master record exists and at least one service record is marked Y.
3. `not_replaceable`: a master record exists, but no service record is marked Y.

Serial applicability is evaluated separately from part status.

If conflicting service records exist, a Y-marked record is treated as evidence of field replaceability. A serial matches if any Y-marked interval covers it.

This is an implementation assumption for conflicting records, since the brief does not define their precedence.

### 3.7 Total Quantity

Quantity represents the number of units required for one complete machine.

The root has quantity 1.

Quantities propagate along the accepted directed graph in topological order. When a part appears through multiple assemblies, contributions from all paths are added.

For example:

- Root contains 4 units of a fastener directly.
- Root contains 2 assemblies.
- Each assembly contains 3 fasteners.

Total fastener quantity = 4 + (2 × 3) = 10.

### 3.8 Assembly Paths

Every path begins at the root and ends at the requested part.

Shared components can have multiple paths. Paths are sorted lexicographically by part number.

### 3.9 Serial Applicability

Only ready parts are considered.

A part is applicable when the serial lies within an eligible interval, including both endpoints.

Blank serial bounds are treated as unbounded. Two blank bounds therefore apply to all serial numbers.

Each applicable part is counted once, even if multiple service ranges match.

Invalid or reversed serial ranges are recorded and excluded from the service data.

## 4. Test Design

Tests use two complementary datasets.

### Original Export Regression

The provided dataset is checked using `check_data.py` and `check_catalogue.py`.

This verifies known counts, the observed cycle, disconnected parts, a shared-part quantity, multiple assembly paths, and serial compatibility.

### Independent Synthetic Dataset

The automated tests generate temporary CSV files with deliberately challenging data, including:

- Case and whitespace variations
- Duplicate BOM relationships
- Conflicting relationship quantities
- Cyclic and disconnected relationships
- Multiple revisions
- Shared components
- Missing master entries
- Serial ranges and boundary conditions
- Invalid queries and unknown parts
- Reordered input rows

The synthetic data is isolated from the repository's production `data/` folder.

## 5. Replacement Dataset Support

The implementation uses the documented column names rather than hardcoded row identifiers or expected output values.

Replacing the three CSVs with another export of the same schema causes the catalogue to be reconstructed on restart.

The automated test suite uses synthetic data independently of the original export.

## 6. Remaining Assumptions and Limitations

The dataset contains some situations for which the brief does not define an explicit precedence rule, especially conflicting BOM quantities and conflicting service permissions.

The chosen fallback rules prioritize deterministic behavior, traceability, and consistent outputs.

Cycle removal is based on depth-first ancestor detection. More complex cyclic input structures may admit multiple valid edge-removal choices; the current algorithm uses sorted traversal for consistency.

The application is intentionally read-only and does not alter source CSV files. Data problems are retained in internal diagnostics and the documented analysis.
