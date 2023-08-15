import pytest
from app.render import Context

_ctx = None


@pytest.fixture(scope="function")
def ctx():
    ctx = _get_context()
    return ctx


def _get_context():
    global _ctx
    if _ctx is None:
        _ctx = Context()
    return _ctx
