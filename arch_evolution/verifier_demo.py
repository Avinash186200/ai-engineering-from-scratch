"""Stage 4 in 60 lines: the model never writes numbers, code checks and renders them.

Each tool result gets a call id (c1, c2, ...). Each number in it gets a token
(c1.n0, c1.n1, ...). The model's answer may only use tokens. The verifier
checks with set lookups, and code renders the real values.

Run: python arch_evolution/verifier_demo.py
"""
import re

DIGIT = re.compile(r"\d")
TOKEN = re.compile(r"\{(c\d+\.n\d+)\}")


def tokenize(results):
    """Give every number in every tool result a token. Returns {token: (field, value)}."""
    table = {}
    for i, result in enumerate(results, start=1):
        n = 0
        for field, value in result.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                table[f"c{i}.n{n}"] = (field, value)
                n += 1
    return table


def verify(statement, table):
    """Return a list of error codes. An empty list means the answer is grounded."""
    errors = []
    text_only = TOKEN.sub("", statement)
    if DIGIT.search(text_only):
        errors.append("DIGIT_IN_TEXT")          # the model typed a number itself
    for tok in TOKEN.findall(statement):
        if tok not in table:
            errors.append(f"UNKNOWN_TOKEN:{tok}")  # a token no tool produced in this run
    return errors


def render(statement, table, decimals=2):
    """Code, not the model, prints the numbers."""
    def fill(m):
        field, value = table[m.group(1)]
        return f"{value:.{decimals}f} ({field})"
    return TOKEN.sub(fill, statement)


def answer(statement, table):
    errors = verify(statement, table)
    if errors:
        return {"status": "repair", "errors": errors}
    return {"status": "ok", "text": render(statement, table)}


if __name__ == "__main__":
    results = [{"fund": "Fund A", "predicted_return_pct": 0.99, "volatility_pct": 12.4}]
    table = tokenize(results)
    print("tokens   :", table)
    print("grounded :", answer("Expected return is {c1.n0}, volatility {c1.n1}.", table))
    print("made up  :", answer("Expected return is 1.5 percent.", table))
    print("bad token:", answer("Expected return is {c2.n0}.", table))
