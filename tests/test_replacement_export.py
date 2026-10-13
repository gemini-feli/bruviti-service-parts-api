
import csv

from app.catalogue import PartsCatalogue


def write_csv(path, headers, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def test_replacement_export(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()

    # A different machine structure with shared assemblies,
    # a duplicate relationship, and a cycle.

    write_csv(
        folder / "bom.csv",
        ["parent_pn", "child_pn", "quantity"],
        [
            ["AS-40000", "AS-1", 2],
            [" as-40000 ", " as-1 ", 2],
            ["AS-40000", "AS-2", 3],
            ["AS-40000", "AS-4", 1],
            ["AS-1", "AS-4", 4],
            ["AS-2", "AS-4", 5],
            ["AS-4", "EL-1", 2],
            ["AS-4", "AS-1", 1],
            ["OUT-1", "OUT-2", 1],
        ]
    )

    write_csv(
        folder / "parts_master.csv",
        [
            "part_number", "revision", "description",
            "category", "unit_cost"
        ],
        [
            ["AS-40000", "A", "Machine", "Assembly", 500],
            ["AS-1", "A", "Assembly 1", "Assembly", 100],
            ["AS-2", "A", "Assembly 2", "Assembly", 100],
            ["AS-4", "A", "Old shared assembly", "Assembly", 50],
            ["AS-4", "B", "New shared assembly", "Assembly", 60],
            ["OUT-1", "A", "Outside part", "Assembly", 20],
        ]
    )

    write_csv(
        folder / "service_parts.csv",
        [
            "part_number", "field_replaceable",
            "serial_from", "serial_to"
        ],
        [
            ["AS-1", "Y", 100, 200],
            ["AS-2", "N", "", ""],
            ["AS-4", "Y", "", ""],
            ["EL-1", "Y", 100, 200],
        ]
    )

    catalogue = PartsCatalogue(data_dir=folder)

    # Verify catalogue counts.
    assert catalogue.validation() == {
        "parts": 5,
        "ready": 2,
        "missing": 1,
        "not_replaceable": 2
    }

    # Verify duplicate and cycle handling.
    assert catalogue.data_summary["bom_duplicates_removed"] == 1
    assert ("AS-4", "AS-1", 1) in catalogue.removed_cycle_edges

    # Verify shared assembly quantities.
    assert catalogue.get_part("AS-4")["total_quantity"] == 24
    assert catalogue.get_part("EL-1")["total_quantity"] == 48

    # Verify latest revision.
    assert catalogue.get_part("AS-4")["revision"] == "B"

    # Verify all paths through the shared assembly.
    assert catalogue.get_paths("EL-1")["paths"] == [
        ["AS-40000", "AS-1", "AS-4", "EL-1"],
        ["AS-40000", "AS-2", "AS-4", "EL-1"],
        ["AS-40000", "AS-4", "EL-1"],
    ]

    # Verify inclusive serial boundaries.
    assert catalogue.applicable_parts(100)["applicable_parts"] == 2
    assert catalogue.applicable_parts(200)["applicable_parts"] == 2
    assert catalogue.applicable_parts(201)["applicable_parts"] == 1

    # Verify unrelated parts are excluded.
    assert "OUT-1" not in catalogue.parts
    assert "OUT-2" not in catalogue.parts
