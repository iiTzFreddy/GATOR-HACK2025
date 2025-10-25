from google import genai
client = genai.Client(api_key="AIzaSyBVzUjYRJj5URDaFHxT2jpa7ZGm7IUiYFE")
nums = [1,2,3,4,5,6]
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents= f"Only give the average of {nums}"
)

print(response.text)