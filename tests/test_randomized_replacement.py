"""Independent randomized-DAG regression test for Bruviti catalogue.

Save this file as tests/test_randomized_replacement.py and run
    python -m pytest tests/test_randomized_replacement.py -v

The expected paths and quantities are independently calculated from the
CSV graph, without using PartsCatalogue's intermediate results.
"""

import csv
import random
from collections import defaultdict

from app.catalogue import PartsCatalogue


def write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def test_30_independent_replacement_exports(tmp_path):
    root = "AS-40000"
    serials_to_check = (0, 100, 180, 200, 250, 400, 9999)
    range_options = (("", ""), ("100", "200"), ("200", "350"),
                     ("", "180"), ("180", ""))

    for seed in range(30):
        rng = random.Random(seed)
        folder = tmp_path / f"export_{seed}"
        folder.mkdir()
        parts = [root] + [f"PT-{i:04d}" for i in range(1, 10)]

        # Build a known acyclic graph with a guaranteed path to every part.
        edges = {}
        for i in range(len(parts) - 1):
            edges[(parts[i], parts[i + 1])] = rng.randint(1, 3)
        for i in range(len(parts)):
            for j in range(i + 2, len(parts)):
                if rng.random() < 0.25:
                    edges[(parts[i], parts[j])] = rng.randint(1, 3)

        bom_rows = []
        for (parent, child), quantity in edges.items():
            bom_rows.append([parent, child, quantity])
            if rng.random() < 0.35:
                bom_rows.append([f" {parent.lower()} ",
                                 f" {child.lower()} ", quantity])
        bom_rows.append(["OUT-1", "OUT-2", 2])
        rng.shuffle(bom_rows)
        write_csv(folder / "bom.csv",
                  ["parent_pn", "child_pn", "quantity"], bom_rows)

        master_rows = []
        missing = set()
        latest = {}
        for i, part in enumerate(parts):
            if i > 0 and rng.random() < 0.18:
                missing.add(part)
                continue
            revision = "B" if i % 3 == 0 else "A"
            latest[part] = revision
            master_rows.append([part, "A", f"{part}-A", "Component", "1"])
            if revision == "B":
                master_rows.append([part, "B", f"{part}-B", "Component", "2"])
        rng.shuffle(master_rows)
        write_csv(folder / "parts_master.csv",
                  ["part_number", "revision", "description", "category",
                   "unit_cost"], master_rows)

        service_rows = []
        service_by_part = defaultdict(list)
        for part in parts:
            permission = "N" if part == root else rng.choice(("Y", "Y", "N"))
            lower, upper = rng.choice(range_options)
            service_rows.append([part, permission, lower, upper])
            service_by_part[part].append((permission, lower, upper))
            if permission == "Y" and rng.random() < 0.30:
                service_rows.append([part, "Y", "250", "500"])
                service_by_part[part].append(("Y", "250", "500"))
        rng.shuffle(service_rows)
        write_csv(folder / "service_parts.csv",
                  ["part_number", "field_replaceable", "serial_from",
                   "serial_to"], service_rows)

        catalogue = PartsCatalogue(data_dir=folder)

        # Independent oracle: enumerate every root-to-part path, multiplying
        # edge quantities along each route. No reuse of catalogue graph data.
        expected = defaultdict(list)
        stack = [(root, [root], 1)]
        while stack:
            part, path, product = stack.pop()
            expected[part].append((path, product))
            for (parent, child), quantity in edges.items():
                if parent == part:
                    stack.append((child, path + [child], product * quantity))

        assert catalogue.parts == set(parts), f"seed={seed}: reachable parts"
        assert catalogue.outside_machine == ["OUT-1", "OUT-2"]

        statuses = {}
        for part in parts:
            if part in missing:
                status = "missing"
            elif any(flag == "Y" for flag, _, _ in service_by_part[part]):
                status = "ready"
            else:
                status = "not_replaceable"
            statuses[part] = status

            result = catalogue.get_part(part)
            assert result["status"] == status, (seed, part, "status")
            assert result["total_quantity"] == sum(q for _, q in expected[part]), (
                seed, part, "quantity")
            assert result["revision"] == latest.get(part), (
                seed, part, "revision")
            assert result["description"] == (
                f"{part}-{latest[part]}" if part in latest else None
            ), (seed, part, "description")
            assert result["parents"] == sorted(
                parent for (parent, child) in edges if child == part
            ), (seed, part, "parents")
            assert result["children"] == [
                {"part_number": child, "quantity": quantity}
                for (parent, child), quantity in sorted(edges.items())
                if parent == part
            ], (seed, part, "children")
            assert catalogue.get_paths(part)["paths"] == sorted(
                path for path, _ in expected[part]
            ), (seed, part, "paths")

        assert catalogue.validation() == {
            "parts": len(parts),
            "ready": sum(s == "ready" for s in statuses.values()),
            "missing": sum(s == "missing" for s in statuses.values()),
            "not_replaceable": sum(s == "not_replaceable" for s in statuses.values()),
        }, f"seed={seed}: validation"

        for serial in serials_to_check:
            applicable = 0
            for part, status in statuses.items():
                if status != "ready":
                    continue
                for flag, lower, upper in service_by_part[part]:
                    if flag != "Y":
                        continue
                    if ((not lower or serial >= int(lower))
                            and (not upper or serial <= int(upper))):
                        applicable += 1
                        break
            assert catalogue.applicable_parts(serial) == {
                "serial": serial, "applicable_parts": applicable
            }, (seed, serial, "serial applicability")
