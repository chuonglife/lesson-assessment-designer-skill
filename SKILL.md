---
name: lesson-assessment-designer
description: Design the quiz, test and assignment for ONE lesson straight from its learning objectives, using a test blueprint (table of specifications) on Bloom's levels - multiple choice, true/false, matching, fill-in-the-blank and short-answer items, plus a practical assignment with a checklist or analytic rubric for skill objectives. Writes assessment.json; a script checks every item against item-writing rules (one key, no "all of the above", no giveaway words, every objective covered) and builds the blueprint, two shuffled forms with answer sheets (Markdown + Word), an answer key with feedback for every option, the rubric, a Moodle GIFT file and a CSV. Use it whenever the user wants a quiz, test, exam, question bank, knowledge check, end-of-module test, assignment, rubric or marking guide for a lesson, class, training or online course (Udemy, Teachable, Moodle, any LMS), even if they only paste the objectives or the lesson and say "make the quiz".
---

# Lesson Assessment Designer

Turns **the learning objectives of one lesson** (and the lesson itself) into **an assessment pack a teacher can use tomorrow**: a test blueprint, a test in two shuffled forms, an answer key that explains every option, and a practical assignment with a checklist or rubric for the objectives a quiz cannot measure.

One sentence holds the whole skill: **no objective, no question; no question, the objective was never assessed.** Every item traces back to exactly one objective, and every objective has at least one item or one marking criterion.

## Inputs and outputs

Best input: a learning objectives file with codes (for example `01_Learning_Objectives.md` from the Lesson Content Writer skill: K1, K2 for knowledge, S1 for skills, A1 for autonomy and attitudes) plus the lesson content (`02_Lesson_Content.md`, a script, slides, a textbook section). The content gives you the facts to ask about, the examples to build scenarios from, and the **mistakes learners really make**, which become distractors.

If the user gives only lesson content, derive the objectives first, write them into `objectives[]` with measurable verbs, and list them under "Assumptions" in your report so the user can correct them. Never write items for objectives that are not there; that is how tests drift away from what was taught.

Learners: take them from the objectives file, the course brief or the user. Scenarios in items come from the learners' own working world (a teacher's class, a nurse's ward, a support agent's chat queue), never from a generic textbook world.

Output folder (default `assessments/<course-slug>/<lesson-folder>/`, or where the user asks):

| File | What it is | Made by |
|---|---|---|
| `assessment.json` | The single source: objectives, topics, items, assignments. Edit it and rebuild | You, from `templates/assessment.example.json` |
| `01_Test_Blueprint.md` | Topics x 4 cognitive levels with item counts, points and percentages; objective coverage; the lesson's assessment plan | script |
| `02_Test_Form_A.md` / `B` + `.docx` | Learner copies, parts by item type, items and options shuffled, answer sheet | script |
| `03_Answer_Key_and_Marking_Guide.md` + `.docx` | Keys per form; every item with why the answer is right and why each distractor is wrong; short-answer scoring; score conversion; what to do after marking | script |
| `04_Assignment_and_Rubric.md` + `.docx` | Task, deliverable, time, deadline, and the checklist or rubric shared with learners in advance | script |
| `quiz.gift` | Moodle GIFT import file | script |
| `questions.csv` | One row per item, for spreadsheets and LMS imports | script |
| `_check/check-report.md` | Blocking errors and warnings | script |

## The six steps

Read `references/test-design-process.md` the first time.

### Step 1. Set the purpose

`purpose` is one of `diagnostic` (before teaching, what do they already know), `formative` (a quiz after a video or section, to fix the teaching), `summative` (end of lesson or module, to certify). Purpose sets length, difficulty and pass mark: formative quizzes 5 to 10 items with a 70 to 80% pass mark; summative tests 15 to 30 items plus an assignment, pass mark as the institution sets it (often 50% in vocational systems, 80% is common for online course quizzes). Write the pass mark and the reason in `pass_mark`.

For a self-paced online course, the sensible default per lesson is **one or two formative quizzes** (5 to 10 items after the theory videos) and **one submitted assignment** with a rubric when the lesson has skill objectives. Write a summative test only when asked or when the curriculum gives the lesson a test slot. One `assessment.json` is one test; a lesson with two quizzes gets two folders (`quiz-1/`, `quiz-2/`) or one test in two parts.

### Step 2. Fix the objectives and the level of each

Copy every objective into `objectives[]` with its code and text. Read the verb and the standard, check `references/objective-levels-and-tools.md`, and give each a blueprint `level`:

- `recall`: list, name, define, state, identify, label, order
- `understand`: describe, explain, distinguish, compare, summarise, classify an example
- `apply`: use a rule or procedure in a familiar case, calculate, correct a given fault, sort given cases
- `higher-order`: analyse a new case, evaluate and choose with reasons, design, write or build a product

Skill objectives ("write", "design", "carry out", "record") and attitude or autonomy objectives are **not measured by selected-response items**. Set `measured_by: "assignment"` (or `"both"` when the test also checks the knowledge behind the skill, such as spotting the faulty step). A quiz can tell you a learner recognises a good objective; only a product tells you they can write one.

The standard inside an objective sets the item count. "At least 8/10" means that test needs 10 items on that objective (`min_items: 10`). "Name the fault in each of 10 given objectives" means a list of 10 objectives in the test.

### Step 3. Choose the format and build the blueprint

`format`: `objective` (selected-response only, the default for quizzes), `mixed` (selected-response plus short answer, for summative tests), `essay` (rare; only when every objective is higher-order and there is a human marker). In a mixed test the selected-response part is done and handed in first; points are split in proportion to the time planned for each part.

Build the blueprint with the nine moves in the process reference: list topics (usually the lesson's sections) → place each objective in its topic x level cell → share points across topics by teaching time and importance → set the total → points per topic → items per cell (every selected-response item **worth the same**) → column totals → column percentages → review. Starting ratios: formative quiz on a theory lesson about 30% recall, 40% understanding, 30% application; summative test on an integrated lesson about 20 / 30 / 30 / 20. If the lesson has application objectives, the application columns are never empty. Declare `planned_percent` per topic; the script prints actual percentages beside the plan.

### Step 4. Write the items to the blueprint

Read `references/item-writing-rules.md`. The rules that matter most:

- One item, one objective, one idea. The stem is a direct question or a concrete scenario from the learners' work, never a sentence copied from the lesson.
- **Multiple choice**: the same number of options across the test (4 by default); exactly one correct or best answer; every distractor plausible to someone who did not master the lesson, ideally a **real mistake** from the lesson's "common mistakes"; no "all of the above", "none of the above" or "both A and B"; no double negatives; options of the same grammatical form and similar length, so the right one does not stand out.
- **True or false**: at most 20% of the points; a false statement has exactly one false element; no giveaway words (always, never, all, none, only, sometimes, usually, may); roughly as many true as false.
- **Matching**: column titles; items of one kind per column; more options on the right than prompts on the left (3 to 5 or 6, at most 5 to 8 or 10); each option used once at most.
- **Fill in the blank**: blank in the middle or at the end; a term, number or name, never a verb; at most 2 blanks; blanks of equal length; list every accepted spelling.
- **Short answer**: the task, length, time and scoring criteria in the question; scoring split into points of 0.25 to 1; a model answer that passes.
- Every selected-response item has an `explanation` (why the key is right and why each distractor is wrong, written for the learner who just chose wrong) and a `source` (section, video or slide to review).
- A test with several item types is split into parts by type, never mixed.

Write cell by cell and check each item against its objective as you go. Put the key anywhere; the script shuffles and spreads the answers.

### Step 5. Key, scoring, assignment and rubric

Selected-response points: total divided evenly (10 items → 1 point each; 25 → 0.4). Mixed tests split points by planned time (30% of the time on the selected-response part → 3 of 10 points). The answer key prints conversion to a 10-point scale and a percentage (10X/Xmax); add `grade_bands` if the institution uses letter grades.

Assignments for skill and attitude objectives: read `references/skill-assessment-tools.md` and pick the tool.

- **Checklist** (yes/no) for procedures, observed steps, simple products that either have a feature or do not.
- **Criteria sheet** (points per criterion, grouped under standards) for products scored part by part.
- **Analytic rubric** (3 or 4 levels, for example Needs work, Meets, Good, Excellent) for products with no single right answer: lesson plans, scripts, objective tables, sales pages, presentations.
- **Holistic rubric** for quick overall judgements of many small products.

Write criteria as **result noun + quality sign + something countable**. Include deadline or time, and rules (copyright, learner data, safety) where relevant. Attitude objectives become criteria such as "submitted on time", "revised within 7 days of feedback", "self-score within one level of the instructor's". Rubrics go to learners together with the task.

### Step 6. Review and build

1. Take the test as a learner, key hidden. Your time should be about 70% of the learner time. Fix any item where you had to guess or where two options both looked right.
2. Ask four questions of every item: does it measure its objective? at the right level? are the points fair? is the time enough?
3. Build:

```bash
python scripts/build_assessment.py <folder>/assessment.json
```

The script **refuses to build while blocking errors remain**: an objective with no item, an item with no objective, not exactly one key, a banned option, true/false over 20% of the points or with a giveaway word, unequal selected-response points, totals that do not add up, an item two levels below its objective, a long dash or a stock AI phrase. Warnings (correct option much longer than the distractors, a letter used for over 40% of keys, short right column in matching, an item one level below an application objective, a negative stem not in capitals) still build; read them and decide. `--seed N` reshuffles, `--check-only` checks without building, `--no-docx` skips Word.

4. Read `02_Test_Form_A.md` once more as a learner; compare `01_Test_Blueprint.md` with the plan from step 3.

Use `python -X utf8` on Windows if the console mangles accents. Word output needs `python-docx` (`pip install python-docx`); everything else uses the standard library.

## Report back

The folder path; the blueprint in short (topic x level: item counts); items per type; the assignment and its marking tool; the pass mark and why; the warnings you kept and why; assumptions (for example an objective you moved to the assignment, or objectives you derived because none were given).

## Language and voice

Write the test in the language of the user's request and set `language` (`en` or `vi`) so headings, instructions and the answer sheet match. Stems and options are short, plain and neutral. Scenarios have a person, a place and numbers ("Hannah teaches Year 9 in Leeds and writes..."). Explanations read like a colleague talking: one or two sentences, pointing at exactly where learners go wrong. No long dashes, no stock phrases ("delve", "in today's fast-paced world", "plays a crucial role"), no tidy triplets. Assignments and rubrics stay brief and administrative.

If a question is hard to write because the lesson is vague, the problem is the lesson or the objective, not the item: say so, and suggest the fix (a countable standard, a split objective, a missing example) rather than writing a vague item.

## Reference files

- `references/test-design-process.md` - the six steps; blueprint templates; the nine blueprint moves; choosing standards and sharing points; scoring for three kinds of test; validity, reliability, usability; diagnostic, formative, summative; analysing results and giving feedback.
- `references/objective-levels-and-tools.md` - levels and verbs for the cognitive (revised Bloom), psychomotor (Dave) and affective (Krathwohl) domains with matching assessment methods; verb → blueprint level → item type or tool.
- `references/item-writing-rules.md` - rules, strengths, weaknesses and examples for essay and oral questions and the four selected-response types; writing distractors from real mistakes; laying out the test and answer sheet; every check the script runs.
- `references/skill-assessment-tools.md` - designing skill assessment; checklists, criteria sheets, holistic and analytic rubrics with steps and examples; writing criteria; the assignment JSON.
- `references/worked-example.md` - the decisions behind the example in `examples/`, to calibrate difficulty, voice and explanation length.
- `templates/assessment.example.json` - a complete test with all five item types and one rubric assignment.
- `scripts/build_assessment.py` - checks and builds everything.
