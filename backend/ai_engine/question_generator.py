import os
import json
import random
import string
from typing import List, Dict, Any, Optional

try:
    import tomllib  # py311+
except Exception:  # pragma: no cover
    tomllib = None

OPENAI_MODEL_DEFAULT = os.getenv("OPENAI_MATH_MODEL", "gpt-4o-mini")

# Data directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
CACHE_PATH = os.path.join(DATA_DIR, "ai_question_cache.json")
LOG_PATH = os.path.join(DATA_DIR, "ai_logs.log")


DEFAULT_TOPICS = ["Algebra", "Functions", "Integrals", "Derivatives", "Geometry"]


def _make_id(length: int = 8) -> str:
    return "q_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _log_ai(message: str) -> None:
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        pass


def _load_openai_api_key() -> Optional[str]:
    # Prefer environment
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    # Try reading from .streamlit/secrets.toml
    if tomllib is not None:
        secrets_path = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            try:
                with open(secrets_path, "rb") as f:
                    data = tomllib.load(f)
                return data.get("openai_api_key") or data.get("OPENAI_API_KEY")
            except Exception:
                pass
    return None


def _read_cache() -> Dict[str, Any]:
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_cache(cache: Dict[str, Any]) -> None:
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception:
        pass


# ---------------- Deterministic templates (expanded) ----------------
# Multiple variants per topic to reduce repetition in fallback mode.

def _generate_algebra() -> Dict[str, Any]:
    variant = random.randint(1, 5)
    labels = ["A", "B", "C", "D"]
    if variant == 1:
        a, b = random.randint(1, 9), random.randint(1, 9)
        correct = a + b
        options = list({correct, correct + 1, correct - 1, correct + 2})
        random.shuffle(options)
        return {
            "id": _make_id(),
            "topic": "Algebra",
            "question": f"What is {a} + {b}?",
            "options": {labels[i]: str(options[i]) for i in range(4)},
            "answer": labels[options.index(correct)],
        }
    if variant == 2:
        a, b = random.randint(2, 10), random.randint(2, 10)
        correct = a - b
        options = list({correct, correct + 1, correct - 1, correct - 2})
        random.shuffle(options)
        return {
            "id": _make_id(),
            "topic": "Algebra",
            "question": f"What is {a} - {b}?",
            "options": {labels[i]: str(options[i]) for i in range(4)},
            "answer": labels[options.index(correct)],
        }
    if variant == 3:
        a, b = random.randint(2, 12), random.randint(2, 12)
        correct = a * b
        options = list({correct, correct + a, correct - b, correct + 1})
        random.shuffle(options)
        return {
            "id": _make_id(),
            "topic": "Algebra",
            "question": f"What is {a}×{b}?",
            "options": {labels[i]: str(options[i]) for i in range(4)},
            "answer": labels[options.index(correct)],
        }
    if variant == 4:
        x = random.randint(1, 9)
        correct = 2 * x + 3
        options = list({correct, correct - 2, correct + 2, correct + 5})
        random.shuffle(options)
        return {
            "id": _make_id(),
            "topic": "Algebra",
            "question": f"If y = 2x + 3, what is y when x={x}?",
            "options": {labels[i]: str(options[i]) for i in range(4)},
            "answer": labels[options.index(correct)],
        }
    # variant 5: simple equation
    c = random.randint(5, 15)
    correct = c
    opts = [c, c - 1, c + 1, c + 2]
    random.shuffle(opts)
    return {
        "id": _make_id(),
        "topic": "Algebra",
        "question": "Solve for x: x = ? (given x = c)",
        "options": {labels[i]: str(opts[i]) for i in range(4)},
        "answer": labels[opts.index(correct)],
    }


def _generate_functions() -> Dict[str, Any]:
    variant = random.randint(1, 4)
    labels = ["A", "B", "C", "D"]
    if variant == 1:
        x = random.randint(2, 6)
        correct = 2 * x + 3
        options = [correct, 2 * x - 3, x + 3, 2 + 3]
        random.shuffle(options)
        return {
            "id": _make_id(),
            "topic": "Functions",
            "question": f"If f(x)=2x+3, what is f({x})?",
            "options": {labels[i]: str(options[i]) for i in range(4)},
            "answer": labels[options.index(correct)],
        }
    if variant == 2:
        x = random.randint(1, 5)
        correct = x * x
        options = [correct, x + x, x ** 3, x + 3]
        random.shuffle(options)
        return {
            "id": _make_id(),
            "topic": "Functions",
            "question": f"If f(x)=x^2, what is f({x})?",
            "options": {labels[i]: str(options[i]) for i in range(4)},
            "answer": labels[options.index(correct)],
        }
    if variant == 3:
        x = random.randint(1, 5)
        correct = 3 * x - 1
        options = [correct, 3 * x + 1, 3 + x, x - 1]
        random.shuffle(options)
        return {
            "id": _make_id(),
            "topic": "Functions",
            "question": f"If f(x)=3x-1, what is f({x})?",
            "options": {labels[i]: str(options[i]) for i in range(4)},
            "answer": labels[options.index(correct)],
        }
    # variant 4
    x = random.randint(1, 4)
    correct = 2 ** x
    options = [correct, 2 * x, x ** 2, 2 ** (x + 1)]
    random.shuffle(options)
    return {
        "id": _make_id(),
        "topic": "Functions",
        "question": f"If f(x)=2^x, what is f({x})?",
        "options": {labels[i]: str(options[i]) for i in range(4)},
        "answer": labels[options.index(correct)],
    }


def _generate_integrals() -> Dict[str, Any]:
    variant = random.randint(1, 4)
    labels = ["A", "B", "C", "D"]
    if variant == 1:
        correct = "x^2"
        options = ["x^2", "2x^2", "x", "2x"]
    elif variant == 2:
        correct = "x^3/3"
        options = ["x^3/3", "3x^2", "x^2/2", "3x"]
    elif variant == 3:
        correct = "ln|x|"
        options = ["ln|x|", "1/x", "x", "e^x"]
    else:
        correct = "e^x"
        options = ["e^x", "x e^x", "x^2", "ln x"]
    random.shuffle(options)
    return {
        "id": _make_id(),
        "topic": "Integrals",
        "question": "Compute the indefinite integral (ignore constant)",
        "options": {labels[i]: options[i] for i in range(4)},
        "answer": labels[options.index(correct)],
    }


def _generate_derivatives() -> Dict[str, Any]:
    variant = random.randint(1, 4)
    labels = ["A", "B", "C", "D"]
    if variant == 1:
        options = ["2x", "x", "x^2", "2"]
        correct = "2x"
        q = "d/dx of x^2 is?"
    elif variant == 2:
        options = ["cos x", "-sin x", "sin x", "-cos x"]
        correct = "cos x"
        q = "d/dx of sin x is?"
    elif variant == 3:
        options = ["e^x", "x e^x", "ln x", "x"]
        correct = "e^x"
        q = "d/dx of e^x is?"
    else:
        options = ["1/x", "x", "ln x", "0"]
        correct = "1/x"
        q = "d/dx of ln x is?"
    random.shuffle(options)
    return {
        "id": _make_id(),
        "topic": "Derivatives",
        "question": q,
        "options": {labels[i]: options[i] for i in range(4)},
        "answer": labels[options.index(correct)],
    }


def _generate_geometry() -> Dict[str, Any]:
    variant = random.randint(1, 4)
    labels = ["A", "B", "C", "D"]
    if variant == 1:
        options = ["180°", "90°", "270°", "360°"]
        correct = "180°"
        q = "Sum of interior angles of a triangle?"
    elif variant == 2:
        options = ["πr^2", "2πr", "πd", "r^2/2"]
        correct = "πr^2"
        q = "Area of a circle with radius r?"
    elif variant == 3:
        options = ["(a+b)/2 * h", "a*b", "(a+b+c)", "2ab"]
        correct = "(a+b)/2 * h"
        q = "Area of a trapezoid with bases a,b and height h?"
    else:
        options = ["a^2 + b^2 = c^2", "a^2 = b^2 + c^2", "a + b = c", "ab = c^2"]
        correct = "a^2 + b^2 = c^2"
        q = "Pythagorean theorem states?"
    random.shuffle(options)
    return {
        "id": _make_id(),
        "topic": "Geometry",
        "question": q,
        "options": {labels[i]: options[i] for i in range(4)},
        "answer": labels[options.index(correct)],
    }


def _generate_question(topic: str) -> Dict[str, Any]:
    if topic == "Algebra":
        return _generate_algebra()
    if topic == "Functions":
        return _generate_functions()
    if topic == "Integrals":
        return _generate_integrals()
    if topic == "Derivatives":
        return _generate_derivatives()
    if topic == "Geometry":
        return _generate_geometry()
    # Fallback simple arithmetic
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    correct = a * b
    options = [correct, correct + 1, correct - 1, correct + 2]
    random.shuffle(options)
    labels = ["A", "B", "C", "D"]
    correct_idx = options.index(correct)
    return {
        "id": _make_id(),
        "topic": topic,
        "question": f"What is {a}×{b}?",
        "options": {labels[i]: str(options[i]) for i in range(4)},
        "answer": labels[correct_idx],
    }


def _openai_generate(topic: str, difficulty: str, num_questions: int) -> List[Dict[str, Any]]:
    # Lazy import to avoid dependency when offline
    try:
        from openai import OpenAI
    except Exception:
        raise RuntimeError("openai package not installed")

    api_key = _load_openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    client = OpenAI(api_key=api_key)

    system = (
        "You are a math question generator. Produce multiple-choice questions with one correct answer."
        " Output JSON only. Choices labeled A-D."
    )
    user = {
        "topic": topic,
        "difficulty": difficulty,
        "num_questions": num_questions,
        "format": {
            "id": "string",
            "topic": "string",
            "question": "string",
            "options": {"A": "string", "B": "string", "C": "string", "D": "string"},
            "answer": "A|B|C|D"
        },
        "instructions": (
            "Return an array named 'questions' where each element matches the format. "
            "IDs must be unique. Questions must be solvable and unambiguous."
        ),
    }

    prompt = {
        "role": "user",
        "content": json.dumps(user, ensure_ascii=False),
    }
    _log_ai(f"[question_gen][request] topic={topic} diff={difficulty} n={num_questions} payload={user}")

    resp = client.chat.completions.create(
        model=OPENAI_MODEL_DEFAULT,
        messages=[{"role": "system", "content": system}, prompt],
        temperature=0.7,
        max_tokens=1200,
    )
    text = resp.choices[0].message.content.strip()
    _log_ai(f"[question_gen][response] {text}")

    data = json.loads(text)
    items = data.get("questions") or data
    # sanitize outputs and ensure schema
    questions: List[Dict[str, Any]] = []
    for q in items:
        qid = q.get("id") or _make_id()
        opts = q.get("options") or {}
        ans = q.get("answer") or q.get("correct")
        question = {
            "id": qid,
            "topic": q.get("topic") or topic,
            "question": q.get("question"),
            "options": {k: str(v) for k, v in list(opts.items())[:4]},
            "answer": (ans if ans in {"A", "B", "C", "D"} else "A"),
        }
        questions.append(question)
    return questions[:num_questions]


def generate_exam(
    topics: List[str] = None,
    num_questions: int = 10,
    mode: str = "deterministic",
    difficulty: str = "medium",
    avoid_repeat: bool = True,
) -> Dict[str, Any]:
    topics = topics or DEFAULT_TOPICS
    mode = (mode or "deterministic").lower()

    api_key_present = _load_openai_api_key() is not None
    use_ai = mode in {"ai", "ai_adaptive"} and api_key_present

    questions: List[Dict[str, Any]] = []
    seen: set[str] = set()

    if use_ai:
        cache = _read_cache()
        topic_quota = max(1, num_questions // max(1, len(topics)))
        remainder = num_questions - (topic_quota * len(topics))
        # For balanced distribution, assign topic_quota to each topic,
        # and distribute the remainder one by one.
        topic_counts = {t: topic_quota for t in topics}
        # Distribute the remainder randomly or round-robin
        for t in random.sample(topics, k=remainder):
            topic_counts[t] += 1

        # Generate/fetch per-topic batch and compose final set
        for topic in topics:
            count = topic_counts[topic]
            key = f"{topic}::{difficulty}::{count}"
            # Remove stale/bad cache if it doesn't match requested count
            if key in cache and len(cache[key]) < count:
                del cache[key]
                _write_cache(cache)
            if key in cache and all(q.get("topic", topic) == topic for q in cache[key]):
                items = cache[key]
            else:
                try:
                    items = _openai_generate(topic=topic, difficulty=difficulty, num_questions=count)
                    # Only cache if all topics are correct
                    if all(q.get("topic", topic) == topic for q in items):
                        cache[key] = items
                        _write_cache(cache)
                except Exception as e:
                    _log_ai(f"[question_gen][fallback] topic={topic} reason={type(e).__name__}: {e}")
                    items = [_generate_question(topic) for _ in range(count)]
            for item in items:
                if len(questions) >= num_questions:
                    break
                key_sig = (item.get("question") or "") + "|" + (item.get("id") or "")
                if avoid_repeat and key_sig in seen:
                    continue
                seen.add(key_sig)
                questions.append(item)
        while len(questions) < num_questions:
            q = _generate_question(random.choice(topics))
            sig = q["question"] + "|" + q["id"]
            if avoid_repeat and sig in seen:
                continue
            seen.add(sig)
            questions.append(q)
        return {"questions": questions[:num_questions], "mode": "ai"}

    if mode in {"ai", "ai_adaptive"} and not api_key_present:
        _log_ai("[question_gen][fallback] No API key; using deterministic generator")

    for _ in range(num_questions * 3):
        if len(questions) >= num_questions:
            break
        topic = random.choice(topics)
        q = _generate_question(topic)
        sig = q["question"] + "|" + q["id"]
        if avoid_repeat and sig in seen:
            continue
        seen.add(sig)
        questions.append(q)

    return {"questions": questions[:num_questions], "mode": "deterministic"}

    # Deterministic mode or no API key available
    if mode in {"ai", "ai_adaptive"} and not api_key_present:
        _log_ai("[question_gen][fallback] No API key; using deterministic generator")

    for _ in range(num_questions * 3):  # extra attempts if avoid_repeat filters
        if len(questions) >= num_questions:
            break
        topic = random.choice(topics)
        q = _generate_question(topic)
        sig = q["question"] + "|" + q["id"]
        if avoid_repeat and sig in seen:
            continue
        seen.add(sig)
        questions.append(q)

    return {"questions": questions[:num_questions], "mode": "deterministic"}


