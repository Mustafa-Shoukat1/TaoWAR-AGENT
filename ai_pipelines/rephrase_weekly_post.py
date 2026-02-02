import os
from typing import Optional
from openai import OpenAI

# Set your API key in the env:  setx OPENAI_API_KEY "sk-xxx"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

REPHRASE_SYSTEM = (
    "You are a concise social copy editor. Rephrase the user's post text "
    "to be clear and engaging for X (Twitter)."
    "\nRules:"
    "\n- Preserve ALL @handles, #hashtags, $cashtags, and URLs EXACTLY as given."
    "\n- Preserve meaning and claims (no new facts)."
    "\n- Keep a professional, energetic tone."
    "\n- Keep within the provided character limit if one is given."
    "\n- Keep line breaks similar (short paragraphs ok)."
)

def build_prompt(post_text: str, max_len: Optional[int] = 280) -> str:
    # Give the model explicit constraints and the original content
    limit_line = f"Character limit: {max_len}." if max_len else "No strict character limit."
    return (
        f"{limit_line}\n\n"
        "Original post text (preserve @handles, #hashtags, $cashtags, and URLs exactly):\n"
        f"{post_text}\n\n"
        "Now rephrase it:"
    )

def rephrase_post(post_text: str, max_len: Optional[int] = 280, temperature: float = 0.7) -> str:
    if not post_text or not post_text.strip():
        raise ValueError("post_text cannot be empty")

    prompt = build_prompt(post_text, max_len=max_len)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": REPHRASE_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()

if __name__ == "__main__":
    # Example usage — replace this with your generated post_content
    post_content = (
        "Lord Reyoku Weekly DAMI Report is out with most engagement from "
        "@BLOCKCHAINCHICK @mattimost @arjunsethi @PeterSchiff and @cryptojack\n\n"
        "Full report available for $tWAR holders only at https://taowar.ai"
    )

    try:
        rephrased = rephrase_post(post_content, max_len=280)
        print("\n--- Rephrased Post ---\n")
        print(rephrased)
    except Exception as e:
        print(f"Error: {e}")
