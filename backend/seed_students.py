"""
Seed script to import students from All Contacts CSV
Run this with: python seed_students.py
"""
import csv
from app.core.database import SessionLocal
from app.models import Student
import os

def seed_students():
    csv_path = "/Users/djw/Documents/VortexHealing Assistant Docs/All Contacts/MainDB 102026.csv"

    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found at: {csv_path}")
        return

    db = SessionLocal()
    try:
        count = 0
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                first_name = row.get('First Name', '').strip()
                last_name = row.get('Last Name', '').strip()
                email = row.get('Email', '').strip()
                lists = row.get('Lists', '').strip()
                tags = row.get('Tags', '').strip()

                # Skip if no email
                if not email:
                    continue

                # Check if student already exists
                existing = db.query(Student).filter(Student.email == email).first()
                if existing:
                    # Update existing student
                    existing.first_name = first_name
                    existing.last_name = last_name
                    existing.lists = lists
                    existing.tags = tags
                    db.add(existing)
                else:
                    # Create new student
                    new_student = Student(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        lists=lists,
                        tags=tags,
                        status="active"
                    )
                    db.add(new_student)

                count += 1
                if count % 100 == 0:
                    print(f"Processing... {count} students")

        db.commit()
        print(f"\n✅ Successfully imported {count} students from All Contacts!")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_students()

