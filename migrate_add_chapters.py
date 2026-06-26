"""
migrate_add_chapters.py
=======================
Run this ONCE to add chapter_order and is_chapter columns
to an existing milestones table, then seed chapters for any
already-assigned projects that don't have them yet.

    python migrate_add_chapters.py

Safe to run multiple times — skips if columns already exist.
"""
import os
from app import create_app
from app.extensions import db

app = create_app(os.environ.get("FLASK_ENV", "development"))

with app.app_context():
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    existing_cols = [c["name"] for c in inspector.get_columns("milestones")]

    # ── 1. Add missing columns ───────────────────────────────────────
    with db.engine.connect() as conn:

        if "chapter_order" not in existing_cols:
            conn.execute(text(
                "ALTER TABLE milestones ADD COLUMN chapter_order INTEGER NULL"
            ))
            conn.commit()
            print("[✓] Added column: chapter_order")
        else:
            print("[–] chapter_order already exists")

        if "is_chapter" not in existing_cols:
            # MySQL / SQLite compatible default
            conn.execute(text(
                "ALTER TABLE milestones ADD COLUMN is_chapter BOOLEAN NOT NULL DEFAULT 0"
            ))
            conn.commit()
            print("[✓] Added column: is_chapter")
        else:
            print("[–] is_chapter already exists")

    # ── 2. Seed chapters for assigned projects with no chapters yet ──
    from app.models.project import Project, ProjectStatus
    from app.models.milestone import Milestone, create_chapters_for_project

    assigned_projects = Project.query.filter(
        Project.supervisor_id.isnot(None)
    ).all()

    seeded = 0
    for project in assigned_projects:
        existing = Milestone.query.filter_by(
            project_id=project.project_id, is_chapter=True
        ).count()
        if existing == 0:
            create_chapters_for_project(project.project_id)
            seeded += 1
            print(f"[✓] Chapters created for: {project.project_title}")

    db.session.commit()

    if seeded == 0:
        print("[–] All assigned projects already have chapters")

    # ── 3. Verify ────────────────────────────────────────────────────
    total_chapters = Milestone.query.filter_by(is_chapter=True).count()
    print(f"\n[✓] Done. Total chapter milestones in DB: {total_chapters}")
    print("    You can now restart Flask — progress bar will work correctly.")