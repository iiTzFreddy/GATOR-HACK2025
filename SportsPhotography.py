#Gemini API
from google import genai
#Pillow Libary
from PIL import Image
#NBA_API
import pandas as pd
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import teams, players
from nba_api.live.nba.endpoints import scoreboard
from nba_api.live.nba.endpoints import boxscore


#Get player from image
client = genai.Client(api_key="AIzaSyBVzUjYRJj5URDaFHxT2jpa7ZGm7IUiYFE")
img_path = r"C:\Users\Typic\Desktop\GATORHACK2025\basketball_player.png"
image = Image.open(img_path)
#Ask Gemini who the player is
PlayerResponse = client.models.generate_content(
    model='gemini-2.5-flash',
    contents= ["Only tell me who is in this image",image]
)
player = PlayerResponse.text
#Ask Gemini what TEAM player is on
TeamResponse = client.models.generate_content(
    model='gemini-2.5-flash',
    contents= [f"Only tell me the name of the team {player} plays for without the city"]
)
playerteam = TeamResponse.text

#Get player id from NBA API
nba_players = players.get_players()
for i in nba_players:
    if i['full_name'] == player:
        PLAYER_ID = i['id']
        break
#Get stats from NBA API
board = scoreboard.ScoreBoard()
board_data = board.get_dict()
games_list = board_data.get('scoreboard', {}).get('games', [])
#Get live player stats
    #Get NBA API Game ID
if not games_list:
    print("No games found for today.")
else:
    for game in games_list:
        home_team = game['homeTeam']['teamName']
        away_team = game['awayTeam']['teamName']
        if home_team == playerteam:
            GAME_ID = game['gameId']
            home_away = "home"
        elif away_team == playerteam:
            GAME_ID = game['gameId']
            home_away = "away"

    #Use boxscore
live_box = boxscore.BoxScore(game_id=GAME_ID)
box_data = live_box.get_dict()
GAME_ID = None
if home_away == "home":
    teamplayers = box_data['game']['homeTeam']['players']
elif home_away == "away":
    teamplayers = box_data['game']['awayTeam']['players']

player_stats_list=[]
for i in teamplayers:
    if i['name'] == player:
        player_stats_list.append({
            'NAME': i['name'],
            'MIN': i.get('statTotal', {}).get('minutes', 0),
            'PTS': i.get('statTotal', {}).get('points', 0),
            'REB': i.get('statTotal', {}).get('rebounds', 0),
            'AST': i.get('statTotal', {}).get('assists', 0),
            'FG_PCT': i.get('statTotal', {}).get('fgm', 0) / (i.get('statTotal', {}).get('fga', 1) or 1)
        })
#NBA SEASON JUST STARTED SO STATS FROM LATEST GAME FOR 25-26 SEASON ARE NOT UPDATED
CURRENT_SEASON = '2024-25'
gamelog = playergamelog.PlayerGameLog(
    player_id = PLAYER_ID, 
    season=CURRENT_SEASON
)
print(player_stats_list)
gamelog_df = gamelog.get_data_frames()[0]
latest_game_stats = gamelog_df.iloc[0]
stats_to_show = {
    'Date': latest_game_stats['GAME_DATE'],
    'Opponent': latest_game_stats['MATCHUP'],
    'Result (W/L)': latest_game_stats['WL'],
    'Minutes': latest_game_stats['MIN'],
    'Points': latest_game_stats['PTS'],
    'Rebounds': latest_game_stats['REB'],
    'Assists': latest_game_stats['AST'],
    'Steals': latest_game_stats['STL'],
    'Blocks': latest_game_stats['BLK'],
    'Turnovers': latest_game_stats['TOV']
}
for key, value in stats_to_show.items():
    print(f"{key.ljust(15)}: {value}")

print("Output:")
print(gamelog_df[['GAME_DATE', 'MATCHUP', 'PTS', 'AST', 'REB', 'WL']])
season_pts_avg = gamelog_df['PTS'].mean()
print(f"\n2023-24 Season Points Average: {season_pts_avg:.1f} PPG")