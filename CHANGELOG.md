# Changelog

## v1.1.0 - 2026-11-17

Fixes from a test run by a new user on Windows 11 (Python 3.12 in a project `.venv`).

- **Udemy quiz sheet.** The build now also writes `udemy-quiz.md`: every question laid out in the order of the Udemy quiz screen (question, answers, explanation, correct answer, related lecture), with the answers in a spread-out order, ready to paste by hand. True/false becomes a two-answer question; matching, fill-in and short-answer items are listed at the end, because Udemy lecture quizzes are multiple choice only. Udemy publishes no import format for lecture quizzes, and the practice test CSV template is only available inside the instructor dashboard, so no import file is guessed. Sources and the date they were checked: `references/udemy-export.md`.
- New optional item fields: `option_feedback` (one explanation per option, kept with its option through the shuffle; checked for one non-empty text per option) and `udemy_description` (the quiz description line).
- **Windows install.** README has PowerShell commands next to the bash ones for both installs (personal and one project), plus how to check that Claude Code sees the skill and how to update it.
- **Virtual environments.** README shows how to make a project `.venv` and install the requirements into it (bash and PowerShell). SKILL.md tells Claude to run the script with the project's `.venv` Python when there is one.
- All other outputs are unchanged: rebuilding the example gives byte-identical Markdown, GIFT, CSV and check report.

## v1.0.0 - 2026-11-12

First public release.
