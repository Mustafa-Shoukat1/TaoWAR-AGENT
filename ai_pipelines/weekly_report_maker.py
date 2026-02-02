import os
from typing import List
from openai import OpenAI
from langchain.prompts import PromptTemplate

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def weekly_report_prompt() -> str:
    return """
# One‑Category Weekly Summary Prompt  (150–200 words)

You are drafting **one section** of a weekly crypto/TradFi market report.  
Each call covers **one category only** (Market Trends, Regulation, DeFi, Stablecoins, Blockchain/AI, or Security).

## Output Structure  
1. **Single heading line** (no markdown symbols):  
   `{category}: A punchy title`  ← 1- max word hook capturing the week’s theme.  
2. Follow with ONE paragraph of narrative (new line).  
3. Finish like an expert analyst
4. No other headings, lists, tables, or code blocks.

## Content Rules  
- **Length:** Heading + paragraph + actionable line = 150–200 words total.  
- **Sources:** Draw exclusively from the supplied daily summaries and influencer names. Do **not invent** data.  
- **Citation Style:** Reference sources inline, e.g., “per CoinDesk (June 26 2025)”. Hyperlink influencer handles only if a URL is included in the input summaries.  
- **Verification:**  
  • If a fact is unconfirmed or conflicting, start with “Unconfirmed reports suggest…”.  
- **Narrative Focus:**  
  • Weave developments into a cohesive story showing interplay among institutional moves, trader behaviour, and geopolitics.  
  • Integrate influencer mentions naturally.  
  • Avoid repeating specific data points from the daily summaries (prices, percentages, etc.).  
  • Every sentence must add a fresh angle—no redundancy.  
- **Tone:** Conversational yet authoritative, vivid active verbs (“funds rotated”, “miners dumped”) and **exclude** clichés:  
  *cautiously optimistic, points towards, convergence of factors, market dynamics, suggests a potential, in the coming weeks, broader implications, underscores the importance of, evidenced by, significant momentum.*

## Hyperlinks
- Hyperlinks or refrences are a must to as which are given in the content provieded.
- You may use them in generating the content.
- If no hyperlinks are provided, do not add any.
- You must use them correctly in the content.

==================================================
🔗  LINK & ATTRIBUTION RULES
==================================================
• Every material claim must cite an *exact* source from the posts.  
• Embed links naturally on the noun/phrase (e.g. “BlackRock’s [ETF inflows](link)”).  
• Always name the author/handle in the sentence.  
• Use **only** the links provided; never invent new ones.
• Using links are must, use from the links provided in the posts.  
• No bare URLs, “click here”, or “this post” phrasing.

## Inputs  
- Category: {category}  
- Summaries: {summaries}   ← bullet‑joined daily summaries for the category  
- Influencers: {influencers} ← comma‑separated handles/names

## Expected Template  

{category}: A punchy title summarising the week’s theme (1 to max 5 words)
<~150‑180 word synthesis paragraph referencing sources and influencers, no extra headings.> 
"""


def format_weekly_report_prompt(category: str, summaries: List[str], influencers: List[str]) -> str:
    template = weekly_report_prompt()
    formatted_summaries = "\n\n".join(
        f"- {s}" for s in summaries if s
    )
    formatted_influencers = ", ".join(influencers) if influencers else "None"

    prompt = PromptTemplate(
        template=template,
        input_variables=["category", "summaries", "influencers"],
    )
    prompt_text = prompt.format(
        category=category,
        summaries=formatted_summaries,
        influencers=formatted_influencers,
    )
    return prompt_text

def generate_weekly_summary(category: str, summaries: List[str], influencers: List[str]) -> str:
    prompt_text = format_weekly_report_prompt(category, summaries, influencers)
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()
