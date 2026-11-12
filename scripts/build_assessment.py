#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check an assessment.json and build the full test pack from it.

Usage:
    python build_assessment.py path/to/assessment.json [--seed N] [--check-only] [--no-docx]

Writes next to the JSON:
    01_Test_Blueprint.md            blueprint (topics x cognitive levels), objective coverage, assessment plan
    02_Test_Form_A.md / .docx       learner copy, form A (shuffled items and options) + answer sheet
    02_Test_Form_B.md / .docx       learner copy, form B (and C, D... if "forms" > 2)
    03_Answer_Key_and_Marking_Guide.md / .docx
    04_Assignment_and_Rubric.md / .docx
    quiz.gift                       Moodle GIFT import file
    questions.csv                   one row per item, for LMS imports and spreadsheets
    _check/check-report.md          blocking errors and warnings

Refuses to build while blocking errors remain (exit code 1).
"""
import argparse
import csv
import json
import random
import re
import sys
from pathlib import Path

LEVELS = ["recall", "understand", "apply", "higher-order"]
TYPES = ["mcq", "true-false", "matching", "fill-blank", "short-answer"]
SELECTED = ("mcq", "true-false", "matching", "fill-blank")
LETTERS = "ABCDEFGHIJKL"
EM_DASH, EN_DASH = chr(0x2014), chr(0x2013)

L = {
    "en": {
        "level": {"recall": "Recall", "understand": "Understanding",
                  "apply": "Routine application", "higher-order": "Higher-order application"},
        "type": {"mcq": "Multiple choice", "true-false": "True or false", "matching": "Matching",
                 "fill-blank": "Fill in the blank", "short-answer": "Short answer"},
        "howto": {
            "mcq": "Choose ONE best answer for each question.",
            "true-false": "Mark T if the statement is true, F if it is false.",
            "matching": "Match each item on the left with ONE item on the right. The right column has extra items.",
            "fill-blank": "Fill each blank with one word, phrase or number.",
            "short-answer": "Answer briefly, within the length and time given for each question.",
        },
        "method": {"product": "Product assessment", "performance": "Observed performance", "observation": "Observation",
                   "role-play": "Role play", "presentation": "Presentation", "project": "Project"},
        "T": "T", "F": "F", "TRUE": "TRUE", "FALSE": "FALSE",
        "form": "Form", "course": "Course", "lesson": "Lesson", "time": "Time", "minutes": "minutes",
        "points": "points", "pt": "pt", "total": "Total", "part": "Part", "items": "items", "one_item": "item", "item": "Item",
        "question": "Question", "answer": "Answer", "answer_sheet": "Answer sheet",
        "name_line": "Name: ................................", "correct": "Correct answers: ......",
        "no_material": "Closed book", "scoring_criteria": "Scoring criteria", "requirements": "Requirements",
        "blueprint": "TEST BLUEPRINT", "purpose": "Purpose", "format": "Format",
        "bp_matrix": "1. Topics x cognitive levels", "topic": "Topic", "planned": "planned",
        "by_type": "2. Items by type", "type_h": "Type", "n_items": "Items",
        "coverage": "3. Objectives and how each one is measured", "objective": "Objective", "level_h": "Level",
        "text_h": "Objective", "test_items": "Test items", "assignments": "Assignments", "none": "(none)",
        "plan": "4. Assessment plan for the lesson", "instrument": "Instrument", "when": "When",
        "measures": "Measures", "weight": "Weight", "marker": "Marked by", "pass": "Pass mark",
        "auto": "auto-scored / instructor", "counts": "counts toward the test",
        "key_title": "ANSWER KEY AND MARKING GUIDE", "pass_mark": "Pass mark", "why": "Why",
        "key_by_form": "1. Answer key by form", "orig": "Source item", "see_guide": "see marking guide",
        "explain_h": "2. Explanations (by source item)", "measures_obj": "measures",
        "correct_is": "Answer", "TRUE_w": "TRUE", "FALSE_w": "FALSE",
        "blank": "Blank", "accept": "accept", "point_needed": "Point to look for",
        "model": "Model answer that passes", "explanation": "Explanation", "review": "Review",
        "scale_h": "3. Scores and conversion",
        "scale_txt": "Total points: {t}. Every selected-response item carries the same points. Convert: score out of 10 = 10 x X / {t}; percentage = 100 x X / {t}.",
        "raw": "Raw score", "out10": "Out of 10", "pct": "Percent", "bands": "Grade bands",
        "after_h": "4. After marking",
        "after_txt": "Any item fewer than 60% of learners get right points to content that was not taught well enough. Record the facility index and fix the lesson section listed:",
        "pct_right": "....... % correct",
        "feedback_txt": "Feedback to learners should be timely, specific, show what to improve and be easy to act on. In an online quiz, the explanations in section 2 are that feedback, so write them for the learner who just picked a wrong option.",
        "asg_title": "ASSIGNMENT AND MARKING TOOL", "no_asg": "This lesson has no submitted assignment; every objective is measured by the test.",
        "measures_row": "Objectives measured", "method_h": "Method", "time_h": "Working time", "deadline": "Deadline",
        "deliverable": "Deliverable", "conditions": "Conditions", "marker_h": "Marked by", "score_h": "Points",
        "pass_when": "Pass when", "task": "Task", "guidance": "Guidance",
        "checklist_h": "Checklist (share it with learners before they start)", "check_item": "Check",
        "yes": "Yes", "no": "No", "required": "Required",
        "criteria_h": "Criteria sheet", "criterion": "Standard / criterion", "max_pts": "Max points", "given": "Awarded",
        "rubric_h": "Analytic rubric (share it with learners before they start)", "crit_pts": "Criterion (points)",
        "rubric_calc": "Criterion score = criterion maximum x (level reached / {n}). Maximum total {t}.",
        "holistic_h": "Holistic rubric", "level_c": "Level", "desc": "Description",
        "self_check_h": "Self-check before submitting",
        "gift_matching": "// GIFT has no distractors on the right; the imported version keeps only the correct pairs",
        "gift_2blank": "// {id}: two blanks, GIFT takes one; split into two questions when importing",
        "report": "Check report", "blocking": "Blocking errors", "warnings": "Warnings",
        "blocking_h": "Blocking errors (fix these; nothing was built)",
        "warn_h": "Warnings (pack was built; read and decide)",
        "built": "Built in {d}: {n} items, {f} forms, {a} assignments. Warnings: {w}.",
        "fix": "{n} blocking errors. Fix {p} and run again. Report: {r}",
        "checked": "Checked, no blocking errors.",
    },
    "vi": {
        "level": {"recall": "Nhận biết", "understand": "Thông hiểu",
                  "apply": "Vận dụng thấp", "higher-order": "Vận dụng cao"},
        "type": {"mcq": "Nhiều lựa chọn", "true-false": "Đúng - Sai", "matching": "Ghép hợp",
                 "fill-blank": "Điền khuyết", "short-answer": "Tự luận ngắn"},
        "howto": {
            "mcq": "Chọn MỘT phương án đúng nhất cho mỗi câu.",
            "true-false": "Ghi Đ nếu phát biểu đúng, S nếu phát biểu sai.",
            "matching": "Ghép mỗi mục ở cột trái với MỘT mục ở cột phải. Cột phải có mục thừa.",
            "fill-blank": "Điền từ, cụm từ hoặc số thích hợp vào chỗ trống.",
            "short-answer": "Trả lời ngắn gọn, đúng độ dài và thời gian ghi ở mỗi câu.",
        },
        "method": {"product": "Đánh giá sản phẩm", "performance": "Quan sát thao tác", "observation": "Quan sát",
                   "role-play": "Đóng vai", "presentation": "Trình bày", "project": "Dự án"},
        "T": "Đ", "F": "S", "TRUE": "ĐÚNG", "FALSE": "SAI",
        "form": "Mã đề", "course": "Khóa", "lesson": "Bài", "time": "Thời gian", "minutes": "phút",
        "points": "điểm", "pt": "đ", "total": "Tổng", "part": "Phần", "items": "câu", "one_item": "câu", "item": "Câu",
        "question": "Câu", "answer": "Trả lời", "answer_sheet": "Phiếu trả lời",
        "name_line": "Họ tên: ................................", "correct": "Số câu đúng: ......",
        "no_material": "Không sử dụng tài liệu", "scoring_criteria": "Tiêu chí chấm", "requirements": "Yêu cầu",
        "blueprint": "MA TRẬN ĐỀ", "purpose": "Mục đích", "format": "Hình thức",
        "bp_matrix": "1. Ma trận chủ đề x mức độ", "topic": "Chủ đề", "planned": "dự kiến",
        "by_type": "2. Số câu theo dạng", "type_h": "Dạng", "n_items": "Số câu",
        "coverage": "3. Mục tiêu và công cụ đo", "objective": "Mục tiêu", "level_h": "Mức",
        "text_h": "Nội dung", "test_items": "Câu hỏi", "assignments": "Bài tập", "none": "(không)",
        "plan": "4. Kế hoạch đánh giá của bài", "instrument": "Công cụ", "when": "Thời điểm",
        "measures": "Đo mục tiêu", "weight": "Tỉ trọng", "marker": "Người chấm", "pass": "Ngưỡng đạt",
        "auto": "tự động / giảng viên", "counts": "tính vào đề",
        "key_title": "ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM", "pass_mark": "Ngưỡng đạt", "why": "Lý do",
        "key_by_form": "1. Bảng đáp án theo mã đề", "orig": "Câu gốc", "see_guide": "xem hướng dẫn chấm",
        "explain_h": "2. Giải thích từng câu (theo câu gốc)", "measures_obj": "đo",
        "correct_is": "Đáp án", "TRUE_w": "ĐÚNG", "FALSE_w": "SAI",
        "blank": "Chỗ trống", "accept": "chấp nhận", "point_needed": "Ý cần có",
        "model": "Bài làm mẫu đạt", "explanation": "Giải thích", "review": "Xem lại",
        "scale_h": "3. Thang điểm và quy đổi",
        "scale_txt": "Tổng điểm đề: {t}. Câu trắc nghiệm điểm bằng nhau. Quy đổi: thang 10 = 10 x X / {t}; phần trăm = 100 x X / {t}.",
        "raw": "Điểm đạt", "out10": "Thang 10", "pct": "Phần trăm", "bands": "Xếp loại",
        "after_h": "4. Sau khi chấm",
        "after_txt": "Câu nào dưới 60% người làm đúng: nội dung đó dạy chưa tới. Ghi tỉ lệ đúng và sửa mục bài tương ứng:",
        "pct_right": "....... % đúng",
        "feedback_txt": "Phản hồi cho người học phải đúng lúc, cụ thể, chỉ ra chỗ cần sửa và dễ làm theo. Với quiz online, phần giải thích ở mục 2 chính là phản hồi, nên viết cho người vừa chọn sai đọc.",
        "asg_title": "BÀI TẬP VÀ CÔNG CỤ CHẤM", "no_asg": "Bài này không có bài tập nộp; mọi mục tiêu đo bằng đề.",
        "measures_row": "Mục tiêu đo", "method_h": "Phương pháp", "time_h": "Thời gian làm", "deadline": "Hạn nộp",
        "deliverable": "Sản phẩm nộp", "conditions": "Điều kiện", "marker_h": "Người chấm", "score_h": "Điểm",
        "pass_when": "Đạt khi", "task": "Nhiệm vụ", "guidance": "Hướng dẫn",
        "checklist_h": "Bảng kiểm (công bố trước cho người học)", "check_item": "Nội dung kiểm",
        "yes": "Có", "no": "Không", "required": "Bắt buộc",
        "criteria_h": "Bảng tiêu chí đánh giá", "criterion": "Tiêu chuẩn / Tiêu chí", "max_pts": "Điểm chuẩn", "given": "Điểm đánh giá",
        "rubric_h": "Rubric phân tích (công bố trước cho người học)", "crit_pts": "Tiêu chí (điểm)",
        "rubric_calc": "Điểm tiêu chí = điểm tối đa của tiêu chí x (mức đạt / {n}). Tổng tối đa {t}.",
        "holistic_h": "Rubric tổng hợp", "level_c": "Mức", "desc": "Mô tả",
        "self_check_h": "Tự chấm trước khi nộp",
        "gift_matching": "// GIFT không có mục thừa ở cột phải; bản nhập LMS chỉ giữ các cặp đúng",
        "gift_2blank": "// {id}: 2 chỗ trống, GIFT chỉ nhận một; tách thành 2 câu khi nhập",
        "report": "Báo cáo kiểm máy", "blocking": "Lỗi chặn", "warnings": "Cảnh báo",
        "blocking_h": "Lỗi chặn (phải sửa, chưa sinh đề)",
        "warn_h": "Cảnh báo (đã sinh đề, đọc và quyết định)",
        "built": "Đã sinh đề tại {d}: {n} câu, {f} mã đề, {a} bài tập. Cảnh báo: {w}.",
        "fix": "{n} lỗi chặn. Sửa {p} rồi chạy lại. Báo cáo: {r}",
        "checked": "Kiểm xong, không lỗi chặn.",
    },
}

# words that give away a true/false answer (absolutes tend to be false, hedges tend to be true)
TELLTALE = {
    "en": ["always", "never", "all", "none", "every", "only", "sometimes", "usually", "often",
           "generally", "may", "might", "most"],
    "vi": ["luôn luôn", "không bao giờ", "tất cả", "mọi", "đôi khi", "thường thường",
           "có thể", "hầu hết", "duy nhất"],
}
BANNED_OPTIONS = ["all of the above", "none of the above", "both a and b", "both b and c",
                  "a and b", "a and c", "b and c", "all of these", "none of these",
                  "tất cả các đáp án", "tất cả các phương án", "tất cả đáp án", "không có đáp án nào",
                  "không có phương án nào", "cả a và b", "cả b và c", "a và c đúng", "a và b đúng"]
STOCK_PHRASES = ["delve", "in today's fast-paced", "fast-paced world", "game-changer", "game changer",
                 "plays a crucial role", "plays a vital role", "it is important to note",
                 "it's important to note", "unlock the power", "ever-evolving", "let's dive",
                 "in the realm of", "tapestry",
                 "trong thế giới ngày nay", "không thể phủ nhận", "đóng vai trò quan trọng",
                 "hãy cùng khám phá", "đó là lý do tại sao", "ngày càng trở nên"]
NEGATION = {"en": r"\b(not|except|false|incorrect|least)\b", "vi": r"\b(không|sai|ngoại trừ|trừ)\b"}
COUNTABLE = r"\d|\bno\b|\bnone\b|\ball\b|\bevery\b|\beach\b|\bmissing\b|\bany\b|không|đủ|mọi|thiếu|hết"


# ------------------------------------------------------------------ helpers
def walk_strings(obj, path=""):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")


def make_num(lang):
    def num(x):
        s = f"{float(x):g}"
        return s.replace(".", ",") if lang == "vi" else s
    return num


def count(n, T):
    return f"{n} {T['one_item'] if n == 1 else T['items']}"


def words(s):
    return len(re.findall(r"\S+", s or ""))


def has_word(text, w, lang):
    if lang == "vi" or " " in w:
        return w in text.lower()
    return re.search(rf"\b{re.escape(w)}\b", text.lower()) is not None


# ------------------------------------------------------------------ checks
def check(a):
    err, warn = [], []
    E, W = err.append, warn.append
    for f in ["lesson_code", "lesson_title", "test_title", "purpose", "format", "minutes",
              "total_points", "objectives", "topics", "items"]:
        if f not in a:
            E(f"Missing required field `{f}`")
    if err:
        return err, warn
    lang = a.get("language", "en")
    if lang not in L:
        E(f"`language` must be one of {list(L)}")
        return err, warn
    num = make_num(lang)
    if a["purpose"] not in ("diagnostic", "formative", "summative"):
        E("`purpose` must be diagnostic | formative | summative")
    if a["format"] not in ("objective", "mixed", "essay"):
        E("`format` must be objective | mixed | essay")

    for p, s in walk_strings(a):
        if EM_DASH in s or EN_DASH in s:
            E(f"Long dash at `{p}`: ...{s[:60]}  (use a hyphen, comma or full stop)")
        for c in STOCK_PHRASES:
            if c in s.lower():
                E(f"Stock phrase '{c}' at `{p}`")

    objs = {o["code"]: o for o in a["objectives"]}
    topics = {t["code"] for t in a["topics"]}
    for o in a["objectives"]:
        if o.get("level") not in LEVELS:
            E(f"Objective {o.get('code')}: level `{o.get('level')}` is not one of {LEVELS}")
        if o.get("measured_by", "test") not in ("test", "assignment", "both"):
            E(f"Objective {o.get('code')}: measured_by must be test | assignment | both")
        if not o.get("text"):
            E(f"Objective {o.get('code')}: missing `text`")

    n_opts = int(a.get("options_per_item", 4))
    total = float(a["total_points"])
    item_pts = tf_pts = 0.0
    sel_pts = set()
    tf_true = tf_false = 0
    per_obj = {k: 0 for k in objs}
    ids = set()

    for q in a["items"]:
        qid = q.get("id", "?")
        if qid in ids:
            E(f"Item {qid}: duplicate id")
        ids.add(qid)
        t = q.get("type")
        if t not in TYPES:
            E(f"Item {qid}: type `{t}` is not one of {TYPES}")
            continue
        if q.get("topic") not in topics:
            E(f"Item {qid}: topic `{q.get('topic')}` is not in topics[]")
        if q.get("level") not in LEVELS:
            E(f"Item {qid}: level `{q.get('level')}` is not valid")
        oc = q.get("objective")
        if oc not in objs:
            E(f"Item {qid}: objective `{oc}` is not in objectives[]")
        else:
            per_obj[oc] += 1
            if q.get("level") in LEVELS and objs[oc].get("level") in LEVELS:
                gap = LEVELS.index(objs[oc]["level"]) - LEVELS.index(q["level"])
                if gap >= 2:
                    E(f"Item {qid}: item level ({q['level']}) is two or more levels below objective {oc} ({objs[oc]['level']}); it does not measure the objective")
                elif gap == 1 and LEVELS.index(objs[oc]["level"]) >= 2:
                    W(f"Item {qid}: one level below objective {oc}; an application objective is measured by a lower-level item")
                elif gap < 0:
                    W(f"Item {qid}: item level is ABOVE objective {oc}; learners may fail an objective they actually met")
        pts = float(q.get("points", 0))
        if pts <= 0:
            E(f"Item {qid}: points must be > 0")
        item_pts += pts
        if t in SELECTED:
            sel_pts.add(round(pts, 4))
        stem = q.get("stem", "")
        if not stem.strip():
            E(f"Item {qid}: missing `stem`")
        n = words(stem)
        if n < 6:
            W(f"Item {qid}: very short stem ({n} words)")
        if n > 70:
            W(f"Item {qid}: long stem ({n} words); consider trimming the scenario")
        if t in SELECTED and not q.get("explanation", "").strip():
            E(f"Item {qid}: missing `explanation` (the learner who picks a wrong option needs feedback)")
        if not q.get("source"):
            W(f"Item {qid}: missing `source` (lesson section or slide to review)")
        if t == "mcq":
            outside_quotes = re.sub(r'"[^"]*"', "", stem)
            if re.search(NEGATION[lang], outside_quotes) and not re.search(NEGATION[lang].upper().replace("\\B", "\\b"), stem):
                W(f"Item {qid}: negative stem not in capitals (write NOT, EXCEPT)")
            opts = q.get("options", [])
            if len(opts) != n_opts:
                E(f"Item {qid}: {len(opts)} options, the test declares {n_opts}")
            if len({o.strip().lower() for o in opts}) != len(opts):
                E(f"Item {qid}: duplicate options")
            ans = q.get("answer")
            if not isinstance(ans, int) or not (0 <= ans < len(opts)):
                E(f"Item {qid}: `answer` must be the index 0..{len(opts) - 1} of the correct option")
            for o in opts:
                for b in BANNED_OPTIONS:
                    if re.search(rf"(^|\W){re.escape(b)}(\W|$)", o.lower()):
                        E(f"Item {qid}: banned option '{o}'")
            if isinstance(ans, int) and 0 <= ans < len(opts) and len(opts) > 1:
                right = len(opts[ans])
                longest_wrong = max(len(o) for i, o in enumerate(opts) if i != ans)
                if right >= 1.5 * longest_wrong and right > 25:
                    W(f"Item {qid}: the correct option is 1.5x longer than the longest distractor (a giveaway)")
        elif t == "true-false":
            if not isinstance(q.get("answer"), bool):
                E(f"Item {qid}: true-false needs `answer` true or false")
            elif q["answer"]:
                tf_true += 1
            else:
                tf_false += 1
            tf_pts += pts
            for w in TELLTALE[lang]:
                if has_word(stem, w, lang):
                    E(f"Item {qid}: telltale word '{w}' in a true-false statement")
        elif t == "matching":
            left, right = q.get("left", []), q.get("right", [])
            if not q.get("left_title") or not q.get("right_title"):
                E(f"Item {qid}: matching item needs both column titles")
            if len(right) <= len(left):
                E(f"Item {qid}: right column ({len(right)}) must be longer than the left ({len(left)})")
            elif len(right) < 2 * len(left) and len(left) >= 3:
                W(f"Item {qid}: make the right column about twice the left to cut guessing")
            ans = q.get("answer", [])
            if len(ans) != len(left):
                E(f"Item {qid}: `answer` needs {len(left)} indexes, one per left item")
            elif len(set(ans)) != len(ans):
                E(f"Item {qid}: one right-column item is matched to more than one left item")
            elif any(not isinstance(i, int) or not (0 <= i < len(right)) for i in ans):
                E(f"Item {qid}: answer index outside the right column")
        elif t == "fill-blank":
            blanks = len(re.findall(r"_{3,}", stem))
            if blanks == 0:
                E(f"Item {qid}: no blank in the stem (write ____)")
            if blanks > 2:
                E(f"Item {qid}: more than 2 blanks")
            if re.match(r"^\s*_{3,}", stem):
                E(f"Item {qid}: blank at the start of the sentence")
            ans = q.get("answer")
            if not isinstance(ans, list) or len(ans) != blanks or any(not isinstance(x, list) or not x for x in ans):
                E(f"Item {qid}: `answer` must be {blanks} list(s) of accepted spellings")
        elif t == "short-answer":
            sc = q.get("scoring", [])
            if not sc:
                E(f"Item {qid}: short answer needs `scoring`")
            elif abs(sum(float(x.get("points", 0)) for x in sc) - pts) > 1e-6:
                E(f"Item {qid}: scoring points add up to {num(sum(float(x.get('points', 0)) for x in sc))}, item is worth {num(pts)}")
            if not q.get("model_answer"):
                W(f"Item {qid}: add a `model_answer` that would pass")

    asg_pts = 0.0
    per_obj_asg = {k: 0 for k in objs}
    for g in a.get("assignments", []):
        gid = g.get("id", "?")
        if not g.get("objectives"):
            E(f"Assignment {gid}: no objectives")
        for oc in g.get("objectives", []):
            if oc not in objs:
                E(f"Assignment {gid}: objective `{oc}` does not exist")
            else:
                per_obj_asg[oc] += 1
        crit = g.get("criteria", [])
        if not crit:
            E(f"Assignment {gid}: no criteria")
        tool = g.get("tool")
        if tool not in ("checklist", "criteria-sheet", "rubric", "holistic-rubric"):
            E(f"Assignment {gid}: tool must be checklist | criteria-sheet | rubric | holistic-rubric")
        if tool in ("criteria-sheet", "rubric"):
            s = sum(float(c.get("points", 0)) for c in crit)
            if abs(s - float(g.get("points", 0))) > 1e-6:
                E(f"Assignment {gid}: criteria add up to {num(s)}, assignment is worth {g.get('points')}")
        if tool == "rubric":
            nl = len(g.get("levels", []))
            if nl < 3:
                E(f"Assignment {gid}: an analytic rubric needs at least 3 `levels`")
            for c in crit:
                if len(c.get("descriptors", [])) != nl:
                    E(f"Assignment {gid}: criterion '{c.get('name')}' needs exactly {nl} descriptors")
                for d in c.get("descriptors", []):
                    if not re.search(COUNTABLE, d.lower()):
                        W(f"Assignment {gid}: descriptor '{d[:40]}...' has nothing countable")
        if tool == "holistic-rubric" and len(g.get("levels", [])) < 3:
            E(f"Assignment {gid}: a holistic rubric needs at least 3 levels")
        for f in ["task", "deliverable", "minutes", "pass_rule"]:
            if not g.get(f):
                E(f"Assignment {gid}: missing `{f}`")
        if g.get("counts_toward_test"):
            asg_pts += float(g.get("points", 0))

    if abs(item_pts + asg_pts - total) > 1e-6:
        E(f"Items ({num(item_pts)}) + assignments counted in the test ({num(asg_pts)}) = {num(item_pts + asg_pts)}, but total_points = {num(total)}")
    if len(sel_pts) > 1:
        E(f"Selected-response items carry different points {sorted(sel_pts)}; give them all the same value")
    if tf_pts > 0.2 * total + 1e-6:
        E(f"True-false items carry {num(tf_pts)} points, more than 20% of the total (50% guessing chance)")
    if tf_true + tf_false >= 4 and abs(tf_true - tf_false) > 1:
        E(f"True-false balance: {tf_true} true, {tf_false} false")
    for k, o in objs.items():
        mb = o.get("measured_by", "test")
        if mb in ("test", "both") and per_obj[k] == 0:
            E(f"Objective {k} is measured by the test but no item measures it")
        if mb in ("assignment", "both") and per_obj_asg[k] == 0:
            E(f"Objective {k} is measured by an assignment but no assignment lists it")
        if mb == "assignment" and per_obj[k] > 0:
            W(f"Objective {k} is assignment-only but {per_obj[k]} test items point to it")
        need = o.get("min_items")
        if need and per_obj[k] < need:
            W(f"Objective {k}: its standard needs at least {need} items, the test has {per_obj[k]}")
    if any(o.get("level") in ("apply", "higher-order") and o.get("measured_by", "test") != "assignment" for o in a["objectives"]) \
            and not any(q.get("level") in ("apply", "higher-order") for q in a["items"]):
        W("An application objective is measured by the test, but no item is at an application level")
    n = len(a["items"])
    if a["purpose"] == "formative" and n > 12:
        W(f"Formative quiz with {n} items (> 12); consider splitting it")
    if a["purpose"] == "summative" and n < 15 and not a.get("assignments"):
        W(f"Summative test with only {n} items and no assignment")
    return err, warn


# ------------------------------------------------------------------ shuffle
def shuffle_form(a, seed):
    """Return [(type, [items])] with items and options shuffled, keeping MCQ answers spread out."""
    parts = []
    for attempt in range(60):
        rng = random.Random(seed * 1000 + attempt)
        parts, keys = [], []
        for t in TYPES:
            items = [dict(q) for q in a["items"] if q["type"] == t]
            if not items:
                continue
            rng.shuffle(items)
            for q in items:
                if t == "mcq":
                    idx = list(range(len(q["options"])))
                    rng.shuffle(idx)
                    q["answer"] = idx.index(q["answer"])
                    q["options"] = [q["options"][i] for i in idx]
                    keys.append(q["answer"])
                elif t == "matching":
                    idx = list(range(len(q["right"])))
                    rng.shuffle(idx)
                    q["answer"] = [idx.index(i) for i in q["answer"]]
                    q["right"] = [q["right"][i] for i in idx]
            parts.append((t, items))
        ok = True
        if len(keys) >= 5 and any(keys.count(c) / len(keys) > 0.4 for c in set(keys)):
            ok = False
        if any(keys[i] == keys[i - 1] == keys[i - 2] for i in range(2, len(keys))):
            ok = False
        if ok:
            return parts, None
    return parts, "could not spread the MCQ answers well after 60 tries; kept the last shuffle"


# ------------------------------------------------------------------ markdown builders
def header(a, T, num, form):
    s = [f"# {a['test_title'].upper()}", "",
         f"{T['course']}: {a.get('course', a.get('slug', ''))} · {T['lesson']}: {a['lesson_code']} {a['lesson_title']} · **{T['form']} {form}**", "",
         f"{T['time']}: {a['minutes']} {T['minutes']} · {T['total']}: {num(a['total_points'])} {T['points']} · {a.get('conditions', T['no_material'])}", ""]
    if a.get("instructions"):
        s += [a["instructions"], ""]
    return s


def md_form(a, T, num, form, parts):
    s = header(a, T, num, form)
    n = 0
    n_opts = int(a.get("options_per_item", 4))
    for i, (t, items) in enumerate(parts):
        pts = sum(float(q["points"]) for q in items)
        s += [f"## {T['part']} {LETTERS[i]}. {T['type'][t]} ({count(len(items), T)}, {num(pts)} {T['points']})", "",
              f"*{T['howto'][t]}*", ""]
        for q in items:
            n += 1
            q["_n"] = n
            if t == "mcq":
                s += [f"**{T['question']} {n}.** {q['stem']}", ""]
                s += [f"- {LETTERS[j]}. {o}" for j, o in enumerate(q["options"])] + [""]
            elif t == "true-false":
                s += [f"**{T['question']} {n}.** {q['stem']}  ☐ {T['T']}  ☐ {T['F']}", ""]
            elif t == "matching":
                s += [f"**{T['question']} {n}.** {q['stem']}", "",
                      f"| {q['left_title']} | {q['right_title']} |", "|---|---|"]
                for k in range(max(len(q["left"]), len(q["right"]))):
                    lft = f"{k + 1}. {q['left'][k]}" if k < len(q["left"]) else ""
                    rgt = f"{LETTERS[k]}. {q['right'][k]}" if k < len(q["right"]) else ""
                    s.append(f"| {lft} | {rgt} |")
                s += ["", f"{T['answer']}: " + "  ".join(f"{k + 1} → ___" for k in range(len(q["left"]))), ""]
            elif t == "fill-blank":
                s += [f"**{T['question']} {n}.** {q['stem']}", ""]
            elif t == "short-answer":
                s += [f"**{T['question']} {n}.** ({num(q['points'])} {T['points']}) {q['stem']}", ""]
                if q.get("requirements"):
                    s += [f"*{T['requirements']}: {q['requirements']}*", ""]
                if q.get("scoring"):
                    s += [f"{T['scoring_criteria']}:", ""]
                    s += [f"- {x['point']} ({num(x['points'])} {T['points']})" for x in q["scoring"]] + [""]
    s += ["---", "", f"## {T['answer_sheet']}", "",
          f"{T['name_line']}  {T['form']}: {form}  {T['correct']}", ""]
    for t, items in parts:
        if t == "mcq":
            s += [f"| {T['item']} | " + " | ".join(LETTERS[:n_opts]) + " |", "|---|" + "---|" * n_opts]
            s += [f"| {q['_n']} |" + " ☐ |" * n_opts for q in items] + [""]
        elif t == "true-false":
            s += [f"| {T['item']} | {T['T']} | {T['F']} |", "|---|---|---|"]
            s += [f"| {q['_n']} | ☐ | ☐ |" for q in items] + [""]
        elif t in ("matching", "fill-blank"):
            s += [f"{T['item']} {q['_n']}: ...................................................." for q in items] + [""]
    return "\n".join(s) + "\n"


def key_cell(q, T):
    t = q["type"]
    if t == "mcq":
        return LETTERS[q["answer"]]
    if t == "true-false":
        return T["T"] if q["answer"] else T["F"]
    if t == "matching":
        return ", ".join(f"{k + 1}-{LETTERS[i]}" for k, i in enumerate(q["answer"]))
    if t == "fill-blank":
        return " ; ".join(x[0] for x in q["answer"])
    return T["see_guide"]


def md_key(a, T, num, forms):
    total = float(a["total_points"])
    s = [f"# {T['key_title']}: {a['test_title']}", "",
         f"{T['lesson']}: {a['lesson_code']} {a['lesson_title']} · {T['total']} {num(total)} {T['points']} · {T['time']} {a['minutes']} {T['minutes']}", ""]
    pm = a.get("pass_mark")
    if pm:
        s += [f"**{T['pass_mark']}**: {num(pm.get('points', 0))}/{num(total)}. {T['why']}: {pm.get('reason', '')}", ""]
    s += [f"## {T['key_by_form']}", ""]
    for form, parts in forms:
        s += [f"### {T['form']} {form}", "", f"| {T['item']} | {T['orig']} | {T['answer']} | {T['points']} |", "|---|---|---|---|"]
        s += [f"| {q['_n']} | {q['id']} | {key_cell(q, T)} | {num(q['points'])} |" for _, items in parts for q in items] + [""]
    s += [f"## {T['explain_h']}", ""]
    for q in a["items"]:
        t = q["type"]
        s += [f"### {q['id']} · {T['type'][t]} · {T['level'][q['level']]} · {T['measures_obj']} {q['objective']} · {num(q['points'])} {T['points']}", "",
              q["stem"], ""]
        if t == "mcq":
            s += [f"- {'**✔**' if j == q['answer'] else '✘'} {o}" for j, o in enumerate(q["options"])] + [""]
        elif t == "true-false":
            s += [f"{T['correct_is']}: **{T['TRUE_w'] if q['answer'] else T['FALSE_w']}**", ""]
        elif t == "matching":
            s += [f"{T['correct_is']}: " + "; ".join(f"{q['left'][k]} → {q['right'][i]}" for k, i in enumerate(q["answer"])), ""]
        elif t == "fill-blank":
            s += [f"- {T['blank']} {k + 1}: **{x[0]}** ({T['accept']}: {', '.join(x)})" for k, x in enumerate(q["answer"])] + [""]
        elif t == "short-answer":
            s += [f"| {T['point_needed']} | {T['points']} |", "|---|---|"]
            s += [f"| {x['point']} | {num(x['points'])} |" for x in q["scoring"]] + [""]
            if q.get("model_answer"):
                s += [f"*{T['model']}*: {q['model_answer']}", ""]
        if q.get("explanation"):
            s += [f"**{T['explanation']}**: {q['explanation']}", ""]
        if q.get("source"):
            s += [f"*{T['review']}*: {q['source']}", ""]
    s += [f"## {T['scale_h']}", "", T["scale_txt"].format(t=num(total)), ""]
    if abs(total - 10) > 1e-6:
        s += [f"| {T['raw']} | {T['out10']} | {T['pct']} |", "|---|---|---|"]
        step = total / 10 if total >= 10 else 1
        x = 0.0
        while x <= total + 1e-9:
            s.append(f"| {num(round(x, 2))} | {num(round(10 * x / total, 2))} | {num(round(100 * x / total, 1))}% |")
            x += step
        s.append("")
    if a.get("grade_bands"):
        s += [f"**{T['bands']}**: " + " · ".join(f"{b['label']} ≥ {num(b['min'])}" for b in a["grade_bands"]), ""]
    s += [f"## {T['after_h']}", "", T["after_txt"], ""]
    s += [f"- {q['id']} ({q['objective']}, {q.get('source', '?')}): {T['pct_right']}" for q in a["items"]]
    s += ["", T["feedback_txt"], ""]
    return "\n".join(s) + "\n"


def md_blueprint(a, T, num):
    total = float(a["total_points"])
    s = [f"# {T['blueprint']}: {a['test_title']}", "",
         f"{T['lesson']}: {a['lesson_code']} {a['lesson_title']} · {T['purpose']}: {a['purpose']} · {T['format']}: {a['format']} · {a['minutes']} {T['minutes']} · {num(total)} {T['points']}", "",
         f"## {T['bp_matrix']}", "",
         f"| {T['topic']} | " + " | ".join(T["level"][lv] for lv in LEVELS) + f" | {T['total']} |",
         "|---|" + "---|" * (len(LEVELS) + 1)]
    col = {lv: [0, 0.0] for lv in LEVELS}
    for tp in a["topics"]:
        cells, n_t, p_t = [], 0, 0.0
        for lv in LEVELS:
            its = [q for q in a["items"] if q["topic"] == tp["code"] and q["level"] == lv]
            n, p = len(its), sum(float(q["points"]) for q in its)
            col[lv][0] += n
            col[lv][1] += p
            n_t += n
            p_t += p
            cells.append(f"{', '.join(sorted({q['objective'] for q in its}))}<br>{count(n, T)} · {num(p)} {T['pt']}<br>({', '.join(q['id'] for q in its)})" if its else "")
        plan = f" ({T['planned']} {tp['planned_percent']}%)" if tp.get("planned_percent") is not None else ""
        s.append(f"| **{tp['name']}**{plan} | " + " | ".join(cells) + f" | {count(n_t, T)} · {num(p_t)} {T['pt']} = {num(round(100 * p_t / total, 1))}% |")
    s.append(f"| **{T['total']}** | " + " | ".join(f"{count(col[lv][0], T)} · {num(col[lv][1])} {T['pt']} · {num(round(100 * col[lv][1] / total, 1))}%" for lv in LEVELS)
             + f" | {count(len(a['items']), T)} · {num(sum(float(q['points']) for q in a['items']))} {T['pt']} |")
    s += ["", f"## {T['by_type']}", "", f"| {T['type_h']} | {T['n_items']} | {T['points']} |", "|---|---|---|"]
    for t in TYPES:
        its = [q for q in a["items"] if q["type"] == t]
        if its:
            s.append(f"| {T['type'][t]} | {len(its)} | {num(sum(float(q['points']) for q in its))} |")
    s += ["", f"## {T['coverage']}", "",
          f"| {T['objective']} | {T['level_h']} | {T['text_h']} | {T['test_items']} | {T['assignments']} |", "|---|---|---|---|---|"]
    for o in a["objectives"]:
        its = [q["id"] for q in a["items"] if q["objective"] == o["code"]]
        gs = [g["id"] for g in a.get("assignments", []) if o["code"] in g.get("objectives", [])]
        s.append(f"| {o['code']} | {T['level'][o['level']]} | {o['text']} | {', '.join(its) or T['none']} | {', '.join(gs) or T['none']} |")
    pm = a.get("pass_mark", {})
    s += ["", f"## {T['plan']}", "",
          f"| {T['instrument']} | {T['when']} | {T['measures']} | {T['weight']} | {T['marker']} | {T['pass']} |", "|---|---|---|---|---|---|",
          f"| {a['test_title']} ({a['format']}) | {a.get('timing', a['purpose'])} | {', '.join(sorted({q['objective'] for q in a['items']}))} | {num(total)} {T['points']} | {T['auto']} | {num(pm.get('points', 0))}/{num(total)} |"]
    for g in a.get("assignments", []):
        s.append(f"| {g['id']} {g['title']} ({g['tool']}) | {g.get('when', '')} | {', '.join(g['objectives'])} | {num(g.get('points', 0))} {T['points']}{' (' + T['counts'] + ')' if g.get('counts_toward_test') else ''} | {g.get('marker', '')} | {g['pass_rule']} |")
    return "\n".join(s) + "\n\n"


def md_assignments(a, T, num):
    gs = a.get("assignments", [])
    s = [f"# {T['asg_title']}: {a['lesson_code']} {a['lesson_title']}", ""]
    if not gs:
        return "\n".join(s + [T["no_asg"], ""]) + "\n"
    objs = {o["code"]: o for o in a["objectives"]}
    for g in gs:
        measured = "; ".join(f"{c}: {objs[c]['text']}" for c in g["objectives"] if c in objs)
        s += [f"## {g['id']}. {g['title']}", "", "| | |", "|---|---|",
              f"| {T['measures_row']} | {measured} |",
              f"| {T['method_h']} | {T['method'].get(g.get('method'), g.get('method', ''))} |",
              f"| {T['time_h']} | {g['minutes']} {T['minutes']} |",
              f"| {T['deadline']} | {g.get('deadline', '')} |",
              f"| {T['deliverable']} | {g['deliverable']} |",
              f"| {T['conditions']} | {g.get('conditions', '')} |",
              f"| {T['marker_h']} | {g.get('marker', '')} |",
              f"| {T['score_h']} | {num(g.get('points', 0))} · {T['pass_when']}: {g['pass_rule']} |", "",
              f"### {T['task']}", "", g["task"], ""]
        if g.get("guidance"):
            s += [f"### {T['guidance']}", "", g["guidance"], ""]
        tool, crit = g["tool"], g["criteria"]
        if tool == "checklist":
            s += [f"### {T['checklist_h']}", "", f"| # | {T['check_item']} | {T['yes']} | {T['no']} | {T['required']} |", "|---|---|---|---|---|"]
            s += [f"| {i} | {c['name']} | ☐ | ☐ | {'✔' if c.get('required') else ''} |" for i, c in enumerate(crit, 1)] + [""]
        elif tool == "criteria-sheet":
            s += [f"### {T['criteria_h']}", "", f"| # | {T['criterion']} | {T['max_pts']} | {T['given']} |", "|---|---|---|---|"]
            group, gi, ci = None, 0, 0
            for c in crit:
                std = c.get("standard")
                if std and std != group:
                    gi, ci, group = gi + 1, 0, std
                    s.append(f"| {gi} | **{std}** | **{num(sum(float(x['points']) for x in crit if x.get('standard') == std))}** | |")
                ci += 1
                s.append(f"| {f'{gi}.{ci}' if std else ci} | {c['name']} | {num(c['points'])} | |")
            s += [f"| | **{T['total']}** | **{num(g['points'])}** | |", ""]
        elif tool == "rubric":
            lv = g["levels"]
            s += [f"### {T['rubric_h']}", "", f"| {T['crit_pts']} | " + " | ".join(f"{i + 1}. {x}" for i, x in enumerate(lv)) + " |",
                  "|---|" + "---|" * len(lv)]
            s += [f"| **{c['name']}** ({num(c['points'])}) | " + " | ".join(c["descriptors"]) + " |" for c in crit]
            s += ["", T["rubric_calc"].format(n=len(lv), t=num(g["points"])), ""]
        elif tool == "holistic-rubric":
            s += [f"### {T['holistic_h']}", "", f"| {T['level_c']} | {T['desc']} |", "|---|---|"]
            s += [f"| {len(g['levels']) - i}. {lv} | {c.get('description', c.get('name'))} |" for i, (lv, c) in enumerate(zip(g["levels"], crit))] + [""]
        if g.get("self_check"):
            s += [f"### {T['self_check_h']}", "", g["self_check"], ""]
    return "\n".join(s) + "\n"


# ------------------------------------------------------------------ GIFT and CSV
def gift_escape(t):
    return re.sub(r"([~=#{}:])", r"\\\1", t)


def gift(a, T):
    s = [f"// {a['test_title']} · {a['lesson_code']} {a['lesson_title']}",
         f"$CATEGORY: {a.get('slug', 'course')}/{a['lesson_code']}", ""]
    for q in a["items"]:
        ex = gift_escape(q.get("explanation", ""))
        t = q["type"]
        if t == "mcq":
            s += [f"::{q['id']}::{gift_escape(q['stem'])} {{"]
            s += [f"  {'=' if j == q['answer'] else '~'}{gift_escape(o)}" for j, o in enumerate(q["options"])]
            s += [f"  ####{ex}", "}", ""]
        elif t == "true-false":
            s += [f"::{q['id']}::{gift_escape(q['stem'])} {{{'TRUE' if q['answer'] else 'FALSE'}####{ex}}}", ""]
        elif t == "matching":
            s += [T["gift_matching"], f"::{q['id']}::{gift_escape(q['stem'])} {{"]
            s += [f"  ={gift_escape(q['left'][k])} -> {gift_escape(q['right'][i])}" for k, i in enumerate(q["answer"])]
            s += ["}", ""]
        elif t == "fill-blank":
            if len(q["answer"]) == 1:
                accepted = " ".join(f"={gift_escape(x)}" for x in q["answer"][0])
                s += [f"::{q['id']}::" + re.sub(r"_{3,}", "{" + accepted + "}", gift_escape(q["stem"]), count=1), ""]
            else:
                s += [T["gift_2blank"].format(id=q["id"]), ""]
        elif t == "short-answer":
            s += [f"::{q['id']}::{gift_escape(q['stem'])} {{}}", ""]
    return "\n".join(s) + "\n"


def write_csv(a, path):
    n = int(a.get("options_per_item", 4))
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "topic", "objective", "level", "points", "stem"]
                   + [f"option_{LETTERS[i].lower()}" for i in range(n)] + ["answer", "explanation", "source"])
        for q in a["items"]:
            opts = q.get("options", []) if q["type"] == "mcq" else []
            if q["type"] == "mcq":
                ans = LETTERS[q["answer"]]
            elif q["type"] == "true-false":
                ans = "TRUE" if q["answer"] else "FALSE"
            elif q["type"] == "matching":
                ans = "; ".join(f"{q['left'][k]} -> {q['right'][i]}" for k, i in enumerate(q["answer"]))
            elif q["type"] == "fill-blank":
                ans = " | ".join("/".join(x) for x in q["answer"])
            else:
                ans = q.get("model_answer", "")
            w.writerow([q["id"], q["type"], q["topic"], q["objective"], q["level"], q["points"], q["stem"]]
                       + [opts[i] if i < len(opts) else "" for i in range(n)]
                       + [ans, q.get("explanation", ""), q.get("source", "")])


# ------------------------------------------------------------------ DOCX
def docx_from_md(md, path, lang):
    try:
        from docx import Document
        from docx.shared import Pt
    except ImportError:
        return False
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Calibri" if lang == "en" else "Times New Roman"
    st.font.size = Pt(11 if lang == "en" else 12)
    table = None
    for line in md.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.match(r"^-+$", c) for c in cells if c):
                continue
            if table is None:
                table = doc.add_table(rows=0, cols=len(cells))
                table.style = "Table Grid"
            row = table.add_row().cells
            for i, c in enumerate(cells[: len(row)]):
                row[i].text = c.replace("**", "").replace("<br>", "\n")
            continue
        table = None
        if line.startswith("### "):
            doc.add_heading(line[4:], level=3)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.strip() == "---":
            doc.add_page_break()
        elif line.strip():
            text = line
            if line.startswith("- ") and re.match(r"^- [A-L]\. ", line):
                text = line[2:]
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Pt(18)
                p.paragraph_format.space_after = Pt(2)
            elif re.match(r"^\s*- ", line):
                text = re.sub(r"^\s*- ", "", line)
                p = doc.add_paragraph(style="List Bullet")
            else:
                p = doc.add_paragraph()
            line = text
            for chunk in re.split(r"(\*\*[^*]+\*\*)", line):
                if chunk.startswith("**") and chunk.endswith("**"):
                    p.add_run(chunk[2:-2]).bold = True
                else:
                    p.add_run(chunk.replace("*", ""))
    doc.save(str(path))
    return True


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description="Check an assessment.json and build the test pack.")
    ap.add_argument("json")
    ap.add_argument("--seed", type=int, default=7, help="change the shuffle")
    ap.add_argument("--check-only", action="store_true", help="run the checks, build nothing")
    ap.add_argument("--no-docx", action="store_true", help="skip the Word files")
    args = ap.parse_args()
    src = Path(args.json)
    a = json.loads(src.read_text(encoding="utf-8"))
    out = src.parent
    lang = a.get("language", "en") if a.get("language", "en") in L else "en"
    T, num = L[lang], make_num(lang)
    (out / "_check").mkdir(parents=True, exist_ok=True)
    err, warn = check(a)
    report = [f"# {T['report']}: {a.get('test_title', src.name)}", "", f"{T['blocking']}: {len(err)} · {T['warnings']}: {len(warn)}", ""]
    if err:
        report += [f"## {T['blocking_h']}", ""] + [f"- {x}" for x in err] + [""]
    if warn:
        report += [f"## {T['warn_h']}", ""] + [f"- {x}" for x in warn] + [""]
    rp = out / "_check" / "check-report.md"
    rp.write_text("\n".join(report), encoding="utf-8")
    for x in err:
        print("ERROR  ", x)
    for x in warn:
        print("WARNING", x)
    if err:
        print("\n" + T["fix"].format(n=len(err), p=src, r=rp))
        sys.exit(1)
    if args.check_only:
        print(T["checked"])
        return
    n_forms = int(a.get("forms", 2))
    forms = []
    for i in range(n_forms):
        name = LETTERS[i]
        parts, note = shuffle_form(a, args.seed + i)
        if note:
            print("WARNING", f"{T['form']} {name}: {note}")
        md = md_form(a, T, num, name, parts)
        (out / f"02_Test_Form_{name}.md").write_text(md, encoding="utf-8")
        if not args.no_docx:
            docx_from_md(md, out / f"02_Test_Form_{name}.docx", lang)
        forms.append((name, parts))
    (out / "01_Test_Blueprint.md").write_text(md_blueprint(a, T, num), encoding="utf-8")
    key = md_key(a, T, num, forms)
    (out / "03_Answer_Key_and_Marking_Guide.md").write_text(key, encoding="utf-8")
    asg = md_assignments(a, T, num)
    (out / "04_Assignment_and_Rubric.md").write_text(asg, encoding="utf-8")
    if not args.no_docx:
        docx_from_md(key, out / "03_Answer_Key_and_Marking_Guide.docx", lang)
        docx_from_md(asg, out / "04_Assignment_and_Rubric.docx", lang)
    (out / "quiz.gift").write_text(gift(a, T), encoding="utf-8")
    write_csv(a, out / "questions.csv")
    print(T["built"].format(d=out, n=len(a["items"]), f=n_forms, a=len(a.get("assignments", [])), w=len(warn)))


if __name__ == "__main__":
    main()
