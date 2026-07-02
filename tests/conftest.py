import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from auction_tracker.models import Base


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with factory() as s:
        yield s
    Base.metadata.drop_all(engine)
