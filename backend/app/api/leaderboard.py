from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from app.db.database import get_db
from app.models import Leaderboard, User, PlayerSolution
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("/global")
def global_leaderboard(
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    results = (
        db.query(Leaderboard, User)
        .join(User, User.id == Leaderboard.user_id)
        .filter(Leaderboard.week == "global")
        .order_by(desc(Leaderboard.score))
        .limit(limit)
        .all()
    )

    entries = []
    for rank, (lb, user) in enumerate(results, 1):
        entries.append({
            "rank": rank,
            "username": user.username,
            "avatar": user.avatar,
            "score": lb.score,
            "cases_solved": user.cases_solved,
            "xp": user.xp,
            "is_you": current_user and user.id == current_user.id,
        })

    # Inject current user if not in top list
    if current_user:
        user_in_list = any(e["is_you"] for e in entries)
        if not user_in_list:
            user_lb = db.query(Leaderboard).filter(
                Leaderboard.user_id == current_user.id,
                Leaderboard.week == "global"
            ).first()
            if user_lb:
                # Calculate rank
                rank_count = db.query(func.count(Leaderboard.id)).filter(
                    Leaderboard.week == "global",
                    Leaderboard.score > user_lb.score
                ).scalar() + 1
                entries.append({
                    "rank": rank_count,
                    "username": current_user.username,
                    "avatar": current_user.avatar,
                    "score": user_lb.score,
                    "cases_solved": current_user.cases_solved,
                    "xp": current_user.xp,
                    "is_you": True,
                    "separator": True,
                })

    return {"entries": entries, "total": len(entries)}


@router.get("/weekly")
def weekly_leaderboard(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    from datetime import datetime
    week_key = datetime.utcnow().strftime("%Y-W%W")

    results = (
        db.query(func.sum(PlayerSolution.score).label("weekly_score"), User)
        .join(User, User.id == PlayerSolution.user_id)
        .filter(func.date_trunc('week', PlayerSolution.submitted_at) == func.date_trunc('week', func.now()))
        .group_by(User.id)
        .order_by(desc("weekly_score"))
        .limit(50)
        .all()
    )

    return {
        "week": week_key,
        "entries": [
            {
                "rank": i + 1,
                "username": user.username,
                "avatar": user.avatar,
                "score": int(score or 0),
                "cases_solved": user.cases_solved,
                "is_you": current_user and user.id == current_user.id,
            }
            for i, (score, user) in enumerate(results)
        ]
    }


@router.get("/case/{slug}")
def case_leaderboard(
    slug: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    from app.models import Case
    case = db.query(Case).filter(Case.slug == slug).first()
    if not case:
        return {"entries": []}

    results = (
        db.query(PlayerSolution, User)
        .join(User, User.id == PlayerSolution.user_id)
        .filter(PlayerSolution.case_id == case.id, PlayerSolution.is_correct == True)
        .order_by(desc(PlayerSolution.score))
        .limit(50)
        .all()
    )

    return {
        "case": case.title,
        "entries": [
            {
                "rank": i + 1,
                "username": user.username,
                "avatar": user.avatar,
                "score": sol.score,
                "time_minutes": (sol.time_taken_seconds or 0) // 60,
                "submitted_at": sol.submitted_at.isoformat(),
                "is_you": current_user and user.id == current_user.id,
            }
            for i, (sol, user) in enumerate(results)
        ]
    }