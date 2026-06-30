import requests
r = requests.get("https://worldcup-economy-tracker.onrender.com/bracket", timeout=30)
import json
print(json.dumps(r.json(), indent=2, default=str))