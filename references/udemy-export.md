# Udemy export: what Udemy accepts and how `udemy-quiz.md` maps to it

Read this when the test is for a Udemy course, or when the user asks how to get the quiz onto Udemy.

## Contents

1. What was checked, and where
2. The short answer for the user
3. How `udemy-quiz.md` maps to the Udemy quiz screen
4. Writing a test that fits Udemy
5. Practice tests

## 1. What was checked, and where

Checked on 2026-11-17 against Udemy's own pages only. Community forum posts and third-party blogs were not used as a source for any format.

| Source | What it says that matters here |
|---|---|
| Udemy Teaching Center, "Enhancing learning with practice and assessment", https://teach.udemy.com/course-creation/plan-your-practice-activities/ | Quizzes are a series of simple multiple-choice questions; a good quiz explains the answer. No import or bulk upload is mentioned for quizzes. |
| Udemy Teaching Center, "Instructor guide to creating practice tests", https://teach.udemy.com/instructor-guide-practice-tests/ | Practice test question types: multiple choice, multi-select, fill in the blank. An explanation per answer choice is recommended for multiple choice. Practice tests can link a lecture and/or a resource; quizzes can link only a related lecture. Up to 2 practice tests in a regular course, 6 in a practice-test-only course. The guide describes writing questions one by one and does not describe any file format. |
| Udemy Help Center, practice test bulk upload article, https://support.udemy.com/hc/articles/4993998520215 | Listed in search results as Udemy's article on bulk uploading practice test questions from a CSV template that is downloaded inside the practice test editor; it notes a newer template replacing an older one (from 2 May 2024). On 2026-11-17 the page answered 403 to automated requests and redirected the browser to the new help site (success.udemy.com) home page, so its column list could not be read. |
| Udemy Help Center, "Create a multiple choice quiz", https://support.udemy.com/hc/articles/229231627 | Listed in search results: questions are added one at a time; a Related Lecture can be chosen and shows to students after they answer. Same 403 on 2026-11-17. |

What this means:

- **Lecture quizzes: no import file.** Nothing official describes one. The quiz is typed or pasted into the Udemy editor question by question.
- **Practice tests: a CSV bulk upload exists**, but the column layout lives only in the template file inside the instructor dashboard and has changed at least once. It is not published, so the script does not write that CSV. Guessing the columns would give learners a file that fails on upload.
- **Limits**: none of the pages above states a character limit or a maximum number of answers for quiz questions, so the script adds no length or answer-count check for Udemy. The one rule that is stated, "multiple choice only", is applied: other item types are left out of the Udemy sheet and listed.

Re-check these pages before relying on this file after 2027; Udemy moves its help articles.

## 2. The short answer for the user

"Udemy has no import for lecture quizzes. Open `udemy-quiz.md`, and for each block paste the question, the answers and the explanation into the Udemy quiz editor, tick the correct answer and choose the related lecture."

## 3. How `udemy-quiz.md` maps to the Udemy quiz screen

| In `udemy-quiz.md` | Udemy field | From `assessment.json` |
|---|---|---|
| Quiz title | Quiz title | `test_title` |
| Quiz description | Quiz description | `udemy_description` (optional) |
| Question | Question | `stem` |
| Answer 1, 2, ... | One answer box each | `options`, in form A's shuffled order so the keys are spread out |
| Explanation under each answer | The explanation box under that answer | `option_feedback[i]` if given, else the item's `explanation` (paste it under every answer) |
| Correct answer | The radio button of that answer | `answer` |
| Related lecture | Related lecture drop-down | `source` (name the lecture there) |

True/false items become two-answer questions (True, False). Matching, fill-in-the-blank and short-answer items are listed under "Not in this quiz" with their objective, for the author to rewrite as multiple choice or to mark in the assignment. The assignment goes into a Udemy Assignment curriculum item: paste the task and the marking tool from `04_Assignment_and_Rubric.md`.

The explanation under an answer is feedback for the learner who just picked it. `option_feedback` lets each answer say exactly why it is right or wrong:

```json
"option_feedback": [
  "Right. Understanding happens in the head; only what the learner does can be watched.",
  "The topic size is not the problem; a small topic with the verb 'understand' fails the same way.",
  "The textbook is a condition, not the behaviour; the line still has nothing to observe.",
  "Time is a standard, which is optional; the missing piece is an observable verb."
]
```

## 4. Writing a test that fits Udemy

- Multiple choice is the only lecture-quiz type, so a Udemy quiz is mostly `mcq` items; true/false works as a two-answer question.
- Skill objectives go to the assignment, as they would anyway.
- Name the lecture in `source` ("Lecture 4: The observer test, at 3:10") so the related-lecture choice is obvious.
- Udemy quizzes are formative: 5 to 10 items after a section is the usual size.

## 5. Practice tests

Practice tests are for certification-style exam practice in paid courses. If the user wants one, build the test as usual, then tell them to download the current CSV template from the practice test's bulk upload option and fill it from `questions.csv` or `udemy-quiz.md`; the explanations and the related lecture are already written. Do not invent the template's columns.
