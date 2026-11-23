## Problem

<!-- What is wrong or missing, and why is it worth fixing? Link the issue. -->

## Impact

<!-- What does a user, a caller or an operator notice? -->

## Change

<!-- What did you change, in two or three sentences? Anything the reviewer should look at first? -->

## How I tested it

<!-- Commands and results. For a bug fix: the test that fails without the change. -->

## Author checklist

- [ ] One logical change; the pull request is small enough to read in one sitting
- [ ] Every commit message follows CONTRIBUTING.md section 3 (`python tools/check_commit_msgs.py origin/main..HEAD` is clean)
- [ ] Every commit has `Signed-off-by:` (`git commit -s`)
- [ ] `python tools/gates.py` is green (gofmt, go vet, ruff, tests, coverage)
- [ ] New or changed behaviour has a test; a bug fix has a test that fails without the fix
- [ ] Documentation and `CHANGELOG.md` updated where behaviour changed
- [ ] If this repairs a broken release: the commit has `Fixes-release: <tag>`

## Reviewer checklist

- [ ] I understand what the change does and why; the description answers it
- [ ] The change is justified on its own merits, and does one thing
- [ ] Tests would fail if the change were wrong; error paths are tested
- [ ] Names, comments and structure match the surrounding code
- [ ] No secrets, no debug output, no unrelated reformatting
- [ ] Public behaviour changes are documented and backwards compatible, or the break is called out
- [ ] I have said which comments block the merge and which are suggestions
