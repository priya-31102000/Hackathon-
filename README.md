# ConceptBridge AI

An interactive prototype that turns quiz mistakes into a likely prerequisite gap, a short lesson, and a fresh mastery question.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The app works without an API key using built-in lessons. For generated lesson wording, set `OPENAI_API_KEY` in your shell before launching Streamlit. `OPENAI_MODEL` is optional and defaults to `gpt-4o-mini`.

## What is implemented

- Five-question diagnostic quiz drawn from a connected fractions and decimals learning path.
- Fifteen tagged diagnostic items and five unseen reassessment items in `question_bank.json`.
- Distractor-specific misconception mapping and prerequisite-aware gap suggestions in `engine.py`.
- Personalized micro-lesson with foundation, analogy, worked example, and knowledge check.
- New-question reassessment with a simple learning recovery signal.
- Optional LLM lesson generation; rules and fallback lesson content keep diagnosis grounded in the tagged bank.

## Demo scope

The current prototype demonstrates one subject area and one student session in Streamlit. Misconception labels are hypotheses inferred from selected distractors; the UI presents them as likely gaps and exposes the answer evidence. Student accounts, persistent teacher reporting, broader content coverage, and stronger mastery estimation are future extensions.
