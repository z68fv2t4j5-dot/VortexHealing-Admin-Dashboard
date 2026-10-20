from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import GlobalStudent
import pandas as pd
import json
import os

router = APIRouter()

CONTACTS_FOLDER = "/Users/djw/Documents/VortexHealing Assistant Docs/All Global Contacts"

@router.post("/admin/refresh-global-contacts")
async def refresh_global_contacts(db: Session = Depends(get_db)):
    """Refresh global contacts from CSV without restarting server"""
    csv_files = [f for f in os.listdir(CONTACTS_FOLDER) if f.endswith('.csv')]

    if not csv_files:
        return {"status": "error", "message": "No CSV files found"}

    try:
        for csv_file in csv_files:
            filepath = os.path.join(CONTACTS_FOLDER, csv_file)

            # Read CSV with encoding handling
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
            seen_emails = set()

            for _, row in df.iterrows():
                first_name = str(row.get('first', '')).strip()
                last_name = str(row.get('last', '')).strip()
                email = str(row.get('email', '')).strip()

                if not first_name and not last_name:
                    continue

                if not email or email == 'nan' or '@' not in str(email):
                    email = f"{first_name.lower()}.{last_name.lower()}@unknown.local"

                if email in seen_emails:
                    continue

                seen_emails.add(email)

                # Extract main contact fields
                address_1 = str(row.get('add1', '')).strip() or None
                address_2 = str(row.get('add2', '')).strip() or None
                city = str(row.get('City', '')).strip() or None
                state = str(row.get('State', '')).strip() or None
                zip_code = str(row.get('ZIP', '')).strip() or None
                country = str(row.get('country', '')).strip() or None
                notes = str(row.get('notes', '')).strip() or None

                # Store all data as JSON
                all_data = {}
                for col in df.columns:
                    val = str(row.get(col, '')).strip()
                    if val and val != 'nan':
                        all_data[col] = val

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

            db.commit()

        return {
            "status": "success",
            "message": f"Refreshed global contacts. Imported {imported_count} records",
            "count": imported_count
        }

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
