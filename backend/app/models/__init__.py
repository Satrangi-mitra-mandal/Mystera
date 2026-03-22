import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime,
    ForeignKey, Enum, ARRAY, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.db.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserTier(str, enum.Enum):
    free = "free"
    pro = "pro"
    creator = "creator"


class CaseDifficulty(str, enum.Enum):
    rookie = "rookie"
    detective = "detective"
    mastermind = "mastermind"


class EvidenceType(str, enum.Enum):
    photo = "photo"
    document = "document"
    phone_log = "phone_log"
    cctv = "cctv"
    forensic = "forensic"


class CaseStatus(str, enum.Enum):
    in_progress = "in_progress"
    submitted = "submitted"
    completed = "completed"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    tier = Column(Enum(UserTier), default=UserTier.free, nullable=False)
    xp = Column(Integer, default=0)
    cases_solved = Column(Integer, default=0)
    avatar = Column(String(10), default="🕵️")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    progress = relationship("CaseProgress", back_populates="user")
    solutions = relationship("PlayerSolution", back_populates="user")


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    difficulty = Column(Enum(CaseDifficulty), nullable=False)
    background = Column(Text, nullable=False)
    setting = Column(String(255))
    victim_name = Column(String(255), nullable=False)
    victim_age = Column(Integer)
    victim_occupation = Column(String(255))
    victim_profile = Column(JSONB, default=dict)
    true_culprit_name = Column(String(255), nullable=False)
    true_motive = Column(Text, nullable=False)
    true_method = Column(Text, nullable=False)
    required_evidence_ids = Column(JSONB, default=list)
    is_weekly = Column(Boolean, default=False)
    is_published = Column(Boolean, default=True)
    creator_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    scene_svg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    suspects = relationship("Suspect", back_populates="case", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    progress = relationship("CaseProgress", back_populates="case")
    solutions = relationship("PlayerSolution", back_populates="case")


class Suspect(Base):
    __tablename__ = "suspects"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    occupation = Column(String(255))
    personality = Column(Text)
    alibi = Column(Text)
    secrets = Column(JSONB, default=list)
    relationship_to_victim = Column(Text)
    is_culprit = Column(Boolean, default=False)
    avatar = Column(String(10), default="🧑")
    motive_hint = Column(Text)
    responses = Column(JSONB, default=dict)

    case = relationship("Case", back_populates="suspects")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(EvidenceType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    content = Column(Text)
    asset_url = Column(String(500))
    icon = Column(String(10), default="📄")
    metadata_ = Column("metadata", JSONB, default=dict)
    is_hidden = Column(Boolean, default=False)
    unlock_condition = Column(String(255))
    sort_order = Column(Integer, default=0)

    case = relationship("Case", back_populates="evidence")


class CaseProgress(Base):
    __tablename__ = "case_progress"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    board_state = Column(JSONB, default=dict)
    unlocked_evidence = Column(JSONB, default=list)
    interrogated_suspects = Column(JSONB, default=list)
    interrogation_history = Column(JSONB, default=dict)
    status = Column(Enum(CaseStatus), default=CaseStatus.in_progress)

    user = relationship("User", back_populates="progress")
    case = relationship("Case", back_populates="progress")


class PlayerSolution(Base):
    __tablename__ = "player_solutions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    culprit_name = Column(String(255), nullable=False)
    motive = Column(Text)
    method = Column(Text)
    evidence_cited = Column(JSONB, default=list)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    time_taken_seconds = Column(Integer)
    score = Column(Integer, default=0)
    score_breakdown = Column(JSONB, default=dict)
    is_correct = Column(Boolean, default=False)

    user = relationship("User", back_populates="solutions")
    case = relationship("Case", back_populates="solutions")


class Leaderboard(Base):
    __tablename__ = "leaderboard"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id", ondelete="CASCADE"), nullable=True)
    week = Column(String(20), default="global")
    score = Column(Integer, default=0)
    rank = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
