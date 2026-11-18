"""Explainable diagnosis, prerequisite tracing, and lesson generation."""
from collections import Counter
import json
import os

MISCONCEPTIONS = {
    "adds_numerators_and_denominators": "You may be adding the top and bottom numbers separately. Fraction parts need equal-sized pieces before they can be added.",
    "adds_denominators_only": "You may be changing the size of the pieces while adding. The denominator describes the piece size and stays fixed when the pieces already match.",
    "adds_numerators_without_conversion": "You may know to add the numerators, but these fractions first need the same-sized pieces.",
    "ignores_common_denominator": "You may be combining fractions before checking whether their parts are the same size.",
    "adds_numerators_unnecessarily": "You may be changing the denominator even though both fractions already use equal-sized parts.",
    "adds_denominators_unnecessarily": "You may be adding denominators even though the fractions already have equal-sized parts.",
    "multiplies_without_simplifying": "Your multiplication is likely on track; the remaining step is simplifying the result when possible.",
    "fails_to_simplify": "You may have the right product but need to reduce it to simplest form.",
    "multiplies_instead_of_dividing": "You may be using the multiplication rule for a division question. Division asks how many groups of the second size fit in the first amount.",
    "flips_wrong_fraction": "You may be flipping the first fraction. For fraction division, keep the first fraction and flip the second.",
    "compares_digits_without_aligning_place_value": "You may be comparing digits before aligning tenths and hundredths. Writing 0.7 as 0.70 makes the place values clear.",
    "treats_longer_decimal_as_larger": "You may be assuming more decimal digits means a larger value. Compare place values by writing the numbers with the same number of decimal places.",
}

def analyze(responses, questions, concepts):
    by_id = {q["id"]: q for q in questions}
    evidence = []
    for response in responses:
        q = by_id.get(response["question_id"])
        if not q or response["answer"] == q["answer"]:
            continue
        code = q.get("errors", {}).get(response["answer"], "unclassified_error")
        evidence.append({"question": q["question"], "concept": q["concept"], "code": code,
                         "prerequisites": q.get("prerequisites", []), "selected": q["options"][response["answer"]]})
    counts = Counter(item["code"] for item in evidence)
    prereq_counts = Counter(p for item in evidence for p in item["prerequisites"])
    # Prioritize a repeated misconception; otherwise investigate the most common prerequisite.
    repeated = [code for code, count in counts.items() if count > 1]
    likely_code = max(repeated, key=lambda c: counts[c]) if repeated else (counts.most_common(1)[0][0] if counts else None)
    target = prereq_counts.most_common(1)[0][0] if prereq_counts else None
    if likely_code in {"adds_numerators_and_denominators", "adds_denominators_only", "adds_numerators_without_conversion", "ignores_common_denominator"}:
        target = "equivalent_fractions"
    elif likely_code and likely_code.startswith("compares_") or likely_code == "treats_longer_decimal_as_larger":
        target = "place_value"
    elif likely_code in {"multiplies_instead_of_dividing", "flips_wrong_fraction"}:
        target = "fraction_multiplication"
    label = concepts.get(target, {}).get("label", target.replace("_", " ").title()) if target else None
    return {"evidence": evidence, "misconception": likely_code,
            "misconception_text": MISCONCEPTIONS.get(likely_code, "This answer pattern suggests a skill to review; one response alone is not enough to know the student's reasoning."),
            "gap": target, "gap_label": label, "gap_count": len(prereq_counts)}

def lesson_for(diagnosis):
    gap = diagnosis.get("gap")
    if gap == "equivalent_fractions":
        return {"title":"Make the pieces match", "foundation":"Equivalent fractions name the same amount using different-sized pieces. Multiply or divide the top and bottom by the same number.", "analogy":"Half a pizza is the same amount as two of four equal slices: 1/2 = 2/4.", "worked":"To add 1/2 + 1/4, rewrite 1/2 as 2/4. Then add the two fourths and one fourth: 2/4 + 1/4 = 3/4.", "check":"What is 1/4 + 1/4?"}
    if gap == "place_value":
        return {"title":"Line up decimal place values", "foundation":"The first digit after the decimal is tenths; the next is hundredths. A zero at the end does not change a number.", "analogy":"Think of $0.7 as 70 cents and $0.65 as 65 cents. Seventy cents is greater.", "worked":"Write 0.7 as 0.70. Compare hundredths: 70 hundredths is greater than 65 hundredths.", "check":"Which is greater: 0.6 or 0.58?"}
    if gap == "fraction_multiplication":
        return {"title":"Understand fraction division", "foundation":"Division can ask how many groups of a given size fit into an amount.", "analogy":"If you have half a pizza and serve quarter-pizza slices, you can serve two slices.", "worked":"For 1/2 ÷ 1/4, ask how many fourths fit in one half. One half equals two fourths, so the answer is 2.", "check":"How many 1/4 pieces fit in 3/4?"}
    return {"title":"Build the fraction foundation", "foundation":"A fraction describes equal-sized parts of a whole. The denominator tells the size of each part; the numerator tells how many parts we have.", "analogy":"If a chocolate bar is split into 4 equal squares and you take 3, you have 3/4 of the bar.", "worked":"Start by identifying the whole, then name the number of equal pieces and how many pieces are selected.", "check":"Which is larger: 1/2 or 1/4?"}

def generate_lesson(diagnosis):
    """Use an LLM when configured; retain a grounded, deterministic offline fallback."""
    fallback = lesson_for(diagnosis)
    if not os.getenv("OPENAI_API_KEY") or not diagnosis.get("gap"):
        return fallback
    try:
        from openai import OpenAI
        response = OpenAI().chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a kind, accurate micro-tutor. Return JSON with keys title, foundation, analogy, worked, check. Teach only the supplied prerequisite concept, keep it concise and age-neutral, and do not claim certainty about the student's thinking."},
                {"role": "user", "content": json.dumps({"likely_gap": diagnosis["gap_label"], "evidence": diagnosis["evidence"], "fallback_lesson": fallback})}
            ],
            temperature=0.4,
        )
        generated = json.loads(response.choices[0].message.content)
        return {key: str(generated[key]) for key in fallback}
    except Exception:
        return fallback

def check_mastery(question, choice):
    return choice == question["answer"]
