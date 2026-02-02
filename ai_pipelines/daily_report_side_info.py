from openai import OpenAI
from config import OPENAI_API_KEY
import json

def generate_info():

    client = OpenAI(api_key=OPENAI_API_KEY)
    # Prepare the prompt
    prompt = f"""
You are an expert financial copywriter specializing in digital assets and cryptocurrency markets.

**Task Overview:**
Given the following post text, your tasks are:
1. Generate a concise, engaging, and informative report title. Your title should reflect the tone and breadth of these examples, but you can be creative:
   - Crypto & Macro Markets: Weekly Trends, Insights, and Strategic Outlook
   - State of Crypto & Global Markets – Analysis, Regulation, Adoption & Trends
   - Digital Asset Market Intelligence: Trends, Policy, Security, and Innovation
   - The Evolving Crypto Economy: Market Trends, Regulation, and Technology Update
   - Crypto & Finance 2025: Markets, Policy, Adoption, and DeFi Developments

2. Rephrase the provided introduction and disclaimer for clarity, conciseness, and a professional tone. Ensure both outputs are easy to read and suitable for a market report.

3. Format your output in valid JSON with the following keys:
- "title": (The new report title, in markdown format)
- "Introduction": (Rephrased introduction in markdown format)
- "Disclaimer": (Rephrased disclaimer in markdown format)

**Input for Rephrasing:**

Introduction:
"Digital Asset Market Intelligence" provides a comprehensive overview of the latest developments in the cryptocurrency and blockchain space. Compiled through extensive analysis of insights from 50 influential voices across social media and industry platforms, this report captures key trends, regulatory updates, security challenges, and technological advancements shaping the digital asset ecosystem. Designed to inform stakeholders, this report synthesizes diverse perspectives to offer actionable insights into the rapidly evolving market.

Disclaimer:
The information provided in this report is for informational purposes only and does not constitute financial, investment, or legal advice. Readers are strongly encouraged to conduct their own research and consult with qualified professionals before making any investment or financial decisions. The insights and data presented are based on publicly available information from influencers and sources, which may not be exhaustive or error-free. Neither the authors nor the publishers accept liability for any losses or damages arising from the use of this report.

**Your Response (JSON only):**

{{
    "title": "The title of the report in markdown format",
    "Introduction": "Rephrase the introduction given but give In markdown format",
    "Disclaimer": "Rephrase the Disclaimer given but give In markdown format"
}}
    """
    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": "You are an expert social media copywriter."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        response_format={"type": "json_object"}
    )
    # Extract and parse JSON
    json_text = response.choices[0].message.content.strip()
    data = json.loads(json_text)
    # Return all three fields
    return data["title"], data["Introduction"], data["Disclaimer"]
