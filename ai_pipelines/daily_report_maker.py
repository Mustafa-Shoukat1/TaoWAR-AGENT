import os
import json
from typing import List
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from openai import OpenAI
from datetime import datetime
from ai_prompts.daily_report_prompt import report_prompt
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Pydantic model for structured output
# class SummaryResponse(BaseModel):
#     summary: str = Field(description="Concise summary of all posts under the category, tagging relevant influencers")

def format_report_prompt(category: str, category_desp, posts: List[dict]) -> str:
    template = report_prompt()
    if posts:
        formatted_posts = ""
        for idx, post in enumerate(posts, 1):
            if post["text"]:
                formatted_posts += (
                    f"### Post {idx}\n"
                    f"- **Influencer:** [{post['influencer']}]({post['link']})\n"
                    f"- **Link:** {post['link']}\n"
                    f"- **Content:** {post['text']}\n\n"
                )
    else:
        formatted_posts = "_No posts found for this category today._"

    prompt = PromptTemplate(
        template=template,
        input_variables=["category", "category_desp", "posts"],
    )
    prompt_text = prompt.format(
        category=category,
        category_desp=category_desp,
        posts=formatted_posts,
    )
    return prompt_text


def generate_report(category: str, category_desp, posts: List[dict]) -> str:
    prompt_text = format_report_prompt(category, category_desp, posts)
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

