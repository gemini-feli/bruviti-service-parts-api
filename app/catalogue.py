
"""Machine graph and service parts catalogue engine."""

from collections import Counter, defaultdict
import heapq

from .data_loader import load_data, normalize_part_number


class PartsCatalogue:
    ROOT = "AS-40000"

    def __init__(self, data_dir=None, root=None):
        data = load_data(data_dir)

        self.root = normalize_part_number(root or self.ROOT)
        self.master = data["master"]
        self.service = data["service"]
        self.data_summary = data["summary"]
        self.data_problems = data["problems"]

        # Build the raw parent -> child relationships.
        raw_graph = defaultdict(dict)

        for (parent, child), quantity in data["bom"].items():
            raw_graph[parent][child] = quantity

        self.graph = {}
        self.parts = set()
        self.removed_cycle_edges = []

        self._build_graph(raw_graph)

        # Identify BOM parts not belonging to the machine.
        all_bom_parts = {
            part
            for parent, child in data["bom"]
            for part in (parent, child)
        }

        self.outside_machine = sorted(
            all_bom_parts - self.parts
        )

        # Build reverse relationships: child -> parents.
        self.parents = defaultdict(set)

        for parent, children in self.graph.items():
            for child in children:
                self.parents[child].add(parent)

        self.total_quantities = self._calculate_quantities()

        # Cache statuses because they do not change at request time.
        self.statuses = {
            part: self._determine_status(part)
            for part in self.parts
        }

    def _build_graph(self, raw_graph):
        """
        Traverse from the machine root using DFS.

        Remove edges pointing to an active ancestor.
        Such edges create cycles in the machine structure.
        """

        self.parts.add(self.root)
        self.graph[self.root] = {}

        # State 1 = currently being explored.
        # State 2 = completely explored.
        state = {self.root: 1}

        stack = [
            (
                self.root,
                iter(sorted(raw_graph.get(self.root, {}).items()))
            )
        ]

        while stack:
            parent, children_iterator = stack[-1]

            try:
                child, quantity = next(children_iterator)

            except StopIteration:
                state[parent] = 2
                stack.pop()
                continue

            # The child is already an ancestor on the DFS path.
            if state.get(child) == 1:
                self.removed_cycle_edges.append(
                    (parent, child, quantity)
                )
                continue

            # Retain the valid relationship.
            self.graph[parent][child] = quantity

            # Explore a child only on its first visit.
            if child not in state:
                state[child] = 1
                self.parts.add(child)
                self.graph[child] = {}

                stack.append(
                    (
                        child,
                        iter(sorted(raw_graph.get(child, {}).items()))
                    )
                )

    def _calculate_quantities(self):
        """
        Calculate quantities using topological ordering.

        If parent P appears N times and contains Q units
        of child C, add N * Q to C's total.
        """

        indegree = {part: 0 for part in self.parts}

        for children in self.graph.values():
            for child in children:
                indegree[child] += 1

        # A heap gives deterministic processing order.
        queue = [
            part
            for part, degree in indegree.items()
            if degree == 0
        ]

        heapq.heapify(queue)

        totals = {part: 0 for part in self.parts}
        totals[self.root] = 1

        processed = 0

        while queue:
            parent = heapq.heappop(queue)
            processed += 1

            for child, quantity in self.graph[parent].items():
                totals[child] += totals[parent] * quantity

                indegree[child] -= 1

                if indegree[child] == 0:
                    heapq.heappush(queue, child)

        if processed != len(self.parts):
            raise ValueError(
                "Machine graph still contains a cycle"
            )

        return totals

    def _determine_status(self, part):
        """Determine the part's catalogue status."""

        if part not in self.master:
            return "missing"

        records = self.service.get(part, [])

        if any(
            row["field_replaceable"] == "Y"
            for row in records
        ):
            return "ready"

        return "not_replaceable"

    def _require_part(self, part_number):
        """Find a machine part, ignoring input capitalization."""

        part = normalize_part_number(part_number)

        if part not in self.parts:
            raise KeyError(f"Part not in machine: {part}")

        return part

    def validation(self):
        """Return the catalogue validation counts."""

        counts = Counter(self.statuses.values())

        return {
            "parts": len(self.parts),
            "ready": counts["ready"],
            "missing": counts["missing"],
            "not_replaceable": counts["not_replaceable"]
        }

    def get_part(self, part_number):
        """Return details for a part belonging to the machine."""

        part = self._require_part(part_number)
        master_record = self.master.get(part)

        children = [
            {
                "part_number": child,
                "quantity": quantity
            }
            for child, quantity in sorted(
                self.graph[part].items()
            )
        ]

        return {
            "part_number": part,
            "description": (
                master_record["description"]
                if master_record else None
            ),
            "revision": (
                master_record["revision"]
                if master_record else None
            ),
            "status": self.statuses[part],
            "total_quantity": self.total_quantities[part],
            "parents": sorted(self.parents[part]),
            "children": children
        }

    def get_paths(self, part_number):
        """
        Find every path from the machine root to a part.

        Traverse backwards through the parent relationships.
        """

        part = self._require_part(part_number)
        paths = []

        # Each item stores a node and the path to the target.
        stack = [(part, (part,))]

        while stack:
            current, path = stack.pop()

            if current == self.root:
                paths.append(list(path))
                continue

            for parent in self.parents[current]:
                stack.append(
                    (parent, (parent,) + path)
                )

        paths.sort()

        return {
            "part_number": part,
            "paths": paths
        }

    def applicable_parts(self, serial):
        """
        Count unique ready parts compatible with a serial.

        Serial boundaries are inclusive.
        A missing boundary is treated as unbounded.
        """

        if isinstance(serial, bool) or not isinstance(serial, int):
            raise ValueError("Serial must be a whole number")

        count = 0

        for part in self.parts:
            if self.statuses[part] != "ready":
                continue

            records = self.service.get(part, [])

            for record in records:
                if record["field_replaceable"] != "Y":
                    continue

                lower = record["serial_from"]
                upper = record["serial_to"]

                lower_ok = lower is None or serial >= lower
                upper_ok = upper is None or serial <= upper

                if lower_ok and upper_ok:
                    count += 1
                    break

        return {
            "serial": serial,
            "applicable_parts": count
        }
