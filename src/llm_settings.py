"""Bound each optional API response; this is not an account spending limit."""
import os


def llm_options():
    try: maximum=int(os.getenv('OPENAI_MAX_OUTPUT_TOKENS','800'))
    except (TypeError,ValueError): maximum=800
    return dict(model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'),temperature=0,
                timeout=30,max_retries=0,max_tokens=max(128,min(maximum,2000)))
