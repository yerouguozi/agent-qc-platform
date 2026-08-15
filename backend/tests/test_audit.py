from sqlalchemy.orm import Session

from app.gateway.audit import log_audit
from app.models import AuditLog


def test_log_audit_creates_row(db: Session, sample_agent):
    request_id = log_audit(db, sample_agent.id, "call:query_sql", source="api", result="success")
    assert request_id
    row = db.query(AuditLog).filter(AuditLog.request_id == request_id).first()
    assert row.agent_id == sample_agent.id
    assert row.action == "call:query_sql"
    assert row.result == "success"