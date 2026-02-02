import os
import json
from typing import List
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from openai import OpenAI
from datetime import datetime
from ai_prompts.prompts_giver import middle_post_prompt
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Pydantic model for structured output
# class SummaryResponse(BaseModel):
#     summary: str = Field(description="Concise summary of all posts under the category, tagging relevant influencers")

def format_summary_prompt(category: str, category_desp, posts: List[dict], thread_no) -> tuple[str, PydanticOutputParser]:
    # parser = PydanticOutputParser(pydantic_object=SummaryResponse)
    template = middle_post_prompt()

        
    post_texts = "\n".join([
        f"{post['influencer']}: \"{post['text']}\"\n"
        for post in posts
    ])
    

    prompt = PromptTemplate(
        template=template,
        input_variables=["category", 'category_desp', "posts", 'thread_no'],
    )
    

    prompt_text = prompt.format(category=category, category_desp= category_desp, posts=post_texts, thread_no=thread_no)

    return prompt_text
    # return prompt_text, parser

def generate_category_summary(category: str, category_desp, posts: List[dict], thread_no) -> str:
    prompt_text = format_summary_prompt(category,category_desp, posts, thread_no)
    # prompt_text, parser = format_summary_prompt(category,category_desp, posts, thread_no, CTA)

    print(f'\nPrompt Text: {prompt_text}\n')
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_text}],
        temperature = 0.7
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
