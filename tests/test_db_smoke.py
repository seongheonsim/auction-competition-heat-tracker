from sqlalchemy import text

from auction_tracker.db import make_engine, make_session_factory


def test_engine_executes_scalar():
    engine = make_engine("sqlite://")
    factory = make_session_factory(engine)
    with factory() as s:
        assert s.execute(text("select 1")).scalar_one() == 1
