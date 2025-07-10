"""
Tests for the retention policy module.
"""

import datetime
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from timeless_py.engine import Snapshot
from timeless_py.retention import RetentionEvaluator, RetentionPolicy


def test_retention_policy_default() -> None:
    """Test that default retention policy is created correctly."""
    policy = RetentionPolicy()

    # Check default values
    assert policy.hourly == 24
    assert policy.daily == 7
    assert policy.weekly == 4
    assert policy.monthly == 12
    assert policy.yearly == 3
    assert policy.exclude_patterns == []


def test_retention_policy_from_dict() -> None:
    """Test creating retention policy from dictionary."""
    policy_dict = {
        "hourly": 12,
        "daily": 14,
        "weekly": 8,
        "monthly": 6,
        "yearly": 2,
        "exclude_patterns": ["*.tmp", "node_modules/"],
    }

    policy = RetentionPolicy.from_dict(policy_dict)

    assert policy.hourly == 12
    assert policy.daily == 14
    assert policy.weekly == 8
    assert policy.monthly == 6
    assert policy.yearly == 2
    assert policy.exclude_patterns == ["*.tmp", "node_modules/"]


def test_retention_policy_from_yaml(tmp_path: Path) -> None:
    """Test creating retention policy from YAML file."""
    yaml_content = """
    hourly: 12
    daily: 14
    weekly: 8
    monthly: 6
    yearly: 2
    exclude_patterns:
      - "*.tmp"
      - "node_modules/"
    """

    yaml_file = tmp_path / "policy.yaml"
    yaml_file.write_text(yaml_content)

    policy = RetentionPolicy.from_file(str(yaml_file))

    assert policy.hourly == 12
    assert policy.daily == 14
    assert policy.weekly == 8
    assert policy.monthly == 6
    assert policy.yearly == 2
    assert policy.exclude_patterns == ["*.tmp", "node_modules/"]


def test_retention_evaluator_basic() -> None:
    """Test basic retention evaluation."""
    now = datetime.datetime.now(datetime.timezone.utc)

    # Create snapshots at different times
    snapshots = [
        # Hourly snapshots for the last 48 hours
        *[
            Snapshot(
                id=f"hourly-{i}",
                time=now - datetime.timedelta(hours=i),
                hostname="test-host",
                paths=["/home/user"],
                tags=["test"],
                metadata={},
            )
            for i in range(1, 49)
        ],
        # Daily snapshots for the last 14 days
        *[
            Snapshot(
                id=f"daily-{i}",
                time=now - datetime.timedelta(days=i),
                hostname="test-host",
                paths=["/home/user"],
                tags=["test"],
                metadata={},
            )
            for i in range(1, 15)
        ],
        # Weekly snapshots for the last 8 weeks
        *[
            Snapshot(
                id=f"weekly-{i}",
                time=now - datetime.timedelta(weeks=i),
                hostname="test-host",
                paths=["/home/user"],
                tags=["test"],
                metadata={},
            )
            for i in range(1, 9)
        ],
        # Monthly snapshots for the last 12 months
        *[
            Snapshot(
                id=f"monthly-{i}",
                time=now - datetime.timedelta(days=i * 30),
                hostname="test-host",
                paths=["/home/user"],
                tags=["test"],
                metadata={},
            )
            for i in range(1, 13)
        ],
        # Yearly snapshots for the last 5 years
        *[
            Snapshot(
                id=f"yearly-{i}",
                time=now - datetime.timedelta(days=i * 365),
                hostname="test-host",
                paths=["/home/user"],
                tags=["test"],
                metadata={},
            )
            for i in range(1, 6)
        ],
    ]

    # Create policy
    policy = RetentionPolicy(hourly=24, daily=7, weekly=4, monthly=6, yearly=3)

    # Evaluate retention
    evaluator = RetentionEvaluator(policy)
    to_keep, to_forget = evaluator.evaluate(snapshots)

    # Check that we're keeping the right number of snapshots
    assert (
        len(to_keep) == 24 + 7 + 4 + 6 + 3
    )  # hourly + daily + weekly + monthly + yearly

    # Check that we're forgetting the rest
    assert len(to_forget) == len(snapshots) - len(to_keep)


@given(
    hourly=st.integers(min_value=0, max_value=100),
    daily=st.integers(min_value=0, max_value=100),
    weekly=st.integers(min_value=0, max_value=100),
    monthly=st.integers(min_value=0, max_value=100),
    yearly=st.integers(min_value=0, max_value=100),
)
def test_retention_policy_property_based(
    hourly: int, daily: int, weekly: int, monthly: int, yearly: int
) -> None:
    """Test retention policy with property-based testing."""
    policy = RetentionPolicy(
        hourly=hourly, daily=daily, weekly=weekly, monthly=monthly, yearly=yearly
    )

    assert policy.hourly == hourly
    assert policy.daily == daily
    assert policy.weekly == weekly
    assert policy.monthly == monthly
    assert policy.yearly == yearly
