"""
DetectiveOS — Database Seeder
Loads all 5 case templates into the database.
Run: python -m app.db.seed
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.db.database import SessionLocal, engine
from app.models import Base, Case, Suspect, Evidence, User
from app.utils.auth import hash_password

CASES_DIR = Path(__file__).resolve().parents[3] / "case-templates"
CASE_FILES = [
    "midnight-manor.json",
    "harbor-street-blackout.json",
    "redwood-inheritance.json",
    "double-exposure.json",
    "zodiac-protocol.json",
    "glass-garden.json",
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ── Demo user ──────────────────────────────────────────
        if not db.query(User).filter(User.email == "detective@demo.com").first():
            demo = User(
                email="detective@demo.com",
                username="detective_demo",
                password_hash=hash_password("password123"),
                tier="pro",
                xp=1240,
                cases_solved=3,
                avatar="🕵️",
            )
            db.add(demo)
            print("✓ Created demo user: detective@demo.com / password123")

        # ── Cases ──────────────────────────────────────────────
        for fname in CASE_FILES:
            fpath = CASES_DIR / fname
            if not fpath.exists():
                print(f"⚠ Case file not found: {fpath}")
                continue

            with open(fpath,encoding = "utf-8") as f:
                data = json.load(f)

            slug = data["slug"]
            existing = db.query(Case).filter(Case.slug == slug).first()
            if existing:
                print(f"↷ Skipping existing case: {data['title']}")
                continue

            case = Case(
                title=data["title"],
                slug=slug,
                difficulty=data["difficulty"],
                setting=data.get("setting"),
                background=data["background"],
                victim_name=data["victim_name"],
                victim_age=data.get("victim_age"),
                victim_occupation=data.get("victim_occupation"),
                victim_profile=data.get("victim_profile", {}),
                true_culprit_name=data["true_culprit_name"],
                true_motive=data["true_motive"],
                true_method=data["true_method"],
                required_evidence_ids=data.get("required_evidence_ids", []),
                is_weekly=data.get("is_weekly", False),
                is_published=True,
            )
            db.add(case)
            db.flush()

            for s in data.get("suspects", []):
                suspect = Suspect(
                    case_id=case.id,
                    name=s["name"],
                    occupation=s.get("occupation"),
                    personality=s.get("personality"),
                    alibi=s.get("alibi"),
                    secrets=s.get("secrets", []),
                    relationship_to_victim=s.get("relationship_to_victim"),
                    is_culprit=s.get("is_culprit", False),
                    avatar=s.get("avatar", "🧑"),
                    motive_hint=s.get("motive_hint"),
                )
                db.add(suspect)

            for e in data.get("evidence", []):
                evidence = Evidence(
                    case_id=case.id,
                    type=e["type"],
                    title=e["title"],
                    description=e["description"],
                    content=e.get("content"),
                    icon=e.get("icon", "📄"),
                    is_hidden=e.get("is_hidden", False),
                    unlock_condition=e.get("unlock_condition"),
                    sort_order=e.get("sort_order", 0),
                )
                db.add(evidence)

            db.commit()
            weekly_tag = " [WEEKLY]" if data.get("is_weekly") else ""
            print(f"✓ Seeded case: {data['title']}{weekly_tag}")

        print("\n✅ Database seeded successfully.")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
