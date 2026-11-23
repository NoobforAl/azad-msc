"""Unit tests for check_commit_msgs.check_message. Run: python -m unittest test_check_commit_msgs -v"""

import unittest
from typing import List

import check_commit_msgs as ccm

NAME = "Lab Student"
EMAIL = "student@example.com"
SIGN = "Signed-off-by: Lab Student <student@example.com>"


def rules(message: str) -> List[str]:
    return [v.rule for v in ccm.check_message(message, NAME, EMAIL)]


class CheckMessage(unittest.TestCase):
    def test_good_message_has_no_violation(self) -> None:
        self.assertEqual(rules("catalog: add Count\n\nExplain why.\n\n" + SIGN + "\n"), [])

    def test_empty_subject(self) -> None:
        self.assertEqual(rules("\n\nbody\n"), ["S1"])

    def test_subject_too_long(self) -> None:
        self.assertEqual(rules("catalog: " + "x" * 70 + "\n\n" + SIGN), ["S2"])

    def test_subject_period_and_missing_area(self) -> None:
        self.assertEqual(rules("Fixed stuff.\n\n" + SIGN), ["S3", "S4"])

    def test_revert_subject_is_allowed(self) -> None:
        self.assertEqual(rules('Revert "catalog: add Count"\n\nThis reverts it.\n\n' + SIGN), [])

    def test_no_blank_line_before_body(self) -> None:
        self.assertEqual(rules("catalog: add Count\nbody starts too early\n\n" + SIGN), ["B1"])

    def test_long_body_line_is_reported_once(self) -> None:
        self.assertEqual(rules("catalog: add Count\n\n" + "word " * 20 + "\n" + "word " * 20 + "\n\n" + SIGN), ["B2"])

    def test_long_url_and_indented_code_are_exempt(self) -> None:
        body = "see https://example.com/" + "a" * 90 + "\n    " + "b" * 90
        self.assertEqual(rules("catalog: add Count\n\n" + body + "\n\n" + SIGN), [])

    def test_missing_signoff(self) -> None:
        self.assertEqual(rules("catalog: add Count\n\nbody\n"), ["T1"])

    def test_signoff_of_someone_else(self) -> None:
        self.assertEqual(rules("catalog: add Count\n\nSigned-off-by: Other Person <other@example.com>\n"), ["T2"])

    def test_comment_lines_are_ignored(self) -> None:
        self.assertEqual(rules("catalog: add Count\n\n# Please enter the commit message\n" + SIGN), [])


if __name__ == "__main__":
    unittest.main()
