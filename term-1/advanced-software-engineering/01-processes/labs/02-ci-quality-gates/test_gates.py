"""Unit tests for the pure parts of gates.py. Run: python -m unittest test_gates -v"""

import unittest

import gates

COVER_FUNC = (
    "example.com/registration/internal/catalog/catalog.go:19:\tNew\t\t100.0%\n"
    "example.com/registration/cmd/registration-api/main.go:35:\tmain\t\t0.0%\n"
    "total:\t\t\t\t\t\t\t\t(statements)\t72.4%\n"
)


class ParseTotalCoverage(unittest.TestCase):
    def test_reads_total_line(self) -> None:
        self.assertEqual(gates.parse_total_coverage(COVER_FUNC), 72.4)

    def test_returns_none_without_total(self) -> None:
        self.assertIsNone(gates.parse_total_coverage("no coverage here\n"))

    def test_ignores_per_function_lines(self) -> None:
        self.assertIsNone(gates.parse_total_coverage("a.go:1:\tF\t\t100.0%\n"))


class LastLines(unittest.TestCase):
    def test_keeps_only_the_tail_and_skips_blank_lines(self) -> None:
        self.assertEqual(gates.last_lines("a\n\nb\nc\nd\n", 2), "c | d")


class FailureLines(unittest.TestCase):
    def test_picks_failing_test_names(self) -> None:
        text = "setup\nFAIL: test_a (x.Y)\nnoise\nERROR: test_b (x.Y)\n"
        self.assertEqual(gates.failure_lines(text, ("FAIL:", "ERROR:")), "FAIL: test_a (x.Y) | ERROR: test_b (x.Y)")

    def test_falls_back_to_the_tail(self) -> None:
        self.assertEqual(gates.failure_lines("a\nb\nc\nd\n", ("FAIL:",)), "b | c | d")


if __name__ == "__main__":
    unittest.main()
