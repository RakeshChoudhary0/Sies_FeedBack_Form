"""
Seed Script for Supabase / PostgreSQL
Inserts initial system settings, default feedback session, stakeholder categories,
and all 38 syllabus questions directly using SQLAlchemy ORM.
"""

import sys
import os
from pathlib import Path

# Ensure app directory is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import engine, SessionLocal, Base
import models

QUESTIONS_DATA = [
    # TEACHER
    {"text": "Name", "type": "TEACHER", "category": "DEMOGRAPHIC"},
    {"text": "Email ID (Enter SIES edu ID only)", "type": "TEACHER", "category": "DEMOGRAPHIC"},
    {"text": "Course", "type": "TEACHER", "category": "DEMOGRAPHIC"},
    {"text": "Class", "type": "TEACHER", "category": "DEMOGRAPHIC"},
    {"text": "Relevance of Syllabus Content : How well does the syllabus align with industry trends, technological advancements, and current academic standards?", "type": "TEACHER", "category": "SYLLABUS"},
    {"text": "Depth and Coverage : Does the syllabus provide a balanced mix of fundamental and advanced topics?", "type": "TEACHER", "category": "SYLLABUS"},
    {"text": "Practical Application : To what extent does the syllabus integrate hands on learning and real-world problem-solving?", "type": "TEACHER", "category": "SYLLABUS"},
    {"text": "Assessment Methods : How effectively do assessments align with learning outcomes?", "type": "TEACHER", "category": "SYLLABUS"},
    {"text": "Teaching Pedagogies : How effective are the teaching methodologies?", "type": "TEACHER", "category": "SYLLABUS"},
    {"text": "How would you rate the Overall Syllabus?", "type": "TEACHER", "category": "SYLLABUS"},
    {"text": "Suggestions for improvement based on your teaching experience.", "type": "TEACHER", "category": "SUGGESTION"},

    # STUDENT
    {"text": "Student Name", "type": "STUDENT", "category": "DEMOGRAPHIC"},
    {"text": "Roll Number / PRN", "type": "STUDENT", "category": "DEMOGRAPHIC"},
    {"text": "Email ID (Enter SIES edu ID only)", "type": "STUDENT", "category": "DEMOGRAPHIC"},
    {"text": "Program / Course", "type": "STUDENT", "category": "DEMOGRAPHIC"},
    {"text": "Class", "type": "STUDENT", "category": "DEMOGRAPHIC"},
    {"text": "Academic Year", "type": "STUDENT", "category": "DEMOGRAPHIC"},
    {"text": "How well does the syllabus align with current industry trends?", "type": "STUDENT", "category": "SYLLABUS"},
    {"text": "Does the syllabus provide a balanced mix of fundamental and advanced topics?", "type": "STUDENT", "category": "SYLLABUS"},
    {"text": "How effective are the teaching methodologies?", "type": "STUDENT", "category": "SYLLABUS"},
    {"text": "How well does the syllabus prepare you for employment or higher studies?", "type": "STUDENT", "category": "SYLLABUS"},
    {"text": "Any other feedback or suggestions regarding curriculum or NEP implementation?", "type": "STUDENT", "category": "SUGGESTION"},

    # ALUMNI
    {"text": "Student Name", "type": "ALUMNI", "category": "DEMOGRAPHIC"},
    {"text": "Email ID", "type": "ALUMNI", "category": "DEMOGRAPHIC"},
    {"text": "Course", "type": "ALUMNI", "category": "DEMOGRAPHIC"},
    {"text": "Relevance of syllabus content with industry trends and academic standards", "type": "ALUMNI", "category": "SYLLABUS"},
    {"text": "Depth and coverage of syllabus topics", "type": "ALUMNI", "category": "SYLLABUS"},
    {"text": "Practical application and real-world problem solving", "type": "ALUMNI", "category": "SYLLABUS"},
    {"text": "Effectiveness of assessment methods", "type": "ALUMNI", "category": "SYLLABUS"},
    {"text": "Effectiveness of teaching pedagogies", "type": "ALUMNI", "category": "SYLLABUS"},
    {"text": "Overall satisfaction with the syllabus learned", "type": "ALUMNI", "category": "SYLLABUS"},
    {"text": "Suggestions for improving syllabus, teaching methods, or learning experience", "type": "ALUMNI", "category": "SUGGESTION"},

    # EMPLOYER
    {"text": "Name of Employer", "type": "EMPLOYER", "category": "DEMOGRAPHIC"},
    {"text": "Name of Institution / Organization", "type": "EMPLOYER", "category": "DEMOGRAPHIC"},
    {"text": "Designation", "type": "EMPLOYER", "category": "DEMOGRAPHIC"},
    {"text": "Email Address", "type": "EMPLOYER", "category": "DEMOGRAPHIC"},
    {"text": "Stream from which students are employed", "type": "EMPLOYER", "category": "DEMOGRAPHIC"},
    {"text": "Curriculum relevance for employability", "type": "EMPLOYER", "category": "SYLLABUS"},
    {"text": "Curriculum effectiveness in developing innovative thinking", "type": "EMPLOYER", "category": "SYLLABUS"},
    {"text": "Effectiveness of syllabus in developing skill-oriented human resources", "type": "EMPLOYER", "category": "SYLLABUS"},
    {"text": "Need-based nature of the current syllabus as per industry requirements", "type": "EMPLOYER", "category": "SYLLABUS"},
    {"text": "Effectiveness of curriculum in developing entrepreneurship skills", "type": "EMPLOYER", "category": "SYLLABUS"},
    {"text": "Student sensitivity towards ethics, values, sustainability, and social issues", "type": "EMPLOYER", "category": "SYLLABUS"},
    {"text": "Students are equipped with latest developments in their field", "type": "EMPLOYER", "category": "SYLLABUS"},
    {"text": "Topics that should be included in the curriculum", "type": "EMPLOYER", "category": "SUGGESTION"},
    {"text": "Opinion on implementation of NEP and Autonomy in the college", "type": "EMPLOYER", "category": "SUGGESTION"},

    # OUTSIDE COLLEGE TEACHER
    {"text": "Name of Respondent", "type": "OUTSIDE_TEACHER", "category": "DEMOGRAPHIC"},
    {"text": "College of Respondent", "type": "OUTSIDE_TEACHER", "category": "DEMOGRAPHIC"},
    {"text": "Subject Name", "type": "OUTSIDE_TEACHER", "category": "DEMOGRAPHIC"},
    {"text": "Email", "type": "OUTSIDE_TEACHER", "category": "DEMOGRAPHIC"},
    {"text": "Program Name", "type": "OUTSIDE_TEACHER", "category": "DEMOGRAPHIC"},
    {"text": "Years / Semester taught", "type": "OUTSIDE_TEACHER", "category": "DEMOGRAPHIC"},
    {"text": "Entrepreneurship skill development through course content", "type": "OUTSIDE_TEACHER", "category": "SYLLABUS"},
    {"text": "Employability relevance of course content", "type": "OUTSIDE_TEACHER", "category": "SYLLABUS"},
    {"text": "Contribution of course content to skill development", "type": "OUTSIDE_TEACHER", "category": "SYLLABUS"},
    {"text": "Alignment of course content with recent trends and advancements", "type": "OUTSIDE_TEACHER", "category": "SYLLABUS"},

    # PARENTS
    {"text": "Name of Parent", "type": "PARENT", "category": "DEMOGRAPHIC"},
    {"text": "Name of Ward", "type": "PARENT", "category": "DEMOGRAPHIC"},
    {"text": "Wards Stream", "type": "PARENT", "category": "DEMOGRAPHIC"},
    {"text": "Overall satisfaction with NEP implementation", "type": "PARENT", "category": "SYLLABUS"},
    {"text": "Flexibility of curriculum for diverse subject exploration", "type": "PARENT", "category": "SYLLABUS"},
    {"text": "Employability focus of the curriculum", "type": "PARENT", "category": "SYLLABUS"},
    {"text": "Support for industry-relevant skill development", "type": "PARENT", "category": "SYLLABUS"},
    {"text": "Inclusion of practical learning opportunities", "type": "PARENT", "category": "SYLLABUS"},
    {"text": "Holistic development through co-curricular activities under NEP", "type": "PARENT", "category": "SYLLABUS"},
    {"text": "Collaboration and teamwork opportunities in syllabus", "type": "PARENT", "category": "SYLLABUS"},
    {"text": "Overall impact of NEP on educational quality", "type": "PARENT", "category": "SYLLABUS"},
    {"text": "Suggestions for new topics to be included in the syllabus", "type": "PARENT", "category": "SUGGESTION"},
    {"text": "Additional comments or suggestions regarding NEP implementation", "type": "PARENT", "category": "SUGGESTION"},
]

STAKEHOLDER_TYPES = ["TEACHER", "STUDENT", "ALUMNI", "EMPLOYER", "OUTSIDE_TEACHER", "PARENT"]

def seed():
    print("[*] Creating all database tables if not existing...")
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. System Settings
        settings = db.query(models.SystemSettings).first()
        if not settings:
            db.add(models.SystemSettings(id=1, is_active=True))
            print("[+] Initialized SystemSettings (is_active=True)")

        # 2. Default Session
        session = db.query(models.FeedbackSession).first()
        if not session:
            db.add(models.FeedbackSession(session_id=1, session_name="Default Session"))
            print("[+] Initialized Default FeedbackSession")

        # 3. Stakeholder Types
        for s_type in STAKEHOLDER_TYPES:
            existing = db.query(models.Stakeholder).filter_by(stakeholder_type=s_type).first()
            if not existing:
                db.add(models.Stakeholder(stakeholder_type=s_type))
                print(f"[+] Added Stakeholder: {s_type}")

        db.commit()

        # 4. Questions
        existing_q_count = db.query(models.SyllabusQuestion).count()
        if existing_q_count == 0:
            for item in QUESTIONS_DATA:
                q = models.SyllabusQuestion(
                    text=item["text"],
                    stakeholder_type=item["type"],
                    category=item["category"]
                )
                db.add(q)
            db.commit()
            print(f"[+] Seeded {len(QUESTIONS_DATA)} questions successfully.")
        else:
            print(f"[!] {existing_q_count} questions already exist in database. Skipping questions seeding.")

        print("[OK] Supabase / PostgreSQL database seeding complete!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()

