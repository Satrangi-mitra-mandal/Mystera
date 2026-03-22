from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import Suspect, Case, CaseProgress, User
from app.schemas import InterrogationRequest, InterrogationResponse
from app.services.ai_interrogation import interrogate_suspect, get_question_limit
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/interrogate", tags=["interrogation"])

FREE_LIMIT = 10


@router.post("/{suspect_id}", response_model=InterrogationResponse)
def ask_suspect(
    suspect_id: str,
    data: InterrogationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
    if not suspect:
        raise HTTPException(status_code=404, detail="Suspect not found")

    case = db.query(Case).filter(Case.id == suspect.case_id).first()

    # Get or find progress
    progress = db.query(CaseProgress).filter(
        CaseProgress.user_id == current_user.id,
        CaseProgress.case_id == suspect.case_id
    ).first()

    if not progress:
        raise HTTPException(status_code=400, detail="Start the case first")

    # Track interrogation history per suspect
    history = progress.interrogation_history or {}
    suspect_history = history.get(suspect_id, [])

    # Enforce quota for free tier
    question_limit = get_question_limit(current_user.tier)
    total_questions = sum(len(v) for v in history.values())

    if current_user.tier == "free" and total_questions >= FREE_LIMIT:
        raise HTTPException(
            status_code=403,
            detail=f"Free tier limit of {FREE_LIMIT} questions reached. Upgrade to Pro."
        )

    # Get AI reply
    reply = interrogate_suspect(
        suspect=suspect,
        case=case,
        user_message=data.message,
        history=suspect_history,
        user_tier=current_user.tier
    )

    # Update history
    suspect_history.append({"role": "user", "content": data.message})
    suspect_history.append({"role": "assistant", "content": reply})
    history[suspect_id] = suspect_history
    progress.interrogation_history = history

    # Mark suspect as interrogated
    interrogated = progress.interrogated_suspects or []
    if suspect_id not in interrogated:
        interrogated.append(suspect_id)
        progress.interrogated_suspects = interrogated

    db.commit()

    total_used = sum(len(v) for v in history.values()) // 2  # turns not messages
    remaining = max(0, question_limit - total_used) if current_user.tier == "free" else 999

    return InterrogationResponse(
        reply=reply,
        suspect_name=suspect.name,
        questions_remaining=remaining
    )