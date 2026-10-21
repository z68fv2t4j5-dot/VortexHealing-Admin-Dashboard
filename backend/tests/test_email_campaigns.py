from app.api.email_campaigns import filter_students_by_tags_and_lists
from app.models import EmailRecipient

CAMPAIGN = {"title": "T", "subject": "S", "body": "B"}


def emails(students):
    return sorted(s.email for s in students)


def test_no_filters_returns_every_student_with_an_email(db):
    assert emails(filter_students_by_tags_and_lists(db, "", "")) == [
        "ana@example.com", "ben@example.com", "cal@example.com"]


def test_list_filter_ignores_case_and_spacing(db):
    assert emails(filter_students_by_tags_and_lists(db, "", " apac wizards ")) == [
        "ana@example.com", "cal@example.com"]


def test_tags_and_lists_must_both_match(db):
    assert emails(filter_students_by_tags_and_lists(db, "Active", "APAC Wizards")) == ["ana@example.com"]


def test_any_one_of_several_tags_matches(db):
    assert emails(filter_students_by_tags_and_lists(db, "SRA,Nope", "")) == ["ana@example.com"]


def test_preview_counts_and_samples(client):
    data = client.post("/api/email/preview", json={**CAMPAIGN, "recipient_lists": "APAC Wizards"}).json()
    assert data["total_recipients"] == 2
    assert {r["email"] for r in data["sample_recipients"]} == {"ana@example.com", "cal@example.com"}
    assert data["sample_recipients"][0]["name"] == "Ana One"


def test_create_then_send_marks_sent_and_records_recipients(client, db):
    created = client.post("/api/email/campaigns", json={**CAMPAIGN, "recipient_tags": "Active"}).json()
    assert created["status"] == "draft"
    assert created["recipient_count"] == 2

    # campaign_id is a query parameter, which is how Email.tsx calls it
    sent = client.post("/api/email/send", params={"campaign_id": created["id"]}).json()
    assert sent["recipients_count"] == 2

    listed = client.get("/api/email/campaigns").json()
    assert [c["status"] for c in listed] == ["sent"]
    assert db.query(EmailRecipient).filter_by(campaign_id=created["id"]).count() == 2


def test_send_unknown_campaign_reports_error(client):
    assert client.post("/api/email/send", params={"campaign_id": 999}).json() == {"error": "Campaign not found"}


def test_filter_endpoint_returns_matches(client):
    data = client.get("/api/students/filter", params={"lists": "Global Wizards"}).json()
    assert data["count"] == 1
    assert data["students"][0]["email"] == "ben@example.com"


def test_options_offer_only_the_apac_list_and_its_full_word_class_tags(client):
    # Omega is on a Global Wizards student only; SRA, 26-01-S1 and MS-Cert are not class names
    assert client.get("/api/email/options").json() == {
        "lists": ["APAC Wizards"], "tags": ["Foundational", "Sensing I"]}
