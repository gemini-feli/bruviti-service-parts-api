## Test Design and Data Quality Verification

The catalogue is validated using two approaches:

**1. Supplied dataset regression checks**

The original CSV export is used to verify machine reconstruction, duplicate relationship handling, cycle removal, latest revision selection, part statuses, total quantities, sorted paths, and serial compatibility.

**2. Independent synthetic dataset testing**

A separate dataset is generated during testing to verify that the implementation generalizes to different input records. It includes:

- Duplicate BOM relationships with inconsistent capitalization and whitespace.
- Shared components appearing through multiple assembly paths.
- A circular relationship pointing back to the machine root.
- Disconnected components that must be excluded from the catalogue.
- Multiple part revisions supplied out of revision order.
- Parts missing from the master file.
- Missing service records and serial-number boundary conditions.
- Conflicting duplicate quantities and changes in CSV row order.

The tests use temporary folders rather than modifying production CSV files.

**Conflict-resolution assumptions**

Where duplicate BOM relationships disagree on quantity, the implementation selects the most frequent valid quantity, with the smallest positive quantity used to break ties. This is a deterministic fallback because the supplied specification does not explicitly resolve conflicting quantities.

Where multiple service records exist, the implementation considers a part replaceable if any record explicitly marks it Y, and considers its serial compatible if at least one Y-marked range matches. These assumptions are documented because conflicting service records are not fully specified.

Tests are designed to run locally without external network calls.