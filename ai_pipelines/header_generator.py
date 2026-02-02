from openai import OpenAI
from config import OPENAI_API_KEY

def generate_header(post_text):
    """
    Send the post_text to OpenAI GPT-3.5/4 and return the formatted response.
    """
    client = OpenAI(api_key = OPENAI_API_KEY)
    # Example prompt - customize as needed
    prompt = f"""
You are a social media expert. Given the following post, provide a catchy, engaging summary
for followers, formatted for Twitter. Keep it professional and insightful.
The generated post must be withing 280 characters.
You just have to rephrase the post keeping the tone and logical things same.
The link https://taowar.ai and hasttags should also be same.
Post:\n{post_text}\n\n

The post should be formated as follows:
-The heading
-An empty line
-The post text

example:
Heading

post text
    """
    
    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": "You are an expert social media copywriter."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=120,
        temperature=0.7,
    )
    # Extract response text
    result = response.choices[0].message.content.strip()
    return result
