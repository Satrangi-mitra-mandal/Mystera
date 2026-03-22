import anthropic
from app.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

FREE_TIER_LIMIT = 10
PRO_TIER_LIMIT = 999


def build_system_prompt(suspect, case) -> str:
    secrets_text = "\n".join(f"- {s}" for s in (suspect.secrets or []))
    return f"""You are {suspect.name}, a character being interrogated in a murder mystery.

CASE: {case.title}
VICTIM: {case.victim_name}
YOUR ROLE: {suspect.occupation}
YOUR PERSONALITY: {suspect.personality}
YOUR ALIBI: {suspect.alibi}
YOUR RELATIONSHIP TO VICTIM: {suspect.relationship_to_victim}
YOUR SECRETS (NEVER reveal directly, but they should subtly influence your answers under pressure):
{secrets_text}
ARE YOU THE CULPRIT: {"YES" if suspect.is_culprit else "NO"}

RULES:
- Stay completely in character. You are being interrogated by a detective.
- If innocent: answer truthfully but may withhold embarrassing truths. Show appropriate emotion.
- If guilty: lie strategically, deflect, subtly show nerves when cornered. Plant small tells.
- Never break the fourth wall or mention this is a game/story.
- When pressed about contradictions, show discomfort through word choice — hesitation, over-explanation, subject changes.
- Keep responses to 2–4 sentences. Terse, realistic, emotionally grounded.
- Speak in first person. No narration.
- React to the tone of the question — aggressive questions get defensive answers; gentle questions get more revealing ones.
"""


def get_question_limit(user_tier: str) -> int:
    if user_tier in ("pro", "creator"):
        return PRO_TIER_LIMIT
    return FREE_TIER_LIMIT


def interrogate_suspect(suspect, case, user_message: str, history: list, user_tier: str) -> str:
    system = build_system_prompt(suspect, case)

    messages = []
    for h in history[-8:]:  # keep last 8 turns for context
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=system,
            messages=messages,
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"[I have nothing more to say right now.]"
