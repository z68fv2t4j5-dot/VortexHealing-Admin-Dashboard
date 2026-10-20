"""
Seed script to populate VortexHealing classes into the database
Run this with: python seed_classes.py
"""
from app.core.database import SessionLocal
from app.models import Class
from datetime import datetime

classes_data = [
    {"name": "Sensing II", "description": "Deepen your sensing and psychic abilities - Level II", "instructor": "Daniel Wald", "capacity": 2980, "schedule": "Multiple sessions", "prerequisites": "Sensing I", "start_date": datetime(2026, 10, 4, 13, 30), "end_date": datetime(2026, 10, 6, 22, 30)},
    {"name": "Sensing III", "description": "Advanced sensing and consciousness development - Level III", "instructor": "Daniel Wald", "capacity": 2470, "schedule": "Multiple sessions", "prerequisites": "Sensing II", "start_date": datetime(2026, 10, 7, 13, 0), "end_date": datetime(2026, 10, 8, 22, 0)},
    {"name": "Clearing the Kundalini Channel", "description": "Clear and activate your kundalini channel", "instructor": "Daniel Wald", "capacity": 4915, "schedule": "Multiple sessions", "prerequisites": "Sensing I", "start_date": datetime(2026, 10, 31, 14, 0), "end_date": datetime(2026, 11, 3, 22, 0)},
    {"name": "Magical Structures", "description": "Learn to work with magical structures and geometric frequencies", "instructor": "Daniel Wald", "capacity": 1760, "schedule": "Multiple sessions", "prerequisites": "Sensing I", "start_date": datetime(2026, 11, 11, 13, 30), "end_date": datetime(2026, 11, 15, 22, 0)},
    {"name": "Connecting with Quinstel (Asia and Europe Timezone)", "description": "Connect with Quinstel consciousness entity", "instructor": "Daniel Wald", "capacity": 400, "schedule": "Multiple sessions", "prerequisites": "Sensing II", "start_date": datetime(2026, 11, 29, 13, 30), "end_date": datetime(2026, 11, 30, 22, 30)},
    {"name": "Deepening in Meditation with Merlin", "description": "Deepen your meditation practice with Merlin's guidance", "instructor": "Daniel Wald", "capacity": 1080, "schedule": "In-person at The Treehouse", "prerequisites": "Basic meditation", "start_date": datetime(2026, 12, 12, 9, 30), "end_date": datetime(2026, 12, 12, 17, 30)},
    {"name": "Sensing I: Psychic and Consciousness Development", "description": "Foundational psychic and consciousness development - Level I", "instructor": "Daniel Wald", "capacity": 1197, "schedule": "In-person at The Treehouse", "prerequisites": "None", "start_date": datetime(2026, 12, 13, 9, 30), "end_date": datetime(2026, 12, 13, 18, 30)},
    {"name": "Connecting with Quinstel (US Timezone)", "description": "Connect with Quinstel consciousness entity - US times", "instructor": "Daniel Wald", "capacity": 7600, "schedule": "Multiple sessions", "prerequisites": "Sensing II", "start_date": datetime(2026, 12, 27, 9, 30), "end_date": datetime(2026, 12, 28, 18, 30)},
    {"name": "Karmic Intensive", "description": "Work intensively with karmic patterns and release", "instructor": "Daniel Wald", "capacity": 400, "schedule": "Multiple sessions", "prerequisites": "Sensing II", "start_date": datetime(2027, 1, 9, 14, 0), "end_date": datetime(2027, 1, 10, 23, 0)},
    {"name": "Multi-Frequency & Merlin's Jewel", "description": "Advanced work with multiple frequencies and Merlin's Jewel", "instructor": "Daniel Wald", "capacity": 990, "schedule": "Multiple sessions", "prerequisites": "Sensing III", "start_date": datetime(2027, 1, 26, 14, 30), "end_date": datetime(2027, 1, 31, 23, 0)},
    {"name": "Foundational Training", "description": "Complete foundational training in VortexHealing principles", "instructor": "Daniel Wald", "capacity": 400, "schedule": "Multiple sessions", "prerequisites": "Sensing I", "start_date": datetime(2027, 2, 17, 14, 30), "end_date": datetime(2027, 2, 21, 23, 0)},
    {"name": "InterDimensional Vortex", "description": "Access and work with interdimensional vortex frequencies", "instructor": "Daniel Wald", "capacity": 590, "schedule": "Multiple sessions", "prerequisites": "Sensing II", "start_date": datetime(2027, 3, 12, 14, 0), "end_date": datetime(2027, 3, 14, 23, 0)},
    {"name": "LifeForm", "description": "Work with life form frequencies and consciousness", "instructor": "Daniel Wald", "capacity": 880, "schedule": "Multiple sessions", "prerequisites": "Sensing II", "start_date": datetime(2027, 4, 14, 13, 30), "end_date": datetime(2027, 4, 18, 22, 30)},
    {"name": "Foundational Training (May)", "description": "Complete foundational training - May session", "instructor": "Daniel Wald", "capacity": 880, "schedule": "Multiple sessions", "prerequisites": "Sensing I", "start_date": datetime(2027, 5, 12, 13, 30), "end_date": datetime(2027, 5, 16, 22, 30)},
    {"name": "OMEGA & The Karmic Body", "description": "Work with OMEGA frequencies and karmic body healing", "instructor": "Daniel Wald", "capacity": 1120, "schedule": "Multiple sessions", "prerequisites": "Sensing III", "start_date": datetime(2027, 6, 21, 13, 30), "end_date": datetime(2027, 6, 27, 22, 30)},
    {"name": "Merlin's Grace & Multi-Dimensional Healing", "description": "Access Merlin's Grace and multi-dimensional healing", "instructor": "Daniel Wald", "capacity": 1510, "schedule": "Multiple sessions", "prerequisites": "Sensing III", "start_date": datetime(2027, 7, 7, 13, 30), "end_date": datetime(2027, 7, 18, 10, 30)},
    {"name": "EarthWorks I", "description": "Work with earth frequencies and grounding", "instructor": "Daniel Wald", "capacity": 590, "schedule": "In-person at The Treehouse", "prerequisites": "Sensing I", "start_date": datetime(2027, 7, 9, 9, 30), "end_date": datetime(2027, 7, 11, 18, 30)},
    {"name": "Magical Structures (August)", "description": "Advanced magical structures work - August session", "instructor": "Daniel Wald", "capacity": 880, "schedule": "Multiple sessions", "prerequisites": "Sensing I", "start_date": datetime(2027, 8, 11, 13, 30), "end_date": datetime(2027, 8, 15, 22, 30)},
    {"name": "Karmic Intensive (September)", "description": "Intensive karmic work - September session", "instructor": "Daniel Wald", "capacity": 400, "schedule": "Multiple sessions", "prerequisites": "Sensing II", "start_date": datetime(2027, 9, 4, 13, 0), "end_date": datetime(2027, 9, 5, 22, 30)},
    {"name": "Sensing I: Psychic and Consciousness Development (September)", "description": "Sensing I - September session", "instructor": "Daniel Wald", "capacity": 210, "schedule": "Multiple sessions", "prerequisites": "None", "start_date": datetime(2027, 9, 11, 13, 30), "end_date": datetime(2027, 9, 11, 22, 30)},
    {"name": "Sensing II (September)", "description": "Sensing II - September session", "instructor": "Daniel Wald", "capacity": 590, "schedule": "Multiple sessions", "prerequisites": "Sensing I", "start_date": datetime(2027, 9, 12, 13, 30), "end_date": datetime(2027, 9, 14, 22, 30)},
    {"name": "Foundational Training (September)", "description": "Foundational training - September session", "instructor": "Daniel Wald", "capacity": 880, "schedule": "Multiple sessions", "prerequisites": "Sensing I", "start_date": datetime(2027, 9, 22, 13, 30), "end_date": datetime(2027, 9, 26, 22, 30)},
    {"name": "Magical Structures (November)", "description": "Magical structures - November session", "instructor": "Daniel Wald", "capacity": 880, "schedule": "Multiple sessions", "prerequisites": "Sensing I", "start_date": datetime(2027, 11, 10, 13, 30), "end_date": datetime(2027, 11, 14, 22, 30)},
    {"name": "Presence", "description": "Develop deep presence and awareness", "instructor": "Daniel Wald", "capacity": 590, "schedule": "Multiple sessions", "prerequisites": "Sensing II", "start_date": datetime(2027, 11, 19, 14, 30), "end_date": datetime(2027, 11, 21, 23, 0)},
    {"name": "Clearing the Kundalini Channel (November)", "description": "Kundalini clearing - November session", "instructor": "Daniel Wald", "capacity": 750, "schedule": "Multiple sessions", "prerequisites": "Sensing I", "start_date": datetime(2027, 11, 25, 11, 15), "end_date": datetime(2027, 11, 28, 19, 15)},
    {"name": "Connecting with Quinstel (Asia Dec)", "description": "Quinstel connection - Asia timezone", "instructor": "Daniel Wald", "capacity": 400, "schedule": "Multiple sessions", "prerequisites": "Sensing II", "start_date": datetime(2027, 12, 15, 14, 30), "end_date": datetime(2027, 12, 16, 23, 0)},
    {"name": "Connecting with Quinstel (US Dec)", "description": "Quinstel connection - US timezone", "instructor": "Daniel Wald", "capacity": 400, "schedule": "Multiple sessions", "prerequisites": "Sensing II", "start_date": datetime(2027, 12, 18, 9, 30), "end_date": datetime(2027, 12, 19, 18, 30)},
]

def seed_classes():
    db = SessionLocal()
    try:
        for class_data in classes_data:
            existing = db.query(Class).filter(Class.name == class_data["name"]).first()
            if not existing:
                new_class = Class(**class_data)
                db.add(new_class)
                print(f"✅ Added: {class_data['name']}")
            else:
                print(f"⏭️  Skipped (exists): {class_data['name']}")

        db.commit()
        print(f"\n✅ Successfully seeded {len(classes_data)} classes!")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_classes()

