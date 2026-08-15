import os

os.environ["DATABASE_URL"] = "sqlite:///./test_qc.db"
os.environ["DEEPSEEK_API_KEY"] = "test-key"

import pytest
from sqlalchemy.orm import Session

from app.core.db import Base, SessionLocal, engine
from app.models import new_id


@pytest.fixture(autouse=True)
def _clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def sample_agent(db: Session):
    from app.models import Agent

    agent = Agent(name="demo", mcp_url="http://localhost:8000/mcp", api_key_hash="h")
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent