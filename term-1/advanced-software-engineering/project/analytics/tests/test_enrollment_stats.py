import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from enrollment_stats import fill_rate, fullest_courses  # noqa: E402


class FillRateTest(unittest.TestCase):
    def test_half_full(self) -> None:
        self.assertEqual(fill_rate(10, 20), 0.5)

    def test_zero_capacity_is_zero(self) -> None:
        self.assertEqual(fill_rate(5, 0), 0.0)

    def test_overbooked_is_capped(self) -> None:
        self.assertEqual(fill_rate(25, 20), 1.0)


class FullestCoursesTest(unittest.TestCase):
    def test_ranks_by_fill_rate_then_id(self) -> None:
        rows = [("B", 10, 20), ("A", 10, 20), ("C", 20, 20)]
        self.assertEqual(fullest_courses(rows, top=2), [("C", 1.0), ("A", 0.5)])


if __name__ == "__main__":
    unittest.main()
