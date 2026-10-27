"""Unit tests for domain scoring logic."""

from qnagym.contracts.types import Alternative, Progress
from qnagym.domain.scoring import (
    calculate_progress_trend,
    format_score,
    get_close_alternatives,
    should_display_confidence,
)


class TestDisplayRules:
    def test_should_display_confidence(self):
        assert should_display_confidence(0.94) is True
        assert should_display_confidence(0.95) is False
        assert should_display_confidence(0.99) is False

    def test_get_close_alternatives(self):
        alts = [
            Alternative(summary="a", score=0.8),
            Alternative(summary="b", score=0.76),
            Alternative(summary="c", score=0.7),
        ]
        close = get_close_alternatives(0.8, alts)
        assert len(close) == 2
        assert close[0].summary == "a"
        assert close[1].summary == "b"

    def test_calculate_progress_trend(self):
        # Starting
        p = Progress(attempts=0)
        assert calculate_progress_trend(p) == "➡️"

        p = Progress(attempts=1)
        assert calculate_progress_trend(p) == "➡️"

        # Improving
        p = Progress(attempts=2, last_score=0.8, best_score=0.8, improving=True)
        assert calculate_progress_trend(p) == "📈"

        # Stable at best
        p = Progress(attempts=3, last_score=0.9, best_score=0.9, improving=False)
        assert calculate_progress_trend(p) == "➡️"

        # Declining
        p = Progress(attempts=3, last_score=0.7, best_score=0.9, improving=False)
        assert calculate_progress_trend(p) == "📉"

    def test_format_score(self):
        assert format_score(0.0) == "0%"
        assert format_score(0.5) == "50%"
        assert format_score(0.75) == "75%"
        assert format_score(1.0) == "100%"
        assert format_score(0.333) == "33%"
