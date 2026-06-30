import requests
r = requests.get("https://worldcup-economy-tracker.onrender.com/health", timeout=15)
print(r.json())