from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.db.database import get_db
from app.models import Case, CaseProgress, PlayerSolution, Evidence
from app.schemas import CaseListItem, CaseDetail, CaseProgressResponse, SuspectPublic, EvidencePublic
from app.utils.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _case_to_list_item(case: Case, db: Session) -> dict:
    solver_count = db.query(func.count(PlayerSolution.id)).filter(
        PlayerSolution.case_id == case.id,
        PlayerSolution.is_correct == True
    ).scalar() or 0
    total_attempts = db.query(func.count(PlayerSolution.id)).filter(
        PlayerSolution.case_id == case.id
    ).scalar() or 0
    solve_rate = round((solver_count / total_attempts * 100) if total_attempts > 0 else 0, 1)

    return {
        "id": case.id,
        "title": case.title,
        "slug": case.slug,
        "difficulty": case.difficulty,
        "setting": case.setting,
        "victim_name": case.victim_name,
        "is_weekly": case.is_weekly,
        "is_published": case.is_published,
        "suspect_count": len(case.suspects),
        "evidence_count": len(case.evidence),
        "solvers_count": solver_count,
        "solve_rate": solve_rate,
        "created_at": case.created_at,
    }


@router.get("/", response_model=List[dict])
def list_cases(
    difficulty: Optional[str] = None,
    weekly: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Case).filter(Case.is_published == True)
    if difficulty:
        q = q.filter(Case.difficulty == difficulty)
    if weekly is not None:
        q = q.filter(Case.is_weekly == weekly)
    cases = q.order_by(Case.created_at.desc()).all()
    return [_case_to_list_item(c, db) for c in cases]


@router.get("/{slug}", response_model=dict)
def get_case(slug: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.slug == slug, Case.is_published == True).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    visible_evidence = [e for e in case.evidence if not e.is_hidden]
    return {
        "id": case.id,
        "title": case.title,
        "slug": case.slug,
        "difficulty": case.difficulty.value,
        "background": case.background,
        "setting": case.setting,
        "victim_name": case.victim_name,
        "victim_age": case.victim_age,
        "victim_occupation": case.victim_occupation,
        "victim_profile": case.victim_profile,
        "is_weekly": case.is_weekly,
        "suspects": [
            {
                "id": s.id, "name": s.name, "occupation": s.occupation,
                "personality": s.personality, "alibi": s.alibi,
                "relationship_to_victim": s.relationship_to_victim,
                "avatar": s.avatar, "motive_hint": s.motive_hint,
            } for s in case.suspects
        ],
        "evidence": [
            {
                "id": e.id, "type": e.type.value, "title": e.title,
                "description": e.description, "content": e.content,
                "icon": e.icon, "is_hidden": e.is_hidden,
                "unlock_condition": e.unlock_condition, "sort_order": e.sort_order,
            } for e in sorted(visible_evidence, key=lambda x: x.sort_order)
        ],
        "timeline": case.victim_profile.get("timeline", []),
        "created_at": case.created_at.isoformat(),
    }


@router.post("/{slug}/start", response_model=dict)
def start_case(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(Case).filter(Case.slug == slug).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    existing = db.query(CaseProgress).filter(
        CaseProgress.user_id == current_user.id,
        CaseProgress.case_id == case.id
    ).first()

    if existing:
        return {
            "id": existing.id, "case_id": existing.case_id,
            "started_at": existing.started_at.isoformat(),
            "board_state": existing.board_state,
            "unlocked_evidence": existing.unlocked_evidence,
            "interrogated_suspects": existing.interrogated_suspects,
            "status": existing.status.value,
            "already_started": True
        }

    progress = CaseProgress(
        user_id=current_user.id,
        case_id=case.id,
        board_state={"pins": [], "connections": [], "notes": ""},
        unlocked_evidence=[],
        interrogated_suspects=[],
        interrogation_history={}
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)

    return {
        "id": progress.id, "case_id": progress.case_id,
        "started_at": progress.started_at.isoformat(),
        "board_state": progress.board_state,
        "unlocked_evidence": progress.unlocked_evidence,
        "interrogated_suspects": progress.interrogated_suspects,
        "status": progress.status.value,
        "already_started": False
    }


@router.get("/{slug}/progress", response_model=dict)
def get_progress(
    slug: str,
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
        raise HTTPException(status_code=404, detail="Case not started")

    return {
        "id": progress.id, "case_id": progress.case_id,
        "started_at": progress.started_at.isoformat(),
        "board_state": progress.board_state,
        "unlocked_evidence": progress.unlocked_evidence,
        "interrogated_suspects": progress.interrogated_suspects,
        "status": progress.status.value,
    }


@router.put("/{slug}/board")
def save_board(
    slug: str,
    data: dict,
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
        raise HTTPException(status_code=404, detail="Start the case first")

    progress.board_state = data
    db.commit()
    return {"status": "saved"}