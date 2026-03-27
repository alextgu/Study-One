# ============================================
# SLIDE STUDY PACK GENERATION PROMPTS
# ============================================

import json

def build_chunk_summary_prompt(*, chunk: str, chunk_index: int, total_chunks: int) -> str:
    return f"""You are processing chunk {chunk_index} of {total_chunks} from lecture slides.

Return strict JSON only (no markdown/code fences):
{{
  "summary": ["3-5 concise bullets for this chunk"],
  "key_facts": ["5-10 short factual statements grounded in this chunk"]
}}

Chunk text:
\"\"\"{chunk}\"\"\""""


def build_merge_outline_prompt(*, chunk_summaries: list[str], key_facts: list[str]) -> str:
    merge_input = {
        "chunk_summaries": chunk_summaries,
        "key_facts": key_facts,
    }
    return f"""You are merging chunk-level notes into a canonical lecture outline.
Use only the provided items.

Return strict JSON only:
{{
  "outline": ["8-20 bullets in coherent order"],
  "summary": ["5-8 final concise bullets for students"],
  "focus_topics": ["5-12 short topic labels"]
}}

Input JSON:
{json.dumps(merge_input, ensure_ascii=False)}"""