
from app.catalogue import PartsCatalogue

catalogue = PartsCatalogue()

print("=" * 50)
print("       BRUVITI MACHINE CATALOGUE TEST")
print("=" * 50)

# Test 1: Machine validation
print("\n1. VALIDATION")
print(catalogue.validation())

# Test 2: Cycles
print("\n2. REMOVED CYCLE RELATIONSHIPS")
print(catalogue.removed_cycle_edges)

# Test 3: Parts outside the machine
print("\n3. PARTS OUTSIDE MACHINE")
print(catalogue.outside_machine)

# Test 4: Root machine
print("\n4. ROOT MACHINE")
root = catalogue.get_part("AS-40000")
print("Description:", root["description"])
print("Quantity:", root["total_quantity"])
print("Children:", len(root["children"]))

# Test 5: Assembly part
print("\n5. AS-40003 DETAILS")
part = catalogue.get_part("AS-40003")
print("Status:", part["status"])
print("Quantity:", part["total_quantity"])
print("Parents:", part["parents"])

# Test 6: Part used in multiple assemblies
print("\n6. FA-30019")
part = catalogue.get_part("fa-30019")
print("Status:", part["status"])
print("Total quantity:", part["total_quantity"])

# Test 7: Paths
print("\n7. FA-30012 PATHS")
result = catalogue.get_paths("FA-30012")
print("Number of paths:", len(result["paths"]))
print("First path:", result["paths"][0])

# Test 8: Serial number
print("\n8. SERIAL COMPATIBILITY")
print(catalogue.applicable_parts(2500))

# Test 9: Missing part handling
print("\n9. UNKNOWN PART")
try:
    catalogue.get_part("UNKNOWN-999")
except KeyError as exc:
    print("Correctly rejected:", exc)

print("\nCATALOGUE CHECK FINISHED")
