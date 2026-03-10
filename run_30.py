import json
import os

with open("completion_benchmark.json", "r") as f:
    data = json.load(f)

data = [d for d in data if d["problem"] != "Prob030_popcount255"]

with open("completion_benchmark.json", "w") as f:
    json.dump(data, f, indent=2)
