import requests

# Buscar el partido Brasil vs Japón en la API directamente
response = requests.get(
    "https://api.football-data.org/v4/competitions/2000/matches",
    headers={"X-Auth-Token": "3a079af75a7d4acb9f0b64b15c7ff2d5"}
)
matches = response.json().get("matches", [])

for m in matches:
    home = m.get("homeTeam", {}).get("name", "")
    away = m.get("awayTeam", {}).get("name", "")
    if "Brazil" in [home, away] and "Japan" in [home, away]:
        print(f"{home} vs {away} — status: {m.get('status')}")