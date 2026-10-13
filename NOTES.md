# Engineering Notes

## Design Decisions

**1. Rule-based reconciliation instead of machine learning**

The task defines explicit engineering rules, so deterministic algorithms are more suitable than predictive AI. This avoids model uncertainty, training overhead, external API dependencies, and unnecessary computational cost.

**2. Directed graph instead of a tree**

A part can appear in multiple assemblies. A directed graph preserves shared relationships and supports accurate quantities and all assembly paths.

**3. Preprocessing at startup**

CSV parsing, reconciliation, cycle handling, graph construction, quantity calculation, and status determination occur when the application starts. API requests reuse the processed catalogue, reducing repeated computation.

**4. Iterative DFS and topological processing**

Iterative DFS reconstructs the reachable graph and excludes back-edges. Topological processing propagates quantities through shared assemblies without repeatedly expanding every path.

**5. Deterministic conflict handling**

Normalized identifiers, sorted graph traversal, sorted API results, and explicit conflict-resolution rules reduce dependence on CSV row order.

**6. Simple frontend**

A lightweight HTML/CSS/JavaScript dashboard demonstrates the API without introducing an additional framework, build pipeline, or external dependency.

## Trade-offs and Limitations

- The application assumes the documented CSV schema and AM-700 root identifier.
- Ambiguous duplicate quantities and service permissions are handled using documented fallback rules.
- CSV changes require a service restart.
- Very large catalogues with exponentially many valid paths could increase path-response size.
- The system is read-only and does not include authentication, database persistence, or live inventory integrations.
- Offline operation requires dependencies to have been installed beforehand.

## Scope Decisions

Priority was given to exact endpoint contracts, data reconciliation, graph correctness, error handling, automated tests, and reproducible startup.

No LLM, neural network, GPU, external database, authentication system, or additional frontend framework was added because these were unnecessary for the required functionality.

## Future Improvements

- Structured machine-readable data-quality reports
- Configurable conflict-resolution policies
- Larger stress and performance test suites
- Versioned catalogue exports and audit trails
- Optional visual assembly-tree exploration

The core scope is implemented using a deliberately minimal and explainable architecture.
