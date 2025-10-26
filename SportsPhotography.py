#Program only works if player has recently played a game
# Gemini API
from google import genai
# Pillow Libary
from PIL import Image
# NBA_API
import time
import pandas as pd
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import teams, players
from nba_api.live.nba.endpoints import scoreboard
from nba_api.live.nba.endpoints import boxscore
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.endpoints import commonplayerinfo

client = genai.Client(api_key="AIzaSyA_UfVo8a95_t3gF38hkzg5F-thuCRws0o") 
img_path = r"C:\Users\Typic\Desktop\GATORHACK2025\test.webp"
CURRENT_SEASON = '2025-26'
PLAYER_ID = None

print("--- Player Identification ---")
try:
    image = Image.open(img_path)
    # Ask Gemini who the player is
    PlayerResponse = client.models.generate_content(
        model='gemini-2.5-flash',
        contents= ["Only tell me who is the subject in this image",image]
    )
    player = PlayerResponse.text
except Exception as e:
    print(f"Error calling Gemini API or opening image: {e}")
    exit()

# Get player id from NBA API
nba_players = players.get_players()
for i in nba_players:
    if i['full_name'] == player:
        PLAYER_ID = i['id']
        break

if PLAYER_ID is None:
    print(f"Error: Player '{player}' not found in NBA database.")
    exit() 
print(f"Player Name: {player}")
print(f"Player ID: {PLAYER_ID}")


# Find TEAM player is on
player_info = commonplayerinfo.CommonPlayerInfo(player_id=PLAYER_ID)
time.sleep(0.5)
player_dict = player_info.get_normalized_dict()
player_team = {}
if 'CommonPlayerInfo' in player_dict and player_dict['CommonPlayerInfo']:
    info = player_dict['CommonPlayerInfo'][0]
    team_id = info.get('TEAM_ID')
    team_name = info.get('TEAM_NAME')
    
    if team_id is None or team_id == 0:
        print("Player is currently not on an active roster.") 
    
    player_team = {
        'team_id': team_id,
        'team_name': team_name,
    }

print(f"Player Team: {player_team['team_name']} (ID: {player_team['team_id']})")

# --- GET LATEST GAME STATS ---
print("\n--- Last Game Stats ---")
gamelog = playergamelog.PlayerGameLog(
    player_id = PLAYER_ID, 
    season=CURRENT_SEASON
)
time.sleep(0.5) 
gamelog_df = gamelog.get_data_frames()[0]

if gamelog_df.empty:
    print(f"No game logs found for the {CURRENT_SEASON} season.")
else:
    latest_game_stats = gamelog_df.iloc[0]
    game_stats = {
        'Date': latest_game_stats['GAME_DATE'],
        'Opponent': latest_game_stats['MATCHUP'],
        'Result (W/L)': latest_game_stats['WL'],
        'Minutes': latest_game_stats['MIN'],
        'Points': latest_game_stats['PTS'],
        'Rebounds': latest_game_stats['REB'],
        'Assists': latest_game_stats['AST'],
    }



    for key, value in game_stats.items():
        print(f"{key}: {value}")


# --- GET CAREER STATS---
print("\n--- Career Averages ---")

career_stats = playercareerstats.PlayerCareerStats(player_id=PLAYER_ID, per_mode36='PerGame')
time.sleep(0.5) 
career_df = career_stats.get_data_frames()[0]

career_stats_dict = {}

career_rows = career_df[career_df['SEASON_ID'] == 'Career']

if not career_rows.empty:
    career_row = career_rows.iloc[0]
    career_stats_dict = {
        'PTS': career_row['PTS'],
        'AST': career_row['AST'],
        'REB': career_row['REB'],
        'FG_PCT': career_row['FG_PCT'],
        'FG3_PCT': career_row['FG3_PCT'],
        'FT_PCT': career_row['FT_PCT'],
    }
    source = "Official Career Row"
else:
    season_df = career_df[career_df['SEASON_ID'] != 'Career'] 
    
    if season_df.empty:
        print("Error: Could not retrieve any career season data.")
        exit()
    career_stats_dict["PTS"] = season_df['PTS'].mean()
    career_stats_dict["AST"] = season_df['AST'].mean()
    career_stats_dict["REB"] = season_df['REB'].mean()
    career_stats_dict["FG_PCT"] = season_df['FG_PCT'].mean()
    career_stats_dict["FG3_PCT"] = season_df['FG3_PCT'].mean()
    career_stats_dict["FT_PCT"] = season_df['FT_PCT'].mean()
    
    source = "Calculated Average of Seasons"

print(f"Source: {source}")
print(f"Avg Career Stats for {player}:")
print(f"Points: {career_stats_dict['PTS']:.2f}")
print(f"Assists: {career_stats_dict['AST']:.2f}")
print(f"Rebounds: {career_stats_dict['REB']:.2f}")
print(f"Feild Goal %: {career_stats_dict['FG_PCT']:.3f}")
print(f"Three %: {career_stats_dict['FG3_PCT']:.3f}")
print(f"Free throw %: {career_stats_dict['FT_PCT']:.3f}")

#Storing Player stats for video file
import json

STAT_KEYS = ['PTS', 'REB', 'AST', 'FG_PCT', 'FG3_PCT', 'FT_PCT']


game_stats_json = {
    'Date': latest_game_stats['GAME_DATE'],
    'Opponent': latest_game_stats['MATCHUP'],
    'Result (W/L)': latest_game_stats['WL'],
    'MIN': int(latest_game_stats['MIN']), 
}

for key in STAT_KEYS:
    if key in ['PTS', 'REB', 'AST']:
        game_stats_json[key] = int(latest_game_stats[key])
    else:
        game_stats_json[key] = float(latest_game_stats[key])


output_data = {
    "player": player,
    "PLAYER_ID": PLAYER_ID,
    "CURRENT_SEASON": CURRENT_SEASON,
    "team": player_team,
    "latest_game_stats": game_stats_json, 
    "career_stats": career_stats_dict 
}

with open("player_output.json", "w") as f:
    json.dump(output_data, f, indent=4)

caption = client.models.generate_content(
        model='gemini-2.5-flash',
        contents= [f"Write a paragragh in the form of an instagram caption about what is going on in this image and comparing {career_stats_dict} to {game_stats} ",image]
    )
import sys
try:
    print(caption.text)
except UnicodeEncodeError:
    print(caption.text.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))