import pandas as pd
import json
import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import Base, GlobalStudent

CONTACTS_FOLDER = "/Users/djw/Documents/VortexHealing Assistant Docs/All Global Contacts"

def seed_global_students():
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Get all CSV files in the folder
    csv_files = [f for f in os.listdir(CONTACTS_FOLDER) if f.endswith('.csv')]

    if not csv_files:
        print("No CSV files found in All Global Contacts folder")
        return

    db = SessionLocal()

    try:
        for csv_file in csv_files:
            filepath = os.path.join(CONTACTS_FOLDER, csv_file)
            print(f"Importing {csv_file}...")

            # Read CSV with proper column mapping and encoding handling
            try:
                df = pd.read_csv(filepath, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(filepath, encoding='latin-1')
                except UnicodeDecodeError:
                    df = pd.read_csv(filepath, encoding='iso-8859-1')

            # Clear existing data
            db.query(GlobalStudent).delete()
            db.commit()

            imported_count = 0
            skipped_count = 0
            seen_emails = set()

            for _, row in df.iterrows():
                # Extract key contact fields
                first_name = str(row.get('first', '')).strip()
                last_name = str(row.get('last', '')).strip()
                email = str(row.get('email', '')).strip()

                if not first_name and not last_name:
                    continue

                # Skip if email is empty or not valid
                if not email or email == 'nan' or '@' not in str(email):
                    email = f"{first_name.lower()}.{last_name.lower()}@unknown.local"

                # Skip if we've already seen this email in this batch
                if email in seen_emails:
                    skipped_count += 1
                    continue

                seen_emails.add(email)

                # Extract main contact fields
                address_1 = str(row.get('add1', '')).strip()
                if address_1 == 'nan':
                    address_1 = None

                address_2 = str(row.get('add2', '')).strip()
                if address_2 == 'nan':
                    address_2 = None

                city = str(row.get('City', '')).strip()
                if city == 'nan':
                    city = None

                state = str(row.get('State', '')).strip()
                if state == 'nan':
                    state = None

                zip_code = str(row.get('ZIP', '')).strip()
                if zip_code == 'nan':
                    zip_code = None

                country = str(row.get('country', '')).strip()
                if country == 'nan':
                    country = None

                notes = str(row.get('notes', '')).strip()
                if notes == 'nan':
                    notes = None

                # Store all data as JSON for searchability
                all_data = {}
                for col in df.columns:
                    val = str(row.get(col, '')).strip()
                    if val and val != 'nan':
                        all_data[col] = val

                # Create GlobalStudent record
                global_student = GlobalStudent(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    address_1=address_1,
                    address_2=address_2,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    country=country,
                    notes=notes,
                    all_data=json.dumps(all_data)
                )

                db.add(global_student)
                imported_count += 1

                if imported_count % 100 == 0:
                    print(f"  Imported {imported_count} records...")

            db.commit()
            print(f"✓ Successfully imported {imported_count} global students from {csv_file} (skipped {skipped_count} duplicates)")

    except Exception as e:
        db.rollback()
        print(f"✗ Error importing global students: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    seed_global_students()
