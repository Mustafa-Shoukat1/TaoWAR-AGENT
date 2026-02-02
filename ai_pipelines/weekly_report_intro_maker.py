"""
intro_generator.py
Generate a one‑paragraph intro for the weekly market report.
"""

import os
from typing import List
from random import sample
from openai import OpenAI
from langchain.prompts import PromptTemplate

# Initialise OpenAI client
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_influencer_links(influencers: List[str]) -> str:
    """Format influencer profile links for X.com."""
    if not influencers:
        return ""
    # Remove @ if present
    return ", ".join([f"{handle}: https://x.com/{handle.lstrip('@')}" for handle in influencers])



# ──────────────────────────────────────────────────────────────────────────────
# Prompt template
# ──────────────────────────────────────────────────────────────────────────────
def _intro_prompt_template() -> str:
    return """
# Weekly Report Introduction Prompt

Write a single‑paragraph introduction (60–90 words) for a weekly cryptocurrency and traditional finance (TradFi) market report.
Yoiu have to return things in markdown format.

## Requirements
• Start with a dynamic welcome phrase (e.g., “Welcome to our Weekly Roundup…”).  
• State the report is based on **“our detailed Daily Reporting.”**  
• Mention the **total number of unique influencers and sources**: {count}.  
• Highlight **2–3 influencer names** chosen from the provided list (no hyperlinks, first names or handles only).  
• Summarise—vividly and concisely—what the report covers this week (e.g., corporate Bitcoin bets, AI‑blockchain breakthroughs).  
• Close with a sentence inviting readers to consult our Daily Reporting for deeper details.  
• Tone: conversational yet authoritative; avoid clichés like “cautiously optimistic,” “market dynamics,” “broader implications.”

- There should be no headings, bullet points, or line breaks in the output.
- Makrdown is to be only be used for the influencer links.

==================================================
🔗  LINK & ATTRIBUTION RULES
==================================================
• Every material claim must cite an *exact* source from the posts.  
• Embed links naturally on the noun/phrase (e.g. “BlackRock’s [ETF inflows](link)”).  
• Always name the author/handle in the sentence.  
• Use **only** the links provided; never invent new ones.
• You can make hyperlinks to the influncers that you will use them in your content.
• This is a must.
- You must make hyperlink the name of influencers that you will use in the content.
- You may make hyperlink like this: [name](link) or [name](https://x.com/name)

## Input Keys
- count: {count}
- influencers: {influencers}
- influencer_links: {influencer_links}

## Output
A single paragraph (no headings, no bullet points, no line breaks).

Example output: (this is just an example, not a template)

Welcome to our Weekly Roundup of our detailed Daily Reporting, compiled from insights shared by 31 unique influencers and sources, including voices like @TimDraper and platforms like CoinDesk. This report distils the crypto and TradFi markets’ activity for investors and professionals, blending verified trends with actionable insights. From corporate Bitcoin bets to AI-blockchain breakthroughs, we cut through the noise to show what’s driving the action and where it’s headed. For deeper details, refer to our Daily Reporting.
"""


# ──────────────────────────────────────────────────────────────────────────────
# Helper: build the prompt
# ──────────────────────────────────────────────────────────────────────────────
def _build_intro_prompt(count: int, influencers: List[str]) -> str:
    pick = ", ".join(sample(influencers, k=min(3, len(influencers)))) if influencers else "industry experts"
    influencer_links = format_influencer_links(influencers)
    prompt = PromptTemplate(
        template=_intro_prompt_template(),
        input_variables=["count", "influencers", "influencer_links"],
    ).format(count=count, influencers=pick, influencer_links=influencer_links)
    return prompt


# ──────────────────────────────────────────────────────────────────────────────
# Public: generate_intro
# ──────────────────────────────────────────────────────────────────────────────
def generate_intro(count: int, influencers: List[str]) -> str:
    """
    Return a polished intro paragraph ready to prepend to your weekly report.

    Parameters
    ----------
    count : int
        Total number of unique influencers and sources in the dataset.
    influencers : List[str]
        List of unique influencer names/handles.

    Returns
    -------
    str
        The generated introduction paragraph.
    """
    prompt_text = _build_intro_prompt(count, influencers)

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.7,
    )

    # Strip any leading/trailing whitespace just in case
    return response.choices[0].message.content.strip()
