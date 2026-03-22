from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ── Auth ──────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8)
    avatar: Optional[str] = "🕵️"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserPublic"


class UserPublic(BaseModel):
    id: str
    email: str
    username: str
    tier: str
    xp: int
    cases_solved: int
    avatar: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Cases ─────────────────────────────────────────────────────────
class CaseListItem(BaseModel):
    id: str
    title: str
    slug: str
    difficulty: str
    setting: Optional[str]
    victim_name: str
    is_weekly: bool
    is_published: bool
    suspect_count: int
    evidence_count: int
    solvers_count: int
    solve_rate: float
    created_at: datetime

    class Config:
        from_attributes = True


class SuspectPublic(BaseModel):
    id: str
    name: str
    occupation: Optional[str]
    personality: Optional[str]
    alibi: Optional[str]
    relationship_to_victim: Optional[str]
    avatar: str
    motive_hint: Optional[str]

    class Config:
        from_attributes = True


class EvidencePublic(BaseModel):
    id: str
    type: str
    title: str
    description: str
    content: Optional[str]
    icon: str
    is_hidden: bool
    unlock_condition: Optional[str]
    sort_order: int

    class Config:
        from_attributes = True


class CaseDetail(BaseModel):
    id: str
    title: str
    slug: str
    difficulty: str
    background: str
    setting: Optional[str]
    victim_name: str
    victim_age: Optional[int]
    victim_occupation: Optional[str]
    victim_profile: Dict[str, Any]
    is_weekly: bool
    suspects: List[SuspectPublic]
    evidence: List[EvidencePublic]
    created_at: datetime

    class Config:
        from_attributes = True


class CaseProgressResponse(BaseModel):
    id: str
    case_id: str
    started_at: datetime
    board_state: Dict[str, Any]
    unlocked_evidence: List[str]
    interrogated_suspects: List[str]
    status: str

    class Config:
        from_attributes = True


# ── Board ─────────────────────────────────────────────────────────
class BoardStateUpdate(BaseModel):
    pins: List[Dict[str, Any]] = []
    connections: List[Dict[str, Any]] = []
    notes: Optional[str] = ""


# ── Interrogation ─────────────────────────────────────────────────
class InterrogationRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    history: Optional[List[Dict[str, str]]] = []


class InterrogationResponse(BaseModel):
    reply: str
    suspect_name: str
    questions_remaining: int


# ── Solutions ─────────────────────────────────────────────────────
class SolutionSubmit(BaseModel):
    culprit_name: str
    motive: str = Field(..., min_length=20)
    method: str = Field(..., min_length=20)
    evidence_cited: List[str] = Field(..., min_items=1)


class ScoreBreakdown(BaseModel):
    culprit: int
    motive: int
    evidence: int
    speed: int
    total: int


class SolutionResponse(BaseModel):
    is_correct: bool
    score: int
    breakdown: ScoreBreakdown
    true_culprit: str
    true_motive: str
    true_method: str
    verdict_message: str
    xp_earned: int


# ── Leaderboard ───────────────────────────────────────────────────
class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    avatar: str
    score: int
    cases_solved: int
    is_you: bool = False

    class Config:
        from_attributes = True
