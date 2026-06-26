"""
app/data/seed_lasu.py

Run once after `flask db upgrade` to populate faculties and departments.

    python -m app.data.seed_lasu

Or call seed_lasu_data(app) from seed.py.
"""
from app.data.lasu_data import LASU_DATA


def seed_lasu_data(app):
    from app.extensions import db
    from app.models.faculty import Faculty
    from app.models.department import Department

    with app.app_context():
        inserted_faculties = 0
        inserted_depts = 0

        for entry in LASU_DATA:
            faculty = Faculty.query.filter_by(faculty_code=entry["code"]).first()
            if not faculty:
                faculty = Faculty(
                    faculty_name=entry["name"],
                    faculty_code=entry["code"],
                    is_active=True,
                )
                db.session.add(faculty)
                db.session.flush()   # get faculty_id before adding departments
                inserted_faculties += 1

            for dept in entry["departments"]:
                exists = Department.query.filter_by(
                    faculty_id=faculty.faculty_id,
                    department_code=dept["code"],
                ).first()
                if not exists:
                    db.session.add(Department(
                        faculty_id=faculty.faculty_id,
                        department_name=dept["name"],
                        department_code=dept["code"],
                        is_active=True,
                    ))
                    inserted_depts += 1

        db.session.commit()
        print(f"[✓] Seeded {inserted_faculties} faculties, {inserted_depts} departments.")


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from app import create_app
    seed_lasu_data(create_app("development"))
