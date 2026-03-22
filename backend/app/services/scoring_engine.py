import anthropic
from app.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def score_culprit(submitted: str, true_culprit: str) -> int:
    """40 points for correct culprit."""
    return 40 if submitted.strip().lower() == true_culprit.strip().lower() else 0


def score_motive(submitted_motive: str, true_motive: str) -> int:
    """Up to 20 points. Uses LLM for semantic similarity."""
    if not submitted_motive or len(submitted_motive) < 10:
        return 0
    try:
        prompt = f"""Score how closely the submitted motive matches the true motive.
Return ONLY a JSON like: {{"score": 15, "reason": "..."}}

True motive: {true_motive}
Submitted motive: {submitted_motive}

Score 0-20:
- 20: Captures the core motive precisely
- 15: Mostly correct, minor details off
- 10: Partially correct, grasps intent
- 5: Related but significantly off
- 0: Completely wrong or irrelevant
"""
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        import json, re
        text = resp.content[0].text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return min(20, max(0, int(data.get("score", 0))))
    except Exception:
        pass
    # Fallback: keyword match
    true_words = set(true_motive.lower().split())
    sub_words = set(submitted_motive.lower().split())
    overlap = len(true_words & sub_words) / max(len(true_words), 1)
    return int(overlap * 20)


def score_evidence(evidence_cited: list, required_evidence_ids: list) -> int:
    """Up to 25 points based on evidence quality."""
    if not evidence_cited or not required_evidence_ids:
        return 0
    cited_set = set(str(e) for e in evidence_cited)
    required_set = set(str(e) for e in required_evidence_ids)
    hits = len(cited_set & required_set)
    return min(25, hits * 8)


def score_speed(time_seconds: int) -> int:
    """Up to 15 points based on speed."""
    if time_seconds <= 0:
        return 0
    if time_seconds < 1800:   return 15   # < 30 min
    if time_seconds < 3600:   return 12   # < 1 hr
    if time_seconds < 7200:   return 8    # < 2 hr
    if time_seconds < 14400:  return 4    # < 4 hr
    return 1


def compute_score(
    culprit_submitted: str,
    true_culprit: str,
    motive_submitted: str,
    true_motive: str,
    method_submitted: str,
    evidence_cited: list,
    required_evidence_ids: list,
    time_seconds: int,
) -> dict:
    c = score_culprit(culprit_submitted, true_culprit)
    m = score_motive(motive_submitted, true_motive) if c > 0 else 0
    e = score_evidence(evidence_cited, required_evidence_ids)
    s = score_speed(time_seconds)
    total = c + m + e + s

    return {
        "culprit": c,
        "motive": m,
        "evidence": e,
        "speed": s,
        "total": total,
        "is_correct": c == 40,
    }


def get_xp_reward(score: int, is_correct: bool) -> int:
    base = score * 2
    if is_correct:
        base += 100
    return base


def get_verdict_message(is_correct: bool, score: int) -> str:
    if is_correct and score >= 85:
        return "Flawless deduction. The department is putting your name on the wall."
    if is_correct and score >= 65:
        return "Case closed. Solid police work. Room for improvement on the details."
    if is_correct:
        return "Right culprit, but the reasoning needs work. Lucky break or real instinct?"
    if score >= 30:
        return "Wrong culprit. You were close — the evidence pointed somewhere true."
    return "Back to the drawing board, detective. The killer walks free today."
