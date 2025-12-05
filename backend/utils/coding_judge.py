import random
from typing import Dict, Any, List, Tuple

PROBLEMS: Dict[str, Dict[str, Any]] = {
    "sum_array": {
        "prompt": "Implement a function solve(arr) that returns the sum of integers in the list arr.",
        "tests": [
            ([1, 2, 3], 6),
            ([], 0),
            ([-1, 5, -4], 0),
        ]
    },
    "reverse_string": {
        "prompt": "Implement a function solve(s) that returns the reverse of string s.",
        "tests": [
            ("abc", "cba"),
            ("", ""),
            ("RaceCar", "raCecaR"),
        ]
    },
    "factorial": {
        "prompt": "Implement a function solve(n) that returns n! (factorial) for non-negative n.",
        "tests": [
            (0, 1),
            (3, 6),
            (5, 120),
        ]
    }
}

TRACK_DEFAULTS = {
    "General": ["sum_array", "reverse_string", "factorial"],
    "MERN": ["reverse_string"],
    "Data Science": ["sum_array"],
    "Data Analytics": ["sum_array"],
    "AI/ML": ["factorial"],
    "Python": ["reverse_string", "sum_array"],
    "Java": ["factorial"],
    "Cloud": ["sum_array"],
    "Cyber": ["reverse_string"]
}


def pick_problem(track: str = "General") -> Dict[str, Any]:
    keys = TRACK_DEFAULTS.get(track, TRACK_DEFAULTS["General"]) or list(PROBLEMS.keys())
    key = random.choice(keys)
    p = PROBLEMS[key]
    return {"key": key, "prompt": p["prompt"]}


def _safe_exec_user(code_text: str) -> Dict[str, Any]:
    env = {}
    # Restrict builtins for safety; this is minimal and only for simple tasks
    safe_globals = {"__builtins__": {"range": range, "len": len, "sum": sum}}
    try:
        exec(code_text, safe_globals, env)
    except Exception as e:
        return {"error": f"Code execution error: {e}"}
    return {"env": env}


def grade_code(problem_key: str, code_text: str) -> Tuple[int, str]:
    prob = PROBLEMS.get(problem_key)
    if not prob:
        return 0, f"Unknown problem: {problem_key}"
    res = _safe_exec_user(code_text or "")
    if "error" in res:
        return 0, res["error"]
    env = res.get("env", {})
    solve = env.get("solve")
    if not callable(solve):
        return 0, "Function solve(...) not found. Define solve to accept the described input."
    passed = 0
    total = len(prob["tests"]) or 1
    failures: List[str] = []
    for inp, expected in prob["tests"]:
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