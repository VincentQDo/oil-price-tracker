import json
from collections import defaultdict

# Optional: list of broken suppliers to skip
BROKEN_SUPPLIERS = {"Broken Supplier Inc"}  # replace with actual names

# Load your sorted JSON file
with open("data_clean.json") as f:
    data = json.load(f)

# Group by supplier
suppliers = defaultdict(list)
for row in data:
    supplier = row["supplier_name"]
    if supplier in BROKEN_SUPPLIERS:
        continue  # skip broken supplier
    suppliers[supplier].append(row)

# Save each supplier to its own file
for supplier, items in suppliers.items():
    # Make filename safe
    filename = supplier.replace(" ", "_").replace("/", "_") + ".json"
    with open(filename, "w") as f:
        json.dump(items, f, indent=2)
    print(f"Saved {len(items)} records to {filename}")
