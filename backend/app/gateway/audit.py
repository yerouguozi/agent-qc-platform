import uuid

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_audit(
    db: Session,
    agent_id: str | None,
    action: str,
    source: str = "",
    result: str = "",
) -> str:
    request_id = uuid.uuid4().hex
    db.add(AuditLog(agent_id=agent_id, action=action, request_id=request_id, source=source, result=result))
    db.commit()
    return request_id