"""Conservative output checks, not a guarantee of semantic correctness."""
import re


def checked_response(content, evidence, citation_count):
    if not isinstance(content, str) or not content.strip():
        raise ValueError('텍스트 답변 없음')
    # Percentages, dates, academic credits and thresholds must not be invented.
    numbers = lambda text: set(re.findall(r'\d+(?:\.\d+)?', text))
    allowed = numbers(evidence) | {str(n) for n in range(1, citation_count + 1)}
    if numbers(content) - allowed:
        raise ValueError('근거 밖 수치')
    citations = re.findall(r'\[(\d+)\]', content)
    if not citations or any(not 1 <= int(c) <= citation_count for c in citations):
        raise ValueError('유효한 근거 인용 없음')
    return content.strip()
