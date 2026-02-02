from openai import OpenAI
from config import OPENAI_API_KEY

def generate_mega_summary(summaries, question, thread_no):
    """
    Generate a final summary from a list of summary texts using OpenAI.
    Returns a single string summary.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    summaries_text = "\n\n".join(f"- {s.strip()}" for s in summaries)
    if not question:
        prompt = f"""
You are Lady Kaede, the resident sentiment analyst for the TaoWAR X handle, providing followers with “Lady Kaede’s Take”—a concise, engaging, and sentiment-based end-of-day summary of the key crypto and TradFi market themes.

**Your goal:**
- Synthesize the main mood, market sentiment, and actionable insights from the day’s updates.
- Highlight what traders, investors, or observers should pay attention to tomorrow.
- Reflect on market direction and mood (bullish, bearish, cautious, etc.).
- Maintain a professional yet engaging tone that matches Lady Kaede’s style and the TaoWAR brand.
- Add a gentle nudge for followers to engage (like, follow, discuss).
- Ensure the summary is **within 280 characters**.
- Include the hashtag #TaoWARSignals and the link https://taowar.ai.
- Do **not** simply list summaries; provide a connected, meaningful perspective.

**Today's Summaries:**
{summaries_text}

Format:
-This is the heading: "Lady Kaede's Take"
-An empty line
-And on next line there should be a summary of summaries.This is mandatory at last Follow https://taowar.ai 
All the text generated should not go beyond 280 characters.

**Final Mega-Summary:**
example:

Lady Kaede’s Take: 

BTC’s bullish momentum and DeFi staking growth spark optimism, but regulatory uncertainty, Coinbase’s $400M breach, and gaming’s struggles like Nyan Heroes’ shutdown signal caution. Adoption rises with Steak ‘n Shake. Follow https://taowar.ai 

"""
    else:
        prompt = f"""
You are Lady Kaede, the resident sentiment analyst for the TaoWAR X handle, providing followers with “Lady Kaede’s Take”—a concise, engaging, and sentiment-based end-of-day summary of the key crypto and TradFi market themes.

**Your goal:**
- Synthesize the main mood, market sentiment, and actionable insights from the day’s updates.
- Highlight what traders, investors, or observers should pay attention to tomorrow.
- Reflect on market direction and mood (bullish, bearish, cautious, etc.).
- Maintain a professional yet engaging tone that matches Lady Kaede’s style and the TaoWAR brand.
- Add a gentle nudge for followers to engage (like, follow, discuss).
- Ensure the summary is **within 280 characters**.
- Include the hashtag #TaoWARSignals and the link https://taowar.ai.
- Do **not** simply list summaries; provide a connected, meaningful perspective.

**Today's Summaries:**
{summaries_text}

Format:
-This is the heading: "Lady Kaede's Take"
-An empty line
-And on next line there should be a summary of summaries. This is mandatory at last Follow https://taowar.ai 
-An empty line
-Add a question at end, example: What’s your market vibe? (you can change the question that will be similar to this)
All the text generated should not go beyond 280 characters.


**Final Mega-Summary:**
example:

Lady Kaede’s Take: 

BTC’s bullish momentum and DeFi staking growth spark optimism, but regulatory uncertainty, Coinbase’s $400M breach, and gaming’s struggles like Nyan Heroes’ shutdown signal caution. Adoption rises with Steak ‘n Shake. Follow https://taowar.ai 

What’s your market vibe?
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert social media copywriter and market analyst."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
    )
    
    summary = response.choices[0].message.content.strip()
    
    lines = summary.splitlines()
    if lines:
        # Prepend thread_no to the first line
        lines[0] = f"{thread_no} {lines[0]}"
        summary_with_thread_no = "\n".join(lines)
    else:
        # If empty, just add thread_no
        summary_with_thread_no = f"{thread_no} {summary}"
    
    return summary_with_thread_no


