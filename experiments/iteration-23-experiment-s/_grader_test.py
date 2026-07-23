import re


def extract_boxed(text):
    idx = text.rfind("\\boxed")
    if idx == -1:
        return None
    i = text.find("{", idx)
    if i == -1:
        return None
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
    return None


def normalize(s):
    if s is None:
        return None
    s = s.strip()
    s = s.strip("$")
    s = s.replace("\\left", "").replace("\\right", "")
    s = s.replace("\\!", "").replace("\\,", "").replace("\\;", "")
    s = s.replace("\\:", "").replace("\\ ", "")
    s = s.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    s = s.replace(" ", "")
    s = s.rstrip(".")
    s = s.replace("{,}", "")  # thousands-separator braces sometimes used
    s = s.replace(",", "")
    return s


def to_number(s):
    if s is None:
        return None
    m = re.match(r"^(-?\d+)\\frac\{(-?\d+)\}\{(\d+)\}$", s)  # mixed number
    if m:
        whole, num, den = int(m.group(1)), int(m.group(2)), int(m.group(3))
        sign = -1 if whole < 0 else 1
        return whole + sign * num / den
    m = re.match(r"^-?\\frac\{-?\d+\}\{-?\d+\}$", s)
    if m:
        neg = s.startswith("-")
        body = s[1:] if neg else s
        m2 = re.match(r"^\\frac\{(-?\d+)\}\{(-?\d+)\}$", body)
        val = int(m2.group(1)) / int(m2.group(2))
        return -val if neg else val
    m = re.match(r"^-?\d+/\d+$", s)
    if m:
        a, b = s.split("/")
        return float(a) / float(b)
    try:
        return float(s)
    except ValueError:
        return None


ANSWER_TOKEN = re.compile(
    r"(-?\\frac\{-?\d+\}\{-?\d+\}"
    r"|-?\d+\\frac\{-?\d+\}\{-?\d+\}"
    r"|-?\d+/\d+"
    r"|-?\d[\d,]*\.\d+"
    r"|-?\d[\d,]*)"
)


def grade(gold_raw, model_text):
    pred_raw = extract_boxed(model_text)
    if pred_raw is None:
        after_answer = re.split(r"(?i)answer\s*:", model_text)
        if len(after_answer) > 1:
            m = ANSWER_TOKEN.search(after_answer[-1])
            pred_raw = m.group(0) if m else None
    if pred_raw is None:
        all_tokens = ANSWER_TOKEN.findall(model_text)
        pred_raw = all_tokens[-1] if all_tokens else None
    gold = normalize(gold_raw)
    pred = normalize(pred_raw) if pred_raw else None
    if pred is None:
        return False
    if gold == pred:
        return True
    gn, pn = to_number(gold), to_number(pred)
    if gn is not None and pn is not None:
        return abs(gn - pn) < 1e-6
    return False


CASES = [
    ("9", r"Let's work through this. The answer is \boxed{9}.", True),
    ("\\frac{14}{3}", r"So x = \boxed{\frac{14}{3}}", True),
    ("\\frac{14}{3}", r"So x = \boxed{\dfrac{14}{3}}", True),
    ("-125", r"\boxed{-125}", True),
    ("1.25", r"The result is \boxed{1.25}", True),
    ("1.25", r"\boxed{5/4}", True),
    ("720", r"\boxed{720}", True),
    ("9", r"\boxed{10}", False),
    ("\\frac{3}{56}", r"\boxed{\frac{6}{112}}", True),
    ("2", r"Answer: 2", True),
    ("13535", r"no boxed here, just prose", False),
    ("4", r"\boxed{4.0}", True),
    ("-125", r"\boxed{125}", False),
    ("10", "...math steps...\n8. ANSWER:\nAnswer: 10", True),
    ("850", "so r_1 satisfies ...\n\nAnswer: 850", True),
    ("66200", "Total: 66,200\n\nAnswer: 66,200", True),
    ("14", "we get x=14 which is wrong\nAnswer: 15", False),
    ("2", "Step 8. ANSWER: The final answer is 2.", True),
]

if __name__ == "__main__":
    ok = 0
    for gold, text, expect in CASES:
        got = grade(gold, text)
        status = "OK" if got == expect else "FAIL"
        if got == expect:
            ok += 1
        print(f"{status}  gold={gold!r:20} expect={expect!s:5} got={got!s:5}")
    print(f"\n{ok}/{len(CASES)} passed")
