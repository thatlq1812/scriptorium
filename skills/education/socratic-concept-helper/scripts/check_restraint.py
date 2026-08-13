#!/usr/bin/env python3
"""Deterministic linter for a drafted tutoring response's Socratic restraint.

Scriptorium never calls an AI/LLM API (CLAUDE.md principle 8) -- this script
cannot "understand" a drafted response the way a model can. What it CAN do
mechanically is a narrow set of text-pattern checks that catch the most
common, cheaply-detectable ways a drafted response breaks Socratic restraint
(Khan Academy Khanmigo's public design pattern -- see SKILL.md "Why this
skill" for the citation): giveaway final-answer phrasing, an answer-key-style
dump, and a response with zero guiding questions at all. It also runs one
genuinely deterministic check: if the student's message contains a simple
arithmetic expression, it computes the expression itself (safe AST-based
evaluation, no eval()/exec()) and flags if that literal computed value
appears in the draft response -- a real, mechanical "did you just hand over
the final number" catch, not a heuristic guess.

This is NOT a semantic understanding of whether the response is genuinely
Socratic -- see SKILL.md "Known limitations" for exactly what it can't catch
(paraphrased answers, answers embedded in a worked-out derivation with no
literal giveaway phrase, non-arithmetic final answers, etc.). A clean run
means "no known violation pattern found," never "this response is provably
Socratic."

Usage:
    python check_restraint.py <session.json>

session.json:
    {
      "student_message": "What is 12 * 15?",
      "draft_response": "What have you tried so far for this kind of problem?",
      "context": "homework"   # optional: "homework" | "exam" | "general" (default "general")
    }

Exit 0 = no violation found, exit 1 = one or more violations (each printed
with the exact matched text/reason), exit 2 = malformed input.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

VALID_CONTEXTS = {"homework", "exam", "general"}

# Giveaway final-answer / answer-key phrasing. Case-insensitive. Deliberately
# narrow and literal -- a paraphrase that avoids all of these is a known gap
# (see SKILL.md "Known limitations"), not silently claimed as caught.
GIVEAWAY_PATTERNS = [
    re.compile(r"\bthe answer is\b", re.IGNORECASE),
    re.compile(r"\bfinal answer\s*[:=]", re.IGNORECASE),
    re.compile(r"\bthe correct answer is\b", re.IGNORECASE),
    re.compile(r"\bthe correct choice is\b", re.IGNORECASE),
    re.compile(r"^\s*answer\s*[:=]", re.IGNORECASE | re.MULTILINE),
    re.compile(r"\banswer key\b", re.IGNORECASE),
    re.compile(r"\bthe result is\b", re.IGNORECASE),
    re.compile(r"^\s*solution\s*[:=]", re.IGNORECASE | re.MULTILINE),
    re.compile(r"\bso the answer to your (?:homework|question|problem) is\b", re.IGNORECASE),
    re.compile(r"\byou should (?:write|put|answer)\b.{0,40}\bas your answer\b", re.IGNORECASE),
]

# Safe arithmetic expression extraction: numbers and + - * / only, no
# variables/functions -- deliberately narrow, extended operators (^, %, etc.)
# are not attempted since ambiguity there is a real risk of a false claim.
ARITH_EXPR_RE = re.compile(
    r"\d+(?:\.\d+)?(?:\s*[+\-*x×/]\s*\d+(?:\.\d+)?)+"
)


def _normalize_arith(expr: str) -> str:
    expr = expr.replace("×", "*").replace("x", "*").replace("X", "*")
    return expr


def _safe_eval_arith(expr: str) -> float | None:
    """Evaluate a restricted arithmetic expression via the ast module --
    never eval()/exec(). Returns None if the expression contains anything
    outside +, -, *, /, numbers, and parentheses."""
    try:
        node = ast.parse(expr, mode="eval")
    except SyntaxError:
        return None

    allowed_binops = (ast.Add, ast.Sub, ast.Mult, ast.Div)

    def _eval(n: ast.AST) -> float:
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.BinOp) and isinstance(n.op, allowed_binops):
            left = _eval(n.left)
            right = _eval(n.right)
            if isinstance(n.op, ast.Add):
                return left + right
            if isinstance(n.op, ast.Sub):
                return left - right
            if isinstance(n.op, ast.Mult):
                return left * right
            if isinstance(n.op, ast.Div):
                if right == 0:
                    raise ZeroDivisionError
                return left / right
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            val = _eval(n.operand)
            return val if isinstance(n.op, ast.UAdd) else -val
        raise ValueError("disallowed node")

    try:
        return _eval(node)
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def _format_number(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:g}"


def find_computed_answer_leak(student_message: str, draft_response: str) -> list[str]:
    violations: list[str] = []
    for match in ARITH_EXPR_RE.finditer(student_message):
        raw_expr = match.group(0)
        normalized = _normalize_arith(raw_expr)
        result = _safe_eval_arith(normalized)
        if result is None:
            continue
        formatted = _format_number(result)
        token_re = re.compile(rf"(?<!\d){re.escape(formatted)}(?!\d)")
        if token_re.search(draft_response):
            violations.append(
                f"student's message contains the arithmetic expression '{raw_expr}' "
                f"(computes to {formatted}); that exact computed value appears literally "
                f"in the draft response -- likely a direct final-answer disclosure."
            )
    return violations


def check_restraint(session: dict) -> list[str]:
    violations: list[str] = []

    student_message = session.get("student_message", "")
    draft_response = session.get("draft_response", "")
    context = session.get("context", "general")

    for pattern in GIVEAWAY_PATTERNS:
        m = pattern.search(draft_response)
        if m:
            violations.append(
                f"giveaway final-answer/answer-key phrasing matched: {m.group(0)!r}"
            )

    if "?" not in draft_response:
        violations.append(
            "draft response contains no question mark -- Socratic restraint requires "
            "at least one guiding question back to the student, never a pure statement."
        )

    violations.extend(find_computed_answer_leak(student_message, draft_response))

    if context in ("homework", "exam"):
        # Extra scrutiny context is recorded for the report but does not change
        # which patterns are checked -- the same mechanical checks apply; a
        # human/agent reviewing a homework/exam-context violation should treat
        # it as higher priority, not differently detected.
        pass

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("session_path", type=Path, help="Path to session.json")
    args = parser.parse_args()

    if not args.session_path.exists():
        print(f"ERROR: {args.session_path} does not exist.", file=sys.stderr)
        return 2

    try:
        raw = args.session_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: could not read {args.session_path}: {exc}", file=sys.stderr)
        return 2

    try:
        session = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: malformed JSON in {args.session_path}: {exc}", file=sys.stderr)
        return 2

    if not isinstance(session, dict):
        print(f"ERROR: {args.session_path} must contain a JSON object, got {type(session).__name__}.", file=sys.stderr)
        return 2

    if "draft_response" not in session or not isinstance(session.get("draft_response"), str) or not session["draft_response"].strip():
        print("ERROR: 'draft_response' is required and must be a non-empty string.", file=sys.stderr)
        return 2

    if "student_message" not in session or not isinstance(session.get("student_message"), str):
        print("ERROR: 'student_message' is required and must be a string (may be empty, but the key must be present and a string).", file=sys.stderr)
        return 2

    context = session.get("context", "general")
    if context not in VALID_CONTEXTS:
        print(f"ERROR: 'context' ({context!r}) must be one of {sorted(VALID_CONTEXTS)} if present.", file=sys.stderr)
        return 2

    violations = check_restraint(session)

    if violations:
        print(f"VIOLATIONS FOUND ({len(violations)}):")
        for v in violations:
            print(f"  - {v}")
        print(
            "\nThis is a mechanical text-pattern check, not proof the response is or "
            "isn't Socratic -- see SKILL.md 'Known limitations' for what it can't catch. "
            "Revise the draft to ask a guiding question and remove any direct final answer "
            "before sending it to the student."
        )
        return 1

    print("OK: no known restraint-violation pattern found in the draft response.")
    print(
        "Reminder: this is a narrow mechanical check (giveaway phrasing, zero-question "
        "responses, literal arithmetic-answer leaks) -- it cannot verify the response is "
        "genuinely Socratic in substance. A human or the calling agent still owns that judgment."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
