import requests
import json
import os

HTML_FILE_PATH = "index.html"
# ESPN's direct public world cup scoreboard endpoint
URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

def map_stage(round_name):
    """Maps ESPN's round text to your bracket columns."""
    r = round_name.upper()
    if "GROUP" in r: return "GROUP_STAGE"
    if "ROUND OF 32" in r or "L32" in r or "ROUND_32" in r: return "LAST_32"
    if "ROUND OF 16" in r or "L16" in r or "ROUND_16" in r: return "LAST_16"
    if "QUARTER" in r: return "QUARTER_FINALS"
    if "SEMI" in r: return "SEMI_FINALS"
    if "FINAL" in r: return "FINAL"
    return "GROUP_STAGE"

def fetch_espn_data():
    try:
        response = requests.get(URL)
        if response.status_code != 200: 
            print(f"ESPN API returned status code {response.status_code}")
            return []
        
        data = response.json()
        events = data.get("events", [])
        parsed_matches = []
        
        print(f"Found {len(events)} games on ESPN scoreboard today.")
        
        for event in events:
            match_id = event.get("id")
            raw_stage = event.get("status", {}).get("type", {}).get("detail", "Group Stage")
            stage = map_stage(raw_stage)
            utc_date = event.get("date")
            
            status_type = event.get("status", {}).get("type", {}).get("name", "")
            if status_type == "STATUS_IN_PROGRESS":
                status = "LIVE"
                time_display = f"Live - {event.get('status', {}).get('displayClock', '')}"
            elif status_type == "STATUS_FINAL":
                status = "FINISHED"
                time_display = "Completed"
            else:
                status = "TIMED"
                time_display = "Scheduled"
                
            competitions = event.get("competitions", [{}])
            competitors = competitions[0].get("competitors", []) if competitions else []
            
            home_team = next((c for c in competitors if c.get("homeAway") == "home"), {})
            away_team = next((c for c in competitors if c.get("homeAway") == "away"), {})
            
            home_name = home_team.get("team", {}).get("name", "TBD")
            away_name = away_team.get("team", {}).get("name", "TBD")
            
            home_score = int(home_team.get("score", 0))
            away_score = int(away_team.get("score", 0))
            
            parsed_matches.append({
                "id": match_id,
                "stage": stage,
                "home": home_name,
                "away": away_name,
                "homeScore": home_score,
                "awayScore": away_score,
                "status": status,
                "time": time_display,
                "utcDate": utc_date
            })
        return parsed_matches
    except Exception as e:
        print(f"Error reading from ESPN: {e}")
        return []

def inject_into_html(matches_list):
    if not os.path.exists(HTML_FILE_PATH):
        print("Error: index.html not found.")
        return
    if not matches_list:
        print("No matches parsed. Skipping update to avoid overwriting with blank data.")
        return
        
    with open(HTML_FILE_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    injection_payload = f"const matches = {json.dumps(matches_list, indent=12)};"
    start_marker = "// --- ROBOT LIVE DATA INSERTION POINT ---"
    end_marker = "// --- END ROBOT LIVE DATA ---"
    
    if start_marker in html_content and end_marker in html_content:
        parts = html_content.split(start_marker)
        remainder = parts[1].split(end_marker)
        updated_html = parts[0] + start_marker + "\n            " + injection_payload + "\n        " + end_marker + remainder[1]
        
        with open(HTML_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(updated_html)
        print("Success! index.html updated with ESPN data.")
    else:
        print("Error: Could not find the comment markers in index.html.")

if __name__ == "__main__":
    matches_data = fetch_espn_data()
    inject_into_html(matches_data)
