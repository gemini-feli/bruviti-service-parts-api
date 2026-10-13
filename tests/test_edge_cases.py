
"""Tests for malformed, conflicting, and disconnected data."""

import pytest

from app.catalogue import PartsCatalogue
from app.data_loader import load_data


@pytest.mark.parametrize(
    "part_number",
    ["UNKNOWN-999", "OUT-1", "OUT-2"]
)
def test_unknown_or_disconnected_part(catalogue, part_number):
    with pytest.raises(KeyError):
        catalogue.get_part(part_number)

    with pytest.raises(KeyError):
        catalogue.get_paths(part_number)


@pytest.mark.parametrize(
    "serial",
    ["1000", 1.5, None, True]
)
def test_invalid_internal_serial_type(catalogue, serial):
    with pytest.raises(ValueError):
        catalogue.applicable_parts(serial)


def test_conflicting_duplicate_bom_quantities_logged(
    tmp_path, data_factory
):
    folder = data_factory(tmp_path / "alternate")

    with (folder / "bom.csv").open("a", encoding="utf-8") as f:
        f.write("AS-40000,AS-1,7\n")

    loaded = load_data(folder)

    assert loaded["bom"][("AS-40000", "AS-1")] == 2

    assert any(
        "Conflicting quantities" in problem
        for problem in loaded["problems"]
    )


def test_row_order_does_not_change_results(
    tmp_path, data_factory
):
    folder = data_factory(tmp_path / "reordered")

    path = folder / "bom.csv"
    rows = path.read_text(
        encoding="utf-8"
    ).splitlines()

    reversed_rows = [rows[0], *reversed(rows[1:])]

    path.write_text(
        "\n".join(reversed_rows) + "\n",
        encoding="utf-8"
    )

    updated = PartsCatalogue(data_dir=folder)

    assert updated.validation() == {
        "parts": 4,
        "ready": 2,
        "missing": 1,
        "not_replaceable": 1,
    }

    assert updated.get_part("FA-9")["total_quantity"] == 10

    assert updated.get_paths("FA-9")["paths"] == [
        ["AS-40000", "AS-1", "FA-9"],
        ["AS-40000", "FA-9"],
    ]


def test_missing_input_file_raises_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        PartsCatalogue(data_dir=tmp_path)
