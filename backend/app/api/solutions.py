from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.models import Case, CaseProgress, PlayerSolution, Leaderboard, User
from app.schemas import SolutionSubmit, SolutionResponse, ScoreBreakdown
from app.services.scoring_engine import compute_score, get_xp_reward, get_verdict_message
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/cases", tags=["solutions"])


@router.post("/{slug}/solve", response_model=SolutionResponse)
def submit_solution(
    slug: str,
    data: SolutionSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(Case).filter(Case.slug == slug).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    progress = db.query(CaseProgress).filter(
        CaseProgress.user_id == current_user.id,
        CaseProgress.case_id == case.id
    ).first()

    if not progress:
        raise HTTPException(status_code=400, detail="Start the case first")

    if progress.status.value == "completed":
        raise HTTPException(status_code=400, detail="Already submitted a solution")

    # Calculate time taken
    time_seconds = int((datetime.utcnow() - progress.started_at).total_seconds())

    # Compute score
    result = compute_score(
        culprit_submitted=data.culprit_name,
        true_culprit=case.true_culprit_name,
        motive_submitted=data.motive,
        true_motive=case.true_motive,
        method_submitted=data.method,
        evidence_cited=data.evidence_cited,
        required_evidence_ids=case.required_evidence_ids or [],
        time_seconds=time_seconds,
    )

    xp = get_xp_reward(result["total"], result["is_correct"])

    # Save solution
    solution = PlayerSolution(
        user_id=current_user.id,
        case_id=case.id,
        culprit_name=data.culprit_name,
        motive=data.motive,
        method=data.method,
        evidence_cited=data.evidence_cited,
        time_taken_seconds=time_seconds,
        score=result["total"],
        score_breakdown=result,
        is_correct=result["is_correct"],
    )
    db.add(solution)

    # Update progress status
    progress.status = "completed"

    # Award XP
    current_user.xp = (current_user.xp or 0) + xp
    if result["is_correct"]:
        current_user.cases_solved = (current_user.cases_solved or 0) + 1

    # Update leaderboard
    lb = db.query(Leaderboard).filter(
        Leaderboard.user_id == current_user.id,
        Leaderboard.week == "global"
    ).first()
    if lb:
        lb.score = (lb.score or 0) + result["total"]
        lb.updated_at = datetime.utcnow()
    else:
        lb = Leaderboard(
            user_id=current_user.id,
            week="global",
            score=result["total"]
        )
        db.add(lb)

    db.commit()

    return SolutionResponse(
        is_correct=result["is_correct"],
        score=result["total"],
        breakdown=ScoreBreakdown(
            culprit=result["culprit"],
            motive=result["motive"],
            evidence=result["evidence"],
            speed=result["speed"],
            total=result["total"],
        ),
        true_culprit=case.true_culprit_name,
        true_motive=case.true_motive,
        true_method=case.true_method,
        verdict_message=get_verdict_message(result["is_correct"], result["total"]),
        xp_earned=xp,
    )


@router.get("/{slug}/solution")
def get_solution(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Only available after submission."""
    case = db.query(Case).filter(Case.slug == slug).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    solution = db.query(PlayerSolution).filter(
        PlayerSolution.user_id == current_user.id,
        PlayerSolution.case_id == case.id
    ).first()

    if not solution:
        raise HTTPException(status_code=403, detail="Submit your theory first")

    return {
        "true_culprit": case.true_culprit_name,
        "true_motive": case.true_motive,
        "true_method": case.true_method,
        "your_score": solution.score,
        "is_correct": solution.is_correct,
        "breakdown": solution.score_breakdown,
    }