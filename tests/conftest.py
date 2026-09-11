from __future__ import annotations

import pytest
from fakes import FakeProvider


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()
