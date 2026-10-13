
"""Read, clean, and reconcile the three CSV files."""

import csv
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def normalize_part_number(value):
    """Remove surrounding spaces and standardize capitalization."""
    return (value or "").strip().upper()


def read_csv(path, required_columns):
    """Read a CSV and check its required columns."""

    if not path.is_file():
        raise FileNotFoundError(f"Required data file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path.name}")

        reader.fieldnames = [field.strip() for field in reader.fieldnames]

        missing = set(required_columns) - set(reader.fieldnames)

        if missing:
            raise ValueError(
                f"{path.name} missing columns: {sorted(missing)}"
            )

        return list(reader)


def parse_optional_serial(value, file_label, row_number):
    """Convert a serial bound to an integer or None."""

    text = (value or "").strip()

    if not text:
        return None

    try:
        return int(text)
    except ValueError as exc:
        raise ValueError(
            f"{file_label} row {row_number}: invalid serial {text!r}"
        ) from exc


def load_data(data_dir=None):
    """Load and normalize the complete parts dataset."""

    folder = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR

    bom_rows = read_csv(
        folder / "bom.csv",
        {"parent_pn", "child_pn", "quantity"}
    )

    master_rows = read_csv(
        folder / "parts_master.csv",
        {"part_number", "revision", "description",
         "category", "unit_cost"}
    )

    service_rows = read_csv(
        folder / "service_parts.csv",
        {"part_number", "field_replaceable",
         "serial_from", "serial_to"}
    )

    problems = []

    # STEP A: Normalize and deduplicate BOM relationships.

    bom_candidates = defaultdict(Counter)

    for row_num, row in enumerate(bom_rows, start=2):
        parent = normalize_part_number(row["parent_pn"])
        child = normalize_part_number(row["child_pn"])

        try:
            quantity = int((row["quantity"] or "").strip())
        except ValueError:
            quantity = 0

        if not parent or not child or quantity <= 0:
            problems.append(
                f"bom.csv row {row_num}: invalid relationship"
            )
            continue

        bom_candidates[(parent, child)][quantity] += 1

    bom = {}

    for edge, frequencies in bom_candidates.items():
        # Most frequent quantity wins.
        # If tied, use the smallest positive quantity.
        bom[edge] = min(
            frequencies,
            key=lambda n: (-frequencies[n], n)
        )

        if len(frequencies) > 1:
            problems.append(
                f"Conflicting quantities for {edge}: "
                f"{dict(frequencies)}"
            )

    # STEP B: Keep the latest revision from parts master.

    master = {}
    master_revisions = defaultdict(set)

    for row_num, row in enumerate(master_rows, start=2):
        part = normalize_part_number(row["part_number"])
        revision = (row["revision"] or "").strip().upper()

        if not part or not revision:
            problems.append(
                f"parts_master.csv row {row_num}: "
                "missing part or revision"
            )
            continue

        cleaned = {
            "part_number": part,
            "revision": revision,
            "description": (row["description"] or "").strip(),
            "category": (row["category"] or "").strip(),
            "unit_cost": (row["unit_cost"] or "").strip()
        }

        master_revisions[part].add(revision)
        previous = master.get(part)

        if (
            previous is None
            or revision > previous["revision"]
            or (
                revision == previous["revision"]
                and (
                    cleaned["description"],
                    cleaned["category"],
                    cleaned["unit_cost"]
                ) < (
                    previous["description"],
                    previous["category"],
                    previous["unit_cost"]
                )
            )
        ):
            master[part] = cleaned

    # STEP C: Load and normalize service records.
    # Preserve multiple serial ranges for a part.

    service = defaultdict(list)

    for row_num, row in enumerate(service_rows, start=2):
        part = normalize_part_number(row["part_number"])

        if not part:
            problems.append(
                f"service_parts.csv row {row_num}: missing part"
            )
            continue

        replaceable = (
            row["field_replaceable"] or ""
        ).strip().upper()

        if replaceable not in {"Y", "N"}:
            problems.append(
                f"service_parts.csv row {row_num}: invalid Y/N"
            )
            replaceable = "N"

        
        # Keep the replaceability flag even when serial data is invalid.
        # Invalid ranges must never be treated as unrestricted.

        serial_valid = True

        try:
            serial_from = parse_optional_serial(
                row["serial_from"], "service_parts.csv", row_num
            )
            serial_to = parse_optional_serial(
                row["serial_to"], "service_parts.csv", row_num
            )

        except ValueError as exc:
            problems.append(str(exc))
            serial_valid = False
            serial_from = None
            serial_to = None

        if (
            serial_valid
            and serial_from is not None
            and serial_to is not None
            and serial_from > serial_to
        ):
            problems.append(
                f"service_parts.csv row {row_num}: "
                "reversed serial bounds"
            )
            serial_valid = False

        record = {
            "field_replaceable": replaceable,
            "serial_from": serial_from,
            "serial_to": serial_to
        }

        # Only malformed records need the additional marker.
        # Existing valid-record structure remains unchanged.
        if not serial_valid:
            record["serial_valid"] = False


        if record not in service[part]:
            service[part].append(record)

    # STEP D: Prepare diagnostics.

    summary = {
        "bom_rows": len(bom_rows),
        "bom_relationships": len(bom),
        "bom_duplicates_removed": sum(
            sum(counts.values()) - 1
            for counts in bom_candidates.values()
        ),
        "master_rows": len(master_rows),
        "master_parts": len(master),
        "parts_with_multiple_revisions": sum(
            len(revisions) > 1
            for revisions in master_revisions.values()
        ),
        "service_rows": len(service_rows),
        "service_parts": len(service)
    }

    return {
        "bom": bom,
        "master": master,
        "service": dict(service),
        "summary": summary,
        "problems": problems
    }
