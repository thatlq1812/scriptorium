#!/usr/bin/env python3
"""Deterministically aggregate/validate exam scores for one assessment
(MCQ answer-key matching + human-scored essay/rubric criteria) — stdlib
only, local, no AI/network of any kind.

This script NEVER invents a score. It does two kinds of arithmetic, both
pure and deterministic:

  1. MCQ (trắc nghiệm): exact answer-key matching, case/whitespace-
     insensitive. A missing/blank answer always counts as wrong, never as
     correct. An answer to a question not in the key is ignored.
  2. Essay/rubric (tự luận): sums per-criterion scores that were ALREADY
     assigned by a human or an upstream process (this script does not
     grade essay content). Each criterion score is validated against that
     criterion's declared max_points — a score exceeding its criterion's
     max is a hard error, refused (never silently clamped or accepted).

Combined total per student = mcq_score + essay_total (whichever sections
are present in the answer key). Class statistics (mean/max/min/count) are
computed over combined totals.

This grades exactly ONE assessment. It does NOT compute a term average
(TBM) or an overall grade classification (xếp loại) across multiple
assessments — that is grade-book-builder's job. It does NOT produce a
final .docx/.xlsx report — delegate that to office-doc-creator once
scores pass this validation.

Usage:
    python grade_exam.py <answer_key.json> <student_responses.json> [--out results.json]

Exit codes: 0 = graded cleanly (results printed, written if --out given),
1 = refused (a criterion score exceeds its declared max, or another
input-validity error), 2 = malformed input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


class GradingError(Exception):
    pass


def _load_json(path: Path, label: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise GradingError(f"MALFORMED {label}: {exc}") from exc
    if not isinstance(data, dict):
        raise GradingError(f"MALFORMED {label}: top-level JSON must be an object")
    return data


def _norm(value: object) -> str:
    """Normalize one MCQ answer cell for matching: trimmed + upper-cased.

    None/empty always normalize to "" which never matches a real key
    option, so a missing answer is always counted wrong, never correct."""
    if value is None:
        return ""
    return str(value).strip().upper()


def parse_answer_key(key: dict) -> tuple[dict | None, dict | None]:
    """Returns (mcq_config, rubric_config). Either may be None if that
    section is absent from the key, but at least one must be present."""
    mcq_raw = key.get("mcq")
    rubric_raw = key.get("rubric")

    if mcq_raw is None and rubric_raw is None:
        raise GradingError("answer key must declare at least one of 'mcq' or 'rubric'")

    mcq: dict | None = None
    if mcq_raw is not None:
        if not isinstance(mcq_raw, dict):
            raise GradingError("answer key 'mcq' must be an object")
        answer_key = mcq_raw.get("answer_key")
        if not isinstance(answer_key, dict) or not answer_key:
            raise GradingError("answer key 'mcq.answer_key' must be a non-empty object {question_id: correct_answer}")

        question_ids: list[str] = []
        key_norm: dict[str, str] = {}
        for qid, correct in answer_key.items():
            qid_s = str(qid).strip()
            if not qid_s:
                raise GradingError("answer key 'mcq.answer_key' has an empty question id")
            norm = _norm(correct)
            if not norm:
                raise GradingError(f"answer key 'mcq.answer_key' question {qid_s!r} has an empty correct answer")
            question_ids.append(qid_s)
            key_norm[qid_s] = norm

        scale = mcq_raw.get("scale", 10)
        if not isinstance(scale, (int, float)) or scale <= 0:
            raise GradingError(f"answer key 'mcq.scale' must be a positive number, got {scale!r}")
        scale = float(scale)

        points_per_question = mcq_raw.get("points_per_question")
        if isinstance(points_per_question, (int, float)) and points_per_question > 0:
            per_q = float(points_per_question)
        else:
            per_q = scale / len(question_ids)

        round_digits = mcq_raw.get("round_digits", 2)
        if not isinstance(round_digits, int) or not (0 <= round_digits <= 6):
            round_digits = 2

        mcq = {
            "question_ids": question_ids,
            "answer_key": key_norm,
            "scale": scale,
            "per_question": per_q,
            "round_digits": round_digits,
        }

    rubric: dict | None = None
    if rubric_raw is not None:
        if not isinstance(rubric_raw, list) or not rubric_raw:
            raise GradingError("answer key 'rubric' must be a non-empty list of {criterion_name, max_points}")
        criteria: dict[str, float] = {}
        order: list[str] = []
        for i, item in enumerate(rubric_raw):
            if not isinstance(item, dict):
                raise GradingError(f"answer key 'rubric[{i}]' must be an object")
            name = str(item.get("criterion_name", "")).strip()
            if not name:
                raise GradingError(f"answer key 'rubric[{i}]' missing 'criterion_name'")
            if name in criteria:
                raise GradingError(f"answer key 'rubric' has a duplicate criterion_name: {name!r}")
            max_points = item.get("max_points")
            if not isinstance(max_points, (int, float)) or max_points <= 0:
                raise GradingError(f"answer key 'rubric[{i}]' ({name!r}) 'max_points' must be a positive number")
            criteria[name] = float(max_points)
            order.append(name)
        rubric = {"criteria": criteria, "order": order}

    return mcq, rubric


def grade_mcq_one(student_id: str, mcq_answers: dict, mcq: dict) -> dict:
    correct = 0
    wrong = 0
    blank = 0
    detail: dict[str, str] = {}
    submitted = {str(k).strip(): v for k, v in mcq_answers.items()} if isinstance(mcq_answers, dict) else {}

    for qid in mcq["question_ids"]:
        ans = submitted.get(qid)
        norm = _norm(ans)
        if not norm:
            detail[qid] = "blank"
            blank += 1
        elif norm == mcq["answer_key"][qid]:
            detail[qid] = "correct"
            correct += 1
        else:
            detail[qid] = "wrong"
            wrong += 1

    score = round(correct * mcq["per_question"], mcq["round_digits"])
    return {
        "correct_count": correct,
        "wrong_count": wrong,
        "blank_count": blank,
        "mcq_score": score,
        "detail": detail,
    }


def grade_essay_one(student_id: str, essay_scores: object, rubric: dict) -> tuple[dict, list[str]]:
    """Sums human-assigned per-criterion scores. Returns (result, errors).
    Refuses (returns errors, never clamps) if a criterion score exceeds its
    declared max_points, is negative, or names a criterion not in the rubric."""
    errors: list[str] = []
    per_criterion: dict[str, dict] = {}
    seen: set[str] = set()

    entries = essay_scores if isinstance(essay_scores, list) else []
    if not isinstance(essay_scores, list) and essay_scores is not None:
        errors.append(f"student {student_id}: 'essay_scores' must be a list")

    for i, item in enumerate(entries):
        if not isinstance(item, dict):
            errors.append(f"student {student_id}: essay_scores[{i}] must be an object")
            continue
        name = str(item.get("criterion_name", "")).strip()
        if not name:
            errors.append(f"student {student_id}: essay_scores[{i}] missing 'criterion_name'")
            continue
        if name not in rubric["criteria"]:
            errors.append(f"student {student_id}: essay_scores[{i}] criterion_name {name!r} is not in the rubric")
            continue
        if name in seen:
            errors.append(f"student {student_id}: duplicate essay score for criterion {name!r}")
            continue
        seen.add(name)

        score = item.get("score")
        max_points = rubric["criteria"][name]
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            errors.append(f"student {student_id}: essay_scores criterion {name!r} 'score' must be a number")
            continue
        score = float(score)
        if score < 0:
            errors.append(f"student {student_id}: essay_scores criterion {name!r} score {score} is negative")
            continue
        if score > max_points:
            errors.append(
                f"student {student_id}: essay_scores criterion {name!r} score {score} exceeds its max_points "
                f"{max_points} — REFUSED, never clamped"
            )
            continue

        per_criterion[name] = {
            "score": score,
            "max_points": max_points,
            "justification": str(item.get("justification", "")).strip(),
        }

    missing = [c for c in rubric["order"] if c not in per_criterion]

    if errors:
        return {}, errors

    essay_total = round(sum(v["score"] for v in per_criterion.values()), 4)
    return {
        "per_criterion": per_criterion,
        "missing_criteria": missing,
        "essay_total": essay_total,
    }, []


def grade(key: dict, responses: dict) -> tuple[list[dict], list[str], dict]:
    """Returns (per_student_results, errors, class_stats). If errors is
    non-empty, per_student_results/class_stats are incomplete/unreliable —
    the caller must refuse to proceed."""
    mcq, rubric = parse_answer_key(key)

    students = responses.get("students")
    if not isinstance(students, list) or not students:
        raise GradingError("student responses 'students' must be a non-empty list")

    errors: list[str] = []
    results: list[dict] = []
    seen_ids: set[str] = set()

    for i, entry in enumerate(students):
        if not isinstance(entry, dict):
            errors.append(f"students[{i}] must be an object")
            continue
        student_id = str(entry.get("student_id", "")).strip()
        if not student_id:
            errors.append(f"students[{i}] missing 'student_id'")
            continue
        if student_id in seen_ids:
            errors.append(f"duplicate student_id: {student_id!r}")
            continue
        seen_ids.add(student_id)

        result: dict = {"student_id": student_id}
        combined = 0.0
        has_component = False

        if mcq is not None:
            mcq_result = grade_mcq_one(student_id, entry.get("mcq_answers", {}), mcq)
            result["mcq"] = mcq_result
            combined += mcq_result["mcq_score"]
            has_component = True

        if rubric is not None:
            essay_result, essay_errors = grade_essay_one(student_id, entry.get("essay_scores"), rubric)
            if essay_errors:
                errors.extend(essay_errors)
                continue
            result["essay"] = essay_result
            combined += essay_result["essay_total"]
            has_component = True

        if not has_component:
            continue

        result["combined_total"] = round(combined, 4)
        results.append(result)

    if errors:
        return results, errors, {}

    totals = [r["combined_total"] for r in results]
    n = len(totals)
    stats = {
        "count": n,
        "mean": round(sum(totals) / n, 4) if n else 0,
        "max": max(totals) if n else 0,
        "min": min(totals) if n else 0,
    }
    return results, errors, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("answer_key", type=Path, help="Path to an answer-key JSON file (see assets/answer_key_template.json)")
    parser.add_argument("responses", type=Path, help="Path to a student-responses JSON file (see assets/student_responses_template.json)")
    parser.add_argument("--out", type=Path, default=None, help="If grading succeeds with no errors, also write full results JSON to this path")
    parser.add_argument("--force", action="store_true", help="Overwrite --out if it already exists")
    args = parser.parse_args()

    try:
        key = _load_json(args.answer_key, "answer_key")
        responses = _load_json(args.responses, "student_responses")
        results, errors, stats = grade(key, responses)
    except GradingError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if errors:
        print(f"REFUSED: {len(errors)} error(s) — no scores accepted, no output written")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"GRADED: {stats['count']} student(s)")
    for r in results:
        parts = []
        if "mcq" in r:
            m = r["mcq"]
            parts.append(f"MCQ {m['mcq_score']} ({m['correct_count']} đúng / {m['wrong_count']} sai / {m['blank_count']} bỏ trống)")
        if "essay" in r:
            e = r["essay"]
            parts.append(f"essay {e['essay_total']}")
            if e["missing_criteria"]:
                parts.append(f"missing criteria: {e['missing_criteria']}")
        print(f"  - {r['student_id']}: total {r['combined_total']} [{', '.join(parts)}]")

    print(f"CLASS STATS: mean={stats['mean']} max={stats['max']} min={stats['min']} count={stats['count']}")

    if args.out:
        if args.out.exists() and not args.force:
            print(f"REFUSED: {args.out} already exists, use --force to overwrite", file=sys.stderr)
            return 2
        payload = {"results": results, "class_stats": stats}
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK: wrote {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
