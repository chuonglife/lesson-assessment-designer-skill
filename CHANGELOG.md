# Changelog

## v1.1.3 - 2026-11-19

- **English is the default output language,** stated in SKILL.md: another language only when the user asks for it or the material is in it. The docs no longer show a Vietnamese language code as an example, so nobody reads it as a supported option.

## v1.1.2 - 2026-11-19

The repository is now in English only. The Vietnamese sources stay in the credits, with their titles in English.

- **Vietnamese output mode removed.** Headings and instructions are built in English only. The label table keeps its structure with one set, `en`, so another language can be added with the same keys. Any `language` other than `en` is a blocking error that names the fix (set `"en"`, or add a label set to `L`), exit code 1, no traceback. Items can still be written in any language.
- The Vietnamese giveaway words, banned options, stock phrases and negation words are gone from the checks, along with the comma decimal separator and the Times New Roman font that came with that mode.
- README: the Vietnamese prompt example is replaced with an English one, and "Can it write tests in other languages?" says what the script does now. SKILL.md tells Claude to keep `language` at `en`. Source titles in the credits are in English and unaccented; the grade-band citation (Circular 04/2022/TT-BLDTBXH) moved from the main text of `references/test-design-process.md` to its Sources line and to the README credits.
- A `language` that is not text (for example a list) gave a traceback; it is now one `ERROR` line.
- English output is unchanged: rebuilding the example gives byte-identical Markdown, GIFT, CSV, Udemy sheet and check report.

## v1.1.1 - 2026-11-19

Fixes from an audit that followed README on a clean Windows 11 machine and fed the script broken input.

- **Vietnamese labels no longer crash in a Windows pipe.** With the Vietnamese labels of that time, or an accented name inside an error message, the script died with `UnicodeEncodeError` when its output was piped (Git Bash, Claude Code). It now prints in UTF-8 on every system; `-X utf8` is no longer needed.
- **Missing `python-docx` is said out loud.** The build used to skip the Word files in silence and still print "Built". It now warns, names the Python it ran with and prints the exact install command, on the console and in `_check/check-report.md`. SKILL.md tells Claude what to do with that warning.
- **Broken input gets a message, not a traceback.** A file that is missing or not valid JSON, an item without `id`, an objective without `code`, a topic without `name`, an assignment without `title`, points written as text, a `scoring` entry without `point`: each is one `ERROR` line that names the item and the field, exit code 1. A JSON saved with a byte order mark (Windows PowerShell does that) is read normally. Numbers typed without quotes as options or accepted answers (`[10, 20, 30, 40]`) are read as text.
- **`quiz.gift` says what it leaves out.** One warning names every item the GIFT file cannot carry in full: a two-blank fill-in (left out, GIFT takes one blank per question), matching (correct pairs only) and short answer (an essay question without its scoring points). Matching and one-blank fill-in now carry the explanation as feedback. A `->` inside a question or option is written as an arrow character, because Moodle reads `=` together with `->` as a matching question. README and SKILL.md describe the file as it is.
- **Fewer false alarms.** An option is banned only when the whole option is "all of the above", "both A and B" and the like, so "Group A and B together" passes. "May" with a capital is read as the month in a true/false statement.
- **Install.** README starts with "Before you start": Git, Python and Claude Code with links, install commands and the commands to check them. The project `.venv` is now the main install path (system Python refuses `pip install` on current Debian, Ubuntu and Homebrew). Notes for Git Bash on Windows and for "Filename too long" in deep folders.
- The note about a shuffle that could not spread the answer letters is now a counted warning in the check report. `--help` shows an example and the list of outputs. The built message says "1 assignment".
- Example: `quiz.gift` gains feedback on the matching item and a comment on the short answer; the check report gains the GIFT warning (4 warnings instead of 3). All other outputs are byte-identical.
- **Example in step with Lesson Content Writer v1.2.0.** The example lesson there now has 7 videos (the close is its own video), so `01_Learning_Objectives.md` is the new copy and one item's review source reads "Video 7 close". The Claude app install steps name the current menu path and say that code execution must be on.

## v1.1.0 - 2026-11-17

Fixes from a test run by a new user on Windows 11 (Python 3.12 in a project `.venv`).

- **Udemy quiz sheet.** The build now also writes `udemy-quiz.md`: every question laid out in the order of the Udemy quiz screen (question, answers, explanation, correct answer, related lecture), with the answers in a spread-out order, ready to paste by hand. True/false becomes a two-answer question; matching, fill-in and short-answer items are listed at the end, because Udemy lecture quizzes are multiple choice only. Udemy publishes no import format for lecture quizzes, and the practice test CSV template is only available inside the instructor dashboard, so no import file is guessed. Sources and the date they were checked: `references/udemy-export.md`.
- New optional item fields: `option_feedback` (one explanation per option, kept with its option through the shuffle; checked for one non-empty text per option) and `udemy_description` (the quiz description line).
- **Windows install.** README has PowerShell commands next to the bash ones for both installs (personal and one project), plus how to check that Claude Code sees the skill and how to update it.
- **Virtual environments.** README shows how to make a project `.venv` and install the requirements into it (bash and PowerShell). SKILL.md tells Claude to run the script with the project's `.venv` Python when there is one.
- All other outputs are unchanged: rebuilding the example gives byte-identical Markdown, GIFT, CSV and check report.

## v1.0.0 - 2026-11-12

First public release.
