#VEO 3 video

#Imports
import json
import time
import pandas as pd
from google import genai
from google.genai import types
from nba_api.stats.endpoints import playergamelog, playercareerstats
my_API_Key = "AIzaSyD-jnak65x-Wva2PdSVWCx9Vf3dJLjZjS8"
#Initialize Gemini Client
client = genai.Client(api_key= my_API_Key)

#Load data exported by the first program
with open("player_output.json", "r") as f:
    data = json.load(f)

player = data["player"]
PLAYER_ID = data["PLAYER_ID"]
CURRENT_SEASON = data["CURRENT_SEASON"]
latest_game_stats_dict = data["latest_game_stats"] 
career_stats_dict = data["career_stats"] 
latest_game_stats = pd.Series(latest_game_stats_dict)
career_row = pd.Series(career_stats_dict)

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
VEO_MODEL = 'veo-3.1-fast-generate-preview'
veo_prompt = prompt_response.text
OUTPUT_FILENAME = "generate_veo_video.mp4"

print("\n--- Generated Veo Prompt ---")
print(veo_prompt)

try:
    client = genai.Client(api_key= my_API_Key)
except Exception as e:
    print("Error initializing client. Is GEMINI_API_KEY environment variable set?")
    print(e)
    exit()
print(f"Starting video generation with model: {VEO_MODEL}")
print(f"Prompt: {veo_prompt}\n")
try:
    operation = client.models.generate_videos(
        model=VEO_MODEL,
        prompt=veo_prompt,
        config=types.GenerateVideosConfig(
            aspect_ratio="16:9",
            duration_seconds=8
        )
    )
    print(f"Video generation operation started: {operation.name}")
    print("Waiting for video to be ready...")
    while not operation.done:
        time.sleep(15)  # Wait for 15 seconds before checking again
        operation = client.operations.get(operation)
        print(f"Status: {operation.metadata.state.name}")
    print("\n--- Generation Complete! ---")
    if operation.response and operation.response.generated_videos:
        generated_video = operation.response.generated_videos[0]
        
        video_file = generated_video.video

        video_file.save(OUTPUT_FILENAME)
        
        print(f"Successfully saved video to: {OUTPUT_FILENAME}")
    else:
        print("Error: Operation completed but no video was returned.")
        print(f"Final status: {operation.error}")

except Exception as e:
    print(f"An error occurred during video generation: {e}")

