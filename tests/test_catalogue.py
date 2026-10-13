
"""Graph and catalogue tests using independent CSV files."""


def test_validation(catalogue):
    assert catalogue.validation() == {
        "parts": 4,
        "ready": 2,
        "missing": 1,
        "not_replaceable": 1,
    }


def test_duplicate_and_cycle_handling(catalogue):
    assert catalogue.data_summary["bom_duplicates_removed"] == 1

    assert (
        "AS-1", "AS-40000", 1
    ) in catalogue.removed_cycle_edges

    assert catalogue.get_part("AS-40000")["parents"] == []


def test_outside_parts_excluded(catalogue):
    assert catalogue.outside_machine == [
        "OUT-1", "OUT-2"
    ]

    assert "OUT-1" not in catalogue.parts
    assert "OUT-2" not in catalogue.parts


def test_quantities_include_all_assembly_paths(catalogue):
    assert catalogue.get_part("AS-40000")["total_quantity"] == 1
    assert catalogue.get_part("AS-1")["total_quantity"] == 2
    assert catalogue.get_part("FA-9")["total_quantity"] == 10
    assert catalogue.get_part("EL-5")["total_quantity"] == 2


def test_part_details_and_latest_revision(catalogue):
    part = catalogue.get_part("fa-9")

    assert part["revision"] == "B"
    assert part["description"] == "Latest fastener"
    assert part["parents"] == ["AS-1", "AS-40000"]
    assert part["children"] == []

    missing = catalogue.get_part("EL-5")

    assert missing["description"] is None
    assert missing["revision"] is None
    assert missing["status"] == "missing"


def test_all_paths_and_sorting(catalogue):
    paths = catalogue.get_paths("FA-9")["paths"]

    assert paths == [
        ["AS-40000", "AS-1", "FA-9"],
        ["AS-40000", "FA-9"],
    ]

    assert catalogue.get_paths("AS-40000")["paths"] == [
        ["AS-40000"]
    ]


def test_serial_boundaries(catalogue):
    assert catalogue.applicable_parts(999)["applicable_parts"] == 1
    assert catalogue.applicable_parts(1000)["applicable_parts"] == 2
    assert catalogue.applicable_parts(1999)["applicable_parts"] == 2
    assert catalogue.applicable_parts(2000)["applicable_parts"] == 1
