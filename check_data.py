
from app.data_loader import load_data

data = load_data()

print("=" * 45)
print("       BRUVITI DATA LOADING SUMMARY")
print("=" * 45)

for name, value in data["summary"].items():
    print(f"{name}: {value}")

print("\nROOT MASTER RECORD:")
print(data["master"].get("AS-40000"))

print("\nSERVICE RECORD EXAMPLE:")
print(data["service"].get("AS-40003"))

print("\nWARNINGS / CONFLICTS:")

for issue in data["problems"][:10]:
    print("-", issue)

print("Total warnings:", len(data["problems"]))
