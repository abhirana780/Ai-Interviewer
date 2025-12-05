import random
from typing import Dict, Any, List, Tuple

LABS: Dict[str, Dict[str, Any]] = {
    "string_length": {
        "prompt": "Implement a function solve(s) that returns the length of string s.",
        "tests": [
            ("abc", 3),
            ("", 0),
            ("OpenAI", 6),
        ]
    },
    "unique_count": {
        "prompt": "Implement a function solve(arr) that returns the count of unique integers in the list arr.",
        "tests": [
            ([1, 2, 2, 3], 3),
            ([], 0),
            ([5, 5, 5], 1),
        ]
    }
}


def pick_lab() -> Dict[str, Any]:
    key = random.choice(list(LABS.keys()))
    lab = LABS[key]
    return {"key": key, "prompt": lab["prompt"]}


def _safe_exec_user(code_text: str) -> Dict[str, Any]:
    env = {}
    safe_globals = {"__builtins__": {"range": range, "len": len, "sum": sum, "set": set}}
    try:
        exec(code_text, safe_globals, env)
    except Exception as e:
        return {"error": f"Code execution error: {e}"}
    return {"env": env}


def grade_lab_code(lab_key: str, code_text: str) -> Tuple[int, str]:
    lab = LABS.get(lab_key)
    if not lab:
        return 0, f"Unknown lab: {lab_key}"
    res = _safe_exec_user(code_text or "")
    if "error" in res:
        return 0, res["error"]
    env = res.get("env", {})
    solve = env.get("solve")
    if not callable(solve):
        return 0, "Function solve(...) not found. Define solve to accept the described input."
    passed = 0
    total = len(lab["tests"]) or 1
    failures: List[str] = []
    for inp, expected in lab["tests"]:
        try:
            out = solve(inp) if isinstance(inp, list) or isinstance(inp, str) else solve(inp)
            if out == expected:
                passed += 1
            else:
                failures.append(f"Input={inp!r} expected={expected!r} got={out!r}")
        except Exception as e:
            failures.append(f"Input={inp!r} raised error: {e}")
    score = int((passed / total) * 100)
    feedback = "All tests passed." if passed == total else ("; ".join(failures) or "Some tests failed.")
    return score, feedback