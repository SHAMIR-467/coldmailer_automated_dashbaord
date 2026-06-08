import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("SUPABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
os.environ.setdefault("SUPABASE_KEY", "postgres")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.get.return_value = None
    redis.incr.return_value = 1
    redis.expire.return_value = True
    redis.delete.return_value = 1
    return redis
