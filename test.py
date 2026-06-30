import requests
import time

for i in range(5):
    r = requests.post("https://worldcup-economy-tracker.onrender.com/admin/sync", timeout=60)
    data = r.json()
    print(f"Sync {i+1}: {data.get('stocks_synced')} stocks, {data.get('events_synced')} eventos")
    if i < 4:
        time.sleep(60)