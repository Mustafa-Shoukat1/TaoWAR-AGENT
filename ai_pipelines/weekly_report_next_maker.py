"""
weekly_report_next_maker.py
Generate the closing “What to Watch Next” section for the weekly report.
"""

import os
from typing import List
from random import sample
from openai import OpenAI
from langchain.prompts import PromptTemplate

# Initialise OpenAI
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ──────────────────────────────────────────────────────────────────────────────
# Prompt template
# ──────────────────────────────────────────────────────────────────────────────
def _next_prompt_template() -> str:
    return """
# What‑to‑Watch‑Next Prompt

Write a **single heading plus one paragraph** (80–120 words) titled **“What to Watch Next”**.  
Inputs:
• `summaries`: Concatenation of the six weekly category summaries (plain text).  
• `influencers`: List of influencer names/handles.

## Requirements
1. Begin with the heading exactly: `What to Watch Next` (no markdown symbols).  
2. Follow with one paragraph (no extra line breaks, no bullet points).  
3. **Purpose:** Synthesise the week’s takeaways into forward‑looking guidance—risks to monitor, opportunities to seize, trends worth following.  
4. Mention 2–3 influencer names from the list to track (no hyperlinks).  
5. End with: `For deeper analysis, refer to our detailed Daily Updates.`  
6. Tone: authoritative, vivid verbs; avoid clichés (cautiously optimistic, market dynamics, broader implications, etc.).  
7. If any claim in `summaries` is unverified, flag it with “Verify unconfirmed claims …” style language.

## Input Keys
- summaries: {summaries}
- influencers: {influencers}

## Output
Exactly:
What to Watch Next
<one paragraph 80–120 words>

(no surrounding markdown fences)
Example output:

What to Watch Next
Our Weekly Roundup shows a market fuelled by corporate cash and regulatory progress, but geopolitical shocks and security risks could jolt it. Bitcoin’s a safe bet, with DeFi and stablecoins gaining ground. AI-blockchain innovations promise big wins, but ethical and security hurdles need tackling. Track @Balaji for big-picture insights and CoinDesk for breaking news. Verify unconfirmed claims, like Fiserv’s stablecoin, before acting. 
For deeper analysis, refer to our detailed Daily Updates.
"""


# ──────────────────────────────────────────────────────────────────────────────
# Helper – assemble prompt
# ──────────────────────────────────────────────────────────────────────────────
def _build_next_prompt(summaries: str, influencers: List[str]) -> str:
    picks = ", ".join(sample(influencers, k=min(3, len(influencers)))) if influencers else "industry experts"
    tmpl = PromptTemplate(
        template=_next_prompt_template(),
        input_variables=["summaries", "influencers"],
    )
    return tmpl.format(summaries=summaries, influencers=picks)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────
def generate_watch_next(summaries: str, influencers: List[str]) -> str:
    """
    Create the “What to Watch Next” section.

    Parameters
    ----------
    summaries : List[str]
        The six category summary strings (already cleaned).
    influencers : List[str]
        Unified list of unique influencer handles/names.

    Returns
    -------
    str
        Heading + paragraph ready to append to the weekly report.
    """
    # combined = " ".join(summaries)
    prompt_text = _build_next_prompt(summaries, influencers)

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
