#Gemini API
from google import genai
#Pillow Libary
from PIL import Image

client = genai.Client(api_key="AIzaSyBVzUjYRJj5URDaFHxT2jpa7ZGm7IUiYFE")


img_path = r"C:\Users\Typic\Desktop\GATORHACK2025\basketball_player.png"
img = Image.open(img_path)
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents= [f"Only tell my who is in this image",img]
)
print("Response:")
print(response.text)