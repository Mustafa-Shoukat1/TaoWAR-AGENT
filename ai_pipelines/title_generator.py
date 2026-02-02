from openai import OpenAI
from config import OPENAI_API_KEY
import json

def generate_daily_title_and_subtitle(report_content):
    """
    Generate title, subtitle, and description summary for daily report based on its content.
    Returns a dictionary with 'title', 'subtitle', and 'description_summary' keys.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""
You are an expert content strategist for digital asset market intelligence reports. 

Given the following daily report content, generate a compelling title and description summary:

TITLE Requirements:
- Captures the key themes and insights from the report
- Is suitable for a digital asset/cryptocurrency market intelligence publication
- Is concise but informative (ideally 5-12 words)
- Sounds professional and authoritative
- Avoids generic phrases like "Daily Report" or "Market Update"
- Focuses on the main trends, developments, or insights discussed

DESCRIPTION_SUMMARY Requirements:
- Provides a comprehensive overview of the report's key insights and findings
- Should be 2-4 sentences long
- Highlights the most important trends, developments, and analysis covered
- Written in a professional, informative tone
- Should entice readers to read the full report
- Can mention specific areas like regulations, technology, market movements, etc.
- Max 160 words
Report Content:
{report_content}...

Return your response as a JSON object with exactly this format:
{{
    "title": "Your generated title here",
    "description_summary": "Your generated description summary here, max 160 words are allowed"
}}

Do not include any other text, explanations, or formatting outside the JSON.
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert content strategist specializing in financial and digital asset market publications. Always respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=200,
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    try:
        result = json.loads(response.choices[0].message.content.strip())
        # Ensure we have both keys and clean them
        title = result.get("title", "Digital Asset Market Intelligence").strip('"\'')
        description_summary = result.get("description_summary", "Comprehensive analysis of daily digital asset market developments and trends.").strip('"\'')
        return {"title": title, "description_summary": description_summary}
    except json.JSONDecodeError:
        # Fallback in case of JSON parsing error
        return {
            "title": "Digital Asset Market Intelligence", 
            "description_summary": "Comprehensive analysis of daily digital asset market developments and trends."
        }

def generate_daily_title(report_content):
    """
    Generate a suitable title for daily report based on its content.
    Maintained for backward compatibility.
    """
    result = generate_daily_title_and_subtitle(report_content)
    return result["title"]

def generate_weekly_title_and_subtitle(report_content):
    """
    Generate title and description summary for weekly report based on its content.
    Returns a dictionary with 'title' and 'description_summary' keys.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""
You are an expert content strategist for digital asset market intelligence reports.

Given the following weekly report content, generate a compelling title and description summary:

TITLE Requirements:
- Captures the major weekly trends and developments
- Is suitable for a comprehensive weekly digital asset market roundup
- Is concise but informative (ideally 6-15 words)
- Sounds professional and authoritative
- Avoids generic phrases like "Weekly Report" or "Weekly Summary"
- Highlights the most significant themes or developments from the week

DESCRIPTION_SUMMARY Requirements:
- Provides a comprehensive overview of the week's key market developments and insights
- Should be 3-5 sentences long
- Highlights the most significant weekly trends, regulatory updates, technology advances, and market movements
- Written in a professional, authoritative tone suitable for institutional readers
- Should summarize the value and scope of the weekly analysis
- Can mention specific themes like DeFi, institutional adoption, regulatory changes, etc.
- Max 160 words
Report Content:
{report_content}...

Return your response as a JSON object with exactly this format:
{{
    "title": "Your generated title here",
    "description_summary": "Your generated description summary here, max 160 words are allowed"
}}

Do not include any other text, explanations, or formatting outside the JSON.
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert content strategist specializing in financial and digital asset market publications. Always respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=250,
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    try:
        result = json.loads(response.choices[0].message.content.strip())
        # Ensure we have both keys and clean them
        title = result.get("title", "Weekly Digital Asset Market Intelligence").strip('"\'')
        description_summary = result.get("description_summary", "Comprehensive weekly analysis of digital asset market trends, regulatory developments, and institutional movements shaping the cryptocurrency landscape.").strip('"\'')
        return {"title": title, "description_summary": description_summary}
    except json.JSONDecodeError:
        # Fallback in case of JSON parsing error
        return {
            "title": "Weekly Digital Asset Market Intelligence", 
            "description_summary": "Comprehensive weekly analysis of digital asset market trends, regulatory developments, and institutional movements shaping the cryptocurrency landscape."
        }

def generate_weekly_title(report_content):
    """
    Generate a suitable title for weekly report based on its content.
    Maintained for backward compatibility.
    """
    result = generate_weekly_title_and_subtitle(report_content)
    return result["title"]
