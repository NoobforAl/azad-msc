"""Enrollment statistics for the Course Registration Platform (analytics service stub)."""

from typing import Dict, Iterable, List, Tuple


def fill_rate(enrolled: int, capacity: int) -> float:
    """Return enrolled / capacity as a number in [0, 1]. A course with no capacity is 0.0."""
    if capacity <= 0:
        return 0.0
    return min(enrolled / capacity, 1.0)


def fullest_courses(rows: Iterable[Tuple[str, int, int]], top: int = 3) -> List[Tuple[str, float]]:
    """Rank (course_id, enrolled, capacity) rows by fill rate, highest first."""
    rates: Dict[str, float] = {course_id: fill_rate(enrolled, capacity) for course_id, enrolled, capacity in rows}
    return sorted(rates.items(), key=lambda item: (-item[1], item[0]))[:top]


if __name__ == "__main__":
    sample = [("SE101", 38, 40), ("SE102", 10, 35), ("SE103", 20, 20)]
    for course_id, rate in fullest_courses(sample):
        print(f"{course_id}: {rate:.0%}")
