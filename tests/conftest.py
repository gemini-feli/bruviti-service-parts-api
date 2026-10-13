
"""Independent dataset for testing catalogue rules."""

import csv
import pytest

from app.catalogue import PartsCatalogue


def write_csv(path, columns, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)


def create_fixture_data(data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)

    # A small machine structure containing:
    # - a duplicate relationship
    # - a shared component
    # - a cycle
    # - disconnected parts

    write_csv(
        data_dir / "bom.csv",
        ["parent_pn", "child_pn", "quantity"],
        [
            ["AS-40000", "AS-1", "2"],
            [" as-40000 ", " as-1 ", "2"],
            ["AS-40000", "FA-9", "4"],
            ["AS-1", "FA-9", "3"],
            ["AS-1", "EL-5", "1"],
            ["AS-1", "AS-40000", "1"],
            ["OUT-1", "OUT-2", "1"],
        ],
    )

    write_csv(
        data_dir / "parts_master.csv",
        [
            "part_number", "revision", "description",
            "category", "unit_cost"
        ],
        [
            ["AS-40000", "A", "AM-700 machine", "Assembly", "500"],
            ["AS-1", "A", "Main assembly", "Assembly", "100"],
            ["FA-9", "B", "Latest fastener", "Fastener", "12"],
            ["fa-9", "A", "Older fastener", "Fastener", "8"],
            ["OUT-1", "A", "Unrelated part", "Assembly", "99"],
        ],
    )

    write_csv(
        data_dir / "service_parts.csv",
        [
            "part_number", "field_replaceable",
            "serial_from", "serial_to"
        ],
        [
            ["AS-1", " y ", "1000", "1999"],
            ["FA-9", "Y", "", ""],
            ["EL-5", "Y", "1000", "1999"],
            ["OUT-1", "Y", "", ""],
        ],
    )

    return data_dir


@pytest.fixture
def data_factory():
    return create_fixture_data


@pytest.fixture
def example_data_dir(tmp_path):
    return create_fixture_data(tmp_path / "data")


@pytest.fixture
def catalogue(example_data_dir):
    return PartsCatalogue(data_dir=example_data_dir)
