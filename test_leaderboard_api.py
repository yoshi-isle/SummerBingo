import requests
import json

# Test the new GET /teams endpoint
try:
    response = requests.get("http://localhost:5000/teams")
    if response.status_code == 200:
        teams = response.json()
        print(f"Found {len(teams)} teams:")
        for i, team in enumerate(teams):
            print(f"{i+1}. {team['team_name']} - Level {team.get('current_level', 'N/A')}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Connection error: {e}")
