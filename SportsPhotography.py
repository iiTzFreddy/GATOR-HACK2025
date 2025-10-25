#Gemini API
from google import genai
#Pillow Libary
from PIL import Image
#NBA_API
import pandas as pd
from nba_api.stats.endpoints import playergamelog, teamdetails, leaguegamelog
from nba_api.stats.static import teams, players


#Get player from image
client = genai.Client(api_key="AIzaSyBVzUjYRJj5URDaFHxT2jpa7ZGm7IUiYFE")
img_path = r"C:\Users\Typic\Desktop\GATORHACK2025\basketball_player.png"
img = Image.open(img_path)
#Ask Gemini who the player is
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents= [f"Only tell my who is in this image",img]
)
player = response.text
#Get player id from NBA API
nba_players = players.get_players()
for i in nba_players:
    if i['full_name'] == player:
        player_id = i['id']
        break
#Get player stats from NBA API
gamelog = playergamelog.PlayerGameLog(
    player_id,
    season = '2024-25'
)
gamelog_df = gamelog.get_data_frames()[0]

print("Output:")
print(gamelog_df[['GAME_DATE', 'MATCHUP', 'PTS', 'AST', 'REB', 'WL']])
season_pts_avg = gamelog_df['PTS'].mean()
print(f"\n2023-24 Season Points Average: {season_pts_avg:.1f} PPG")