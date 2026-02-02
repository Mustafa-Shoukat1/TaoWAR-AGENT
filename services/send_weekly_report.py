import requests
from utils.logger import logger

def send_weekly_report(
    title: str,
    content: str,
    influencer_stats: list,
    generated_by: str = "weekly_ai",
    description_summary: str = "",
    api_key: str = "7febb13aee3d64c20ecd7d1d312cd24c7446e144bd594c1f858d465d9a40dfa3"
) -> dict:
    """
    Send the weekly report to the TaoWAR backend weekly/internal endpoint.
    Returns the response as a dict.
    Raises requests.HTTPError if the API call fails.
    """
    url = "https://tao-war-backend.onrender.com/weekly/internal"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "title": title,
        "content": content,
        "generatedBy": generated_by,
        "influencerStats": influencer_stats,
        "descriptionSummary": description_summary
    }
    response = requests.post(url, json=payload, headers=headers, timeout=50)
    try:
        response.raise_for_status()  # Will raise an error for 4xx/5xx
    except Exception as e:
        logger.error(f"Got error in sending report function: {e}")
    return response.json()


