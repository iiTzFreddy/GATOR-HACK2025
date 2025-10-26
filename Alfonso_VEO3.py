#VEO 3 video

#Imports
import json
import time
import pandas as pd
from google import genai
from nba_api.stats.endpoints import playergamelog, playercareerstats

#Initialize Gemini Client
client = genai.Client(api_key="AIzaSyBVzUjYRJj5URDaFHxT2jpa7ZGm7IUiYFE")

#Load data exported by the first program
with open("player_output.json", "r") as f:
    data = json.load(f)

player = data["player"]
PLAYER_ID = data["PLAYER_ID"]
CURRENT_SEASON = data["CURRENT_SEASON"]
latest_game_stats = pd.Series(data["latest_game_stats"])
career_row = pd.Series(data["career_row"])
print(f"--- Loaded data for {player} ---")

#Compare Last Game vs Career Averages
stat_labels = {
    "PTS": "Points",
    "REB": "Rebounds",
    "AST": "Assists",
    "FG_PCT": "Field Goal Percentage",
    "FG3_PCT": "Three-Point Percentage",
    "FT_PCT": "Free-Throw Percentage",
}

differences = {}
for key in stat_labels.keys():
    if key in latest_game_stats and key in career_row:
        game_val = latest_game_stats[key]
        career_val = career_row[key]
        differences[key] = game_val - career_val

# Find the stat with the highest absolute variance
highest_var_stat = max(differences, key=lambda x: abs(differences[x]))
difference_value = differences[highest_var_stat]

print("\n--- Performance Analysis ---")
print(f"Statistic with highest variance: {stat_labels[highest_var_stat]}")
print(f"Last Game:  {latest_game_stats[highest_var_stat]:.2f}")
print(f"Career Avg: {career_row[highest_var_stat]:.2f}")
print(f"Difference: {difference_value:+.2f}")

#Build Video Prompt
if difference_value > 0:
    tone = "positive"
    performance_phrase = (
        f"show {player} excelling at their {stat_labels[highest_var_stat].lower()}, "
        "capturing the energy and excitement of peak performance."
    )
else:
    tone = "negative"
    performance_phrase = (
        f"show {player} struggling with their {stat_labels[highest_var_stat].lower()}, "
        "using somber lighting and reflective pacing to convey a tough game.")

#Ask Gemini to write the VEO prompt
prompt_response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        f"Write a short cinematic description for Gemini Veo. "
        f"It should {performance_phrase} Include camera direction, mood, and emotion. "
        f"Output only the text that should be used as the Veo video prompt."
    ],
)

veo_prompt = prompt_response.text

print("\n--- Generated Veo Prompt ---")
print(veo_prompt)

#Generate video with Gemini Veo
try:
    veo_video = client.models.generate_content(
        model="gemini-veo",
        contents=[veo_prompt],
        generation_config={"output_type": "video", "duration": "10s"},
    )

    # hypothetical field holding the video bytes
    video_bytes = veo_video.video
    video_path = f"{player.replace(' ', '_')}_highlight.mp4"
    with open(video_path, "wb") as f:
        f.write(video_bytes)

    print(f"\nVideo saved as {video_path}")

except Exception as e:
    print(
        "\n[Note] Veo video generation placeholder — replace with official Veo SDK call when available."
    )
    print(f"Error: {e}")