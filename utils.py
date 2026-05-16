def format_duration(seconds: int) -> str:
    """Convert seconds to human-readable duration string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


# Unit tests
def test_format_duration_seconds():
    """Test formatting for durations under 60 seconds."""
    assert format_duration(0) == "0s"
    assert format_duration(30) == "30s"
    assert format_duration(59) == "59s"
    print("[PASS] All seconds tests passed")


def test_format_duration_minutes_and_hours():
    """Test formatting for minutes and hours."""
    # Minutes
    assert format_duration(60) == "1m 0s"
    assert format_duration(90) == "1m 30s"
    assert format_duration(3599) == "59m 59s"
    
    # Hours
    assert format_duration(3600) == "1h 0m"
    assert format_duration(3661) == "1h 1m"
    assert format_duration(7200) == "2h 0m"
    assert format_duration(7320) == "2h 2m"
    print("[PASS] All minutes and hours tests passed")


if __name__ == "__main__":
    test_format_duration_seconds()
    test_format_duration_minutes_and_hours()
    print("\n[SUCCESS] All tests passed!")

# Made with Bob
