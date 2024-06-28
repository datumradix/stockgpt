import os
import base64
from openai import OpenAI

OPENAI_API_KEY = ""
OPENAI_ORG_ID = ""

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

client = OpenAI(organization=OPENAI_ORG_ID)

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
  
def analyze_chart(chart_path):
    base64_image = encode_image(chart_path)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this chart. Include the symbol and discuss the price action."},
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                },
                },
            ],
            }
        ]
    )

    return response.choices[0].message.content
