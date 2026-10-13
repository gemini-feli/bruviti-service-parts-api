# Data Analysis and Reconciliation

## 1. Data Sources

The application uses only the three CSV exports supplied for Bruviti Use Case 5.

| Source | Original rows | Purpose |
|---|---:|---|
| `bom.csv` | 1,287 | Machine assembly relationships and quantities |
| `parts_master.csv` | 950 | Part metadata, descriptions, and revisions |
| `service_parts.csv` | 854 | Field replaceability and serial-number applicability |

No external datasets, databases, APIs, or additional product catalogues are used.

The supplied dataset describes the Arcadia AM-700 bottling machine, rooted at part number `AS-40000`.

All source files are read from the repository's `data/` directory. The application reconstructs its catalogue from these files during startup.

## 2. Observed Data Quality Issues

Analysis of the supplied CSV exports identified the following issues:

| Issue | Observation | Resolution |
|---|---|---|
| Duplicate BOM relationships | 40 repeated relationship records | Treat each normalized parent-child pair as one relationship |
| Inconsistent identifiers | Variations in capitalization and surrounding whitespace | Normalize using `strip().upper()` |
| Multiple part revisions | 63 parts have multiple revisions | Select the highest normalized revision |
| Missing master records | 25 in-machine parts lack master metadata | Preserve them with `missing` status and null description/revision |
| Missing or non-Y service permission | Some master parts are not marked field-replaceable | Classify them as `not_replaceable` |
| Circular assembly relationship | `AS-40209 → AS-40002` points back to an ancestor | Exclude the cycle-forming relationship |
| Disconnected components | 5 BOM-referenced parts are outside the AM-700 hierarchy | Exclude them from catalogue results |

### 2.1 Results After Initial Reconciliation

| Metric | Count |
|---|---:|
| Original BOM records | 1,287 |
| Unique BOM relationships | 1,247 |
| Duplicate BOM records removed | 40 |
| Original parts-master records | 950 |
| Unique master parts | 855 |
| Parts with multiple revisions | 63 |
| Original service-list records | 854 |
| Unique service-list parts | 854 |

### 2.2 Final Machine Catalogue

After graph construction, cycle handling, and reachability filtering:

| Status | Count |
|---|---:|
| Total machine parts | 875 |
| Ready | 483 |
| Missing | 25 |
| Not replaceable | 367 |

The status counts reconcile to the total:

**483 + 25 + 367 = 875**

These values describe the original supplied export. They are not hardcoded in the application and will be recalculated when the CSV files are replaced.

## 3. Reconciliation Rules and Engineering Decisions

### 3.1 Part Number Normalization

Part numbers are standardized by removing surrounding whitespace and converting characters to uppercase.

For example:

- ` fa-30019 `
- `FA-30019`
- `fa-30019`

All are normalized to `FA-30019`.

This ensures that records from the three different systems can be matched consistently.

### 3.2 Duplicate BOM Relationships

A normalized parent-child relationship represents a single engineering fact.

Repeated export rows must not increase the actual component quantity.

For example, if the relationship `AS-1 → FA-9` with quantity 4 appears twice, the accepted relationship still has quantity 4.

When conflicting positive quantities exist for the same normalized parent-child pair:

1. Select the most frequently occurring quantity.
2. If frequencies are equal, select the smallest positive quantity.
3. Record conflicting quantities in the data diagnostics.

This is a deterministic fallback assumption for ambiguous data, not an explicitly prescribed rule in the assignment.

Relationships with missing identifiers, invalid quantities, or nonpositive quantities are skipped and recorded as data problems.

### 3.3 Current Part Revision

A part can appear in the master file with several revisions.

The latest revision is selected using the highest normalized revision value, following the assignment's highest-letter rule.

For example, revision `B` is preferred over revision `A`.

If multiple records share the same highest revision but contain different metadata, the implementation uses a deterministic comparison of description, category, and unit cost to choose one record independently of CSV row order.

The selected record supplies the part's description and revision.

### 3.4 Machine Membership and Reachability

The AM-700 catalogue contains:

- Root part `AS-40000`.
- Every part reachable from that root through accepted BOM relationships.

Parts belonging only to disconnected assemblies or unrelated exports are excluded.

The five BOM-referenced parts outside the machine in the supplied dataset are:

- `AS-40210`
- `EL-10336`
- `EL-10337`
- `ME-20307`
- `ME-20308`

Parts present only in the master or service lists are also excluded if they are not reachable from the machine root.

This ensures that catalogue totals represent one complete AM-700 rather than every part appearing across all source systems.

### 3.5 Cycle Detection and Handling

An assembly cannot directly or indirectly contain itself.

For example, the following relationships would be invalid:

- Assembly A contains Assembly B.
- Assembly B contains Assembly C.
- Assembly C contains Assembly A.

The implementation uses iterative Depth-First Search (DFS), beginning at `AS-40000`.

During traversal:

- An active node is one currently being explored.
- A completed node has already been fully explored.
- An edge pointing to an active ancestor is identified as a cycle-forming back-edge and excluded.

The supplied dataset contains the offending relationship:

**`AS-40209 → AS-40002`, quantity 1**

This relationship is removed from the accepted graph.

Child relationships are traversed in sorted order to make the cycle-removal process deterministic.

The accepted graph is then processed as a Directed Acyclic Graph (DAG).

### 3.6 Part Status Classification

Every part reachable from the machine root is assigned exactly one status.

| Status | Condition |
|---|---|
| `missing` | No record exists in the parts master |
| `ready` | A master record exists and at least one service record is marked `Y` |
| `not_replaceable` | A master record exists, but no service record is marked `Y` |

Status evaluation follows this precedence:

1. If the part is absent from the master, classify it as `missing`.
2. Otherwise, if any service record is marked `Y`, classify it as `ready`.
3. Otherwise, classify it as `not_replaceable`.

A missing part remains in the reconstructed machine graph but returns null values for its description and revision.

Serial-number applicability is evaluated separately from part status.

If conflicting service records exist, a `Y` record is treated as evidence of field replaceability. This is a documented assumption because the brief does not specify how conflicting service permissions should be prioritized.

### 3.7 Total Quantity Calculation

Total quantity represents the number of physical units of a part contained in one complete AM-700 machine.

The root part always has total quantity 1.

Quantities are calculated by propagating the accumulated quantity of each parent through its child relationships in topological order.

For every accepted relationship:

`child_total += parent_total × relationship_quantity`

If a part appears through several assemblies, all valid contributions are added.

**Example:**

- The root contains 4 fasteners directly.
- The root also contains 2 assemblies.
- Each assembly contains 3 additional fasteners.

The total number of fasteners is:

**4 + (2 × 3) = 10**

Topological processing ensures that contributions from parent assemblies are accumulated before their child quantities are propagated.

In the supplied dataset, `FA-30019` has a calculated total quantity of **178**.

### 3.8 Assembly Paths

An assembly path identifies a sequence of parts from the machine root to a requested component.

Every returned path:

- Begins at `AS-40000`.
- Ends at the requested part.
- Follows accepted parent-child relationships.
- Is sorted lexicographically against other paths.

A shared part can appear in multiple assemblies and therefore have multiple valid paths.

The implementation traverses reverse parent relationships to enumerate these paths and sorts the completed results.

For the supplied dataset, `FA-30012` has **17 assembly paths**.

### 3.9 Serial Applicability

Serial applicability is evaluated independently of field-replaceable status.

Only parts classified as `ready` can be counted as applicable.

A ready part is applicable if at least one valid service record marked `Y` covers the requested machine serial number.

The following rules are applied:

- Serial-range boundaries are inclusive.
- A blank lower bound means there is no lower restriction.
- A blank upper bound means there is no upper restriction.
- Both bounds blank means the record applies to all serial numbers.
- If multiple valid intervals match, the part is counted only once.
- Records marked `N` do not contribute to applicable-part counts.

For the supplied dataset, serial number `2500` has **448 applicable ready part types**.

#### Handling Malformed Serial Ranges

Service records with non-numeric or reversed serial bounds are retained for determining field-replaceable status.

For example:

`Part EL-1 | Replaceable Y | Serial from 2000 | Serial to 1000`

Although the range is invalid, the `Y` permission remains available when determining whether the part is `ready`.

However, the malformed interval:

- Is flagged as a data-quality problem.
- Is excluded from serial applicability calculations.
- Is never interpreted as an unrestricted serial range.

A record with genuinely blank bounds remains unrestricted, whereas a malformed range does not match any serial.

This prevents invalid serial metadata from incorrectly changing a part's replaceability classification.

The policy is a documented reconciliation assumption because the assignment does not explicitly define malformed-range precedence.

## 4. Test Design and Verification

Testing uses the original supplied export and independent synthetic datasets.

### 4.1 Original Export Regression

The supplied dataset was examined using `check_data.py` and `check_catalogue.py`.

Verification included:

- Original CSV row counts and deduplicated relationships.
- Latest revision selection.
- Reachability from `AS-40000`.
- Observed cycle detection and removal.
- Disconnected part identification.
- Catalogue status counts.
- Shared-part quantity calculations.
- Sorted assembly paths.
- Serial-number applicability.

The supplied-data regression checks include:

| Check | Expected value |
|---|---:|
| Total catalogue parts | 875 |
| Ready parts | 483 |
| Missing parts | 25 |
| Not-replaceable parts | 367 |
| Applicable parts for serial 2500 | 448 |
| Total quantity of `FA-30019` | 178 |
| Assembly paths for `FA-30012` | 17 |

### 4.2 Independent Synthetic Datasets

Automated tests create temporary CSV exports with deliberately challenging data.

The test scenarios cover:

- Part-number capitalization and whitespace differences.
- Duplicate BOM relationships.
- Conflicting BOM quantities.
- Circular relationships and cycle removal.
- Disconnected parts.
- Multiple part revisions.
- Shared components with multiple parents.
- Quantity propagation through nested assemblies.
- Missing master records.
- Conflicting or missing service permissions.
- Inclusive serial-number boundaries.
- Unrestricted serial ranges.
- Invalid and reversed serial-number intervals.
- Preservation of `Y` replaceability despite malformed serial ranges.
- Exclusion of malformed intervals from compatibility counts.
- Invalid API queries and unknown parts.
- Case-insensitive API lookups.
- Input row-order independence.
- Missing input-file errors.

Synthetic datasets are isolated in temporary test directories and do not overwrite the repository's original `data/` files.

### Randomized Replacement-Data Verification

An additional automated test generates 30 independent synthetic CSV exports with varying assembly structures, shared components, duplicate relationships, quantities, revisions, part statuses, and serial ranges.

For each generated export, the expected catalogue results are calculated independently and compared with the implementation.

All 30 generated datasets passed. These tests strengthen confidence in generalization to unseen acyclic machine structures but do not guarantee correctness for every possible malformed or cyclic dataset.

The complete automated test suite contains **35 passing tests**.

### 4.3 Automated Test Results

The final automated test suite contains **35 passing tests**.

A dedicated regression test verifies that malformed serial ranges do not erase field-replaceability information and are not accidentally treated as unrestricted intervals.

Tests were executed using:

`python -m pytest tests/ -q`

The latest local execution completed with:

**35 passed, 1 non-failing dependency deprecation warning.**

The tests validate the implemented behavior for the scenarios covered, but they do not prove correctness for every possible unseen dataset.

### 4.4 Startup and API Verification

The application was also tested from a fresh GitHub clone.

Verification confirmed that:

- `python start.py` creates the Python environment when necessary, installs dependencies, and launches the application.
- FastAPI serves the application on port `8000`.
- `GET /health` returns HTTP 200 and `{"status":"ok"}`.
- Required catalogue endpoints respond successfully.
- Invalid inputs produce appropriate HTTP error responses.
- The interactive dashboard is served from `/`.
- Tested API responses completed within the assignment's one-second limit.

The running API processes local data without external inference or API calls.

## 5. Replacement Dataset Support

At grading time, Bruviti may replace the repository's `data/` folder with another export containing the same CSV filenames and column structure.

The implementation is designed to accommodate this because:

- CSV parsing uses column names rather than fixed row positions.
- Part identifiers are normalized dynamically.
- Duplicate relationships and revisions are reconciled by general rules.
- The machine graph is reconstructed from the current BOM.
- Part statuses and total quantities are recalculated.
- Assembly paths are derived from the reconstructed graph.
- Serial compatibility is evaluated using the currently loaded service records.
- Catalogue counts are computed rather than hardcoded.

The machine root `AS-40000` is defined by the assignment specification.

After replacing the CSV files and restarting the service, the application reconstructs the catalogue using the replacement data.

The synthetic test suite provides evidence of generalization beyond the original export, although unseen data-quality conditions may reveal additional edge cases.

## 6. Remaining Assumptions and Limitations

Some data-quality situations do not have an explicitly prescribed precedence rule in the assignment.

The implementation therefore makes the following documented decisions:

1. **Conflicting BOM quantities:** Select the most frequent valid quantity, using the smallest positive quantity as a tie-breaker.
2. **Conflicting latest-revision metadata:** Apply deterministic metadata comparison to avoid CSV row-order dependence.
3. **Conflicting service permissions:** Treat at least one `Y` record as evidence of field replaceability.
4. **Malformed serial ranges:** Preserve the permission flag, record the issue, and exclude the invalid interval from serial matching.
5. **Complex cycles:** Remove DFS back-edges pointing to active ancestors. More complicated cyclic graphs may admit different edge-removal choices depending on the intended interpretation of the relationships.

Additional limitations include:

- The application is read-only and does not modify the original CSV files.
- The catalogue is reconstructed at startup rather than reloaded automatically when files change.
- Extremely large graphs with many valid assembly paths may require additional performance optimization.
- Data-quality problems are recorded in internal diagnostics and described in this document; the required API contract does not expose a separate diagnostics endpoint.
- No external authoritative source is available to resolve ambiguous, conflicting engineering records.

The chosen approach prioritizes deterministic behavior, traceability, exact API responses, and reproducible testing.

The final application is designed to process replacement exports with the documented schema while keeping reconciliation decisions transparent.