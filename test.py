import requests
r = requests.get("https://worldcup-economy-tracker.onrender.com/matches/live", timeout=15)
print(r.json())