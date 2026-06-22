import os
import json
import requests

# 1. Fetch the raw live data from football-data.org
API_URL = "https://api.football-data.org/v4/competitions/WC/matches"

# Checks GitHub Secrets first. If testing locally, falls back to your token string automatically.
API_KEY = os.environ.get("FOOTBALL_API_KEY", "15e1eb6c1240450daad57212958ac59a")
HEADERS = {"X-Auth-Token": API_KEY}

print("🔄 Fetching latest tournament data from API...")
response = requests.get(API_URL, headers=HEADERS)

if response.status_code != 200:
    print(f"❌ Error fetching data: {response.status_code}")
    print(response.text)
    exit()

data = response.json()
matches_payload = []

# 2. Map the API payload exactly to your high-energy frontend format
for match in data.get("matches", []):
    home_name = match.get("homeTeam", {}).get("name", "TBD") if match.get("homeTeam") else "TBD"
    away_name = match.get("awayTeam", {}).get("name", "TBD") if match.get("awayTeam") else "TBD"

    # API returns None for scores if the match hasn't started, default to 0
    home_score = match.get("score", {}).get("fullTime", {}).get("home")
    away_score = match.get("score", {}).get("fullTime", {}).get("away")
    if home_score is None: home_score = 0
    if away_score is None: away_score = 0

    matches_payload.append({
        "id": match.get("id"),
        "stage": match.get("stage"),       # Matches 'LAST_32', 'ROUND_OF_16', 'QUARTER_FINALS', etc.
        "home": home_name,
        "away": away_name,
        "homeScore": home_score,
        "awayScore": away_score,
        "status": match.get("status"),     # Matches 'FINISHED', 'LIVE', 'TIMED'
        "time": "Live Match" if match.get("status") == "LIVE" else "Scheduled" if match.get("status") == "TIMED" else "Completed",
        "utcDate": match.get("utcDate")
    })

# 3. Read your visual HTML file, inject the clean data, and overwrite it
try:
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    start_marker = "// --- ROBOT LIVE DATA INSERTION POINT ---"
    end_marker = "// --- END ROBOT LIVE DATA ---"

    if start_marker in html_content and end_marker in html_content:
        split_start = html_content.split(start_marker)[0]
        split_end = html_content.split(end_marker)[1]

        # Format the JSON payload nicely to keep your template clean
        new_data_string = f"\n        const matches = {json.dumps(matches_payload, indent=12)};\n        "
        updated_html = split_start + start_marker + new_data_string + end_marker + split_end

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(updated_html)

        print(f"🏆 Tracker successfully updated with {len(matches_payload)} matches!")
    else:
        print("❌ Error: Could not find the ROBOT comment lines in your index.html file.")

except FileNotFoundError:
    print("❌ Error: index.html file not found in this directory.")
