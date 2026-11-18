import json
from pathlib import Path
import streamlit as st
from engine import analyze, generate_lesson

st.set_page_config(page_title="ConceptBridge AI", page_icon="🌉", layout="wide")
DATA = json.loads(Path(__file__).with_name("question_bank.json").read_text(encoding="utf-8"))
QUESTIONS, CONCEPTS = DATA["questions"], DATA["concepts"]
QUIZ_IDS = ["Q01", "Q04", "Q07", "Q10", "Q13"]
by_id = {q["id"]: q for q in QUESTIONS}

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
.stApp {background: #f5f7fb; color: #152338; font-family: 'DM Sans', sans-serif;}
h1,h2,h3 {font-family:'Manrope',sans-serif; letter-spacing:-.03em;}
.hero {background:linear-gradient(120deg,#132d4f,#205c79);color:#fff;padding:30px 34px;border-radius:20px;margin:8px 0 24px;}
.hero p {color:#d8e9f1;margin-bottom:0}.tag {display:inline-block;background:#dff2e9;color:#17634b;padding:5px 10px;border-radius:20px;font-size:12px;font-weight:700;}
.card {background:white;border:1px solid #e5eaf1;border-radius:16px;padding:20px 22px;margin:10px 0;box-shadow:0 3px 12px #17324d08;}
.muted {color:#69788c;font-size:14px}.big {font-size:28px;font-weight:800;color:#142c49}
div.stButton>button {border-radius:10px;font-weight:700;}
</style>""", unsafe_allow_html=True)

if "stage" not in st.session_state: st.session_state.stage = "home"

with st.sidebar:
    st.markdown("## 🌉 ConceptBridge")
    st.caption("Don't correct the answer. Correct the understanding.")
    st.markdown("---")
    st.markdown("**Learning path**")
    stages = ["quiz", "analysis", "lesson", "mastery"]
    active = stages.index(st.session_state.stage) if st.session_state.stage in stages else -1
    for i, label in enumerate(["1  Diagnostic quiz", "2  Gap analysis", "3  Micro-lesson", "4  Mastery check"]):
        st.write(("● " if active == i else "○ ") + label)
    st.markdown("---")
    st.caption("Demo subject · Fractions & decimals")

st.markdown('<div class="hero"><div class="tag">PREREQUISITE INTELLIGENCE</div><h1 style="color:white;margin:12px 0 4px">Every wrong answer has a story.</h1><p>Find the foundation behind the mistake, learn it in a few minutes, then prove what you know.</p></div>', unsafe_allow_html=True)

def reset():
    for key in list(st.session_state.keys()):
        if key.startswith("ans_") or key in ["stage", "responses", "diagnosis", "lesson", "recheck"]: st.session_state.pop(key, None)
    st.session_state.stage = "home"

if st.session_state.stage == "home":
    left, right = st.columns([1.3, .7])
    with left:
        st.markdown("### A five-question learning check")
        st.write("This short diagnostic looks for patterns across fractions and decimals. If it finds a possible gap, you'll get a focused explanation and new questions to try.")
        st.markdown('<div class="card"><b>What happens next</b><br><br>① Answer 5 questions &nbsp; ② See the likely concept gap &nbsp; ③ Learn with an everyday example &nbsp; ④ Try unseen practice</div>', unsafe_allow_html=True)
        if st.button("Start diagnostic", type="primary", use_container_width=True): st.session_state.stage = "quiz"; st.rerun()
    with right:
        st.markdown('<div class="card"><span class="muted">QUIZ LENGTH</span><div class="big">5 questions</div><hr><span class="muted">SUBJECT</span><div><b>Fractions & decimals</b></div><br><span class="muted">APPROACH</span><div><b>Explainable · supportive · adaptive</b></div></div>', unsafe_allow_html=True)

elif st.session_state.stage == "quiz":
    st.subheader("Diagnostic quiz")
    st.caption("Choose the answer that feels right. Your selections help us find what to teach next.")
    with st.form("quiz_form"):
        answers = {}
        for n, qid in enumerate(QUIZ_IDS, 1):
            q = by_id[qid]
            st.markdown(f'<div class="card"><span class="tag">QUESTION {n} OF 5</span><h3>{q["question"]}</h3></div>', unsafe_allow_html=True)
            answers[qid] = st.radio("Choose one", list(q["options"].keys()), format_func=lambda x, opts=q["options"]: f"{x}.  {opts[x]}", key=f"ans_{qid}", horizontal=True, label_visibility="collapsed")
        submitted = st.form_submit_button("Analyze my answers", type="primary", use_container_width=True)
    if submitted:
        st.session_state.responses = [{"question_id": qid, "answer": answers[qid]} for qid in QUIZ_IDS]
        st.session_state.diagnosis = analyze(st.session_state.responses, QUESTIONS, CONCEPTS)
        st.session_state.stage = "analysis"; st.rerun()

elif st.session_state.stage == "analysis":
    d = st.session_state.diagnosis
    correct = sum(st.session_state.responses[i]["answer"] == by_id[qid]["answer"] for i, qid in enumerate(QUIZ_IDS))
    st.subheader("Your learning snapshot")
    m1,m2,m3 = st.columns(3)
    m1.metric("Starting score", f"{correct}/5")
    m2.metric("Questions to review", str(len(d["evidence"])))
    m3.metric("Pattern found", "Yes" if d["misconception"] else "Not yet")
    if d["evidence"]:
        st.markdown(f'<div class="card"><span class="tag">A LIKELY GAP TO EXPLORE</span><h2>{d["gap_label"] or "Foundational skill"}</h2><p>{d["misconception_text"]}</p><p class="muted">This is a hypothesis based on your selected answers, not a judgment about how you think. We will check it with a new question.</p></div>', unsafe_allow_html=True)
        with st.expander("What evidence led to this suggestion?"):
            for e in d["evidence"]: st.write(f"• {e['question']} — selected {e['selected']}")
        if st.button("Show me a short lesson", type="primary"): st.session_state.lesson = generate_lesson(d); st.session_state.stage = "lesson"; st.rerun()
    else:
        st.success("Great work — you got all five right. Try a stretch lesson or restart to explore another learning path.")
    if st.button("Start over"): reset(); st.rerun()

elif st.session_state.stage == "lesson":
    lesson = st.session_state.lesson
    st.markdown(f'<span class="tag">2-MINUTE MICRO-LESSON</span><h2>{lesson["title"]}</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><h3>1 · Start with the foundation</h3><p>{lesson["foundation"]}</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><h3>2 · Picture it</h3><p>{lesson["analogy"]}</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><h3>3 · Work through an example</h3><p>{lesson["worked"]}</p></div>', unsafe_allow_html=True)
    if st.button("I’m ready to check my understanding", type="primary"): st.session_state.stage = "mastery"; st.rerun()

elif st.session_state.stage == "mastery":
    st.subheader("Try a fresh question")
    lesson = st.session_state.lesson
    mapping = {"equivalent_fractions":"R01", "fraction_addition":"R02", "fraction_multiplication":"R04", "fraction_division":"R05", "place_value":"Q14"}
    rq = by_id[mapping.get(st.session_state.diagnosis.get("gap"), "R01")]
    st.caption("Practice question")
    choice = st.radio(rq["question"], list(rq["options"].keys()), format_func=lambda x: f"{x}. {rq['options'][x]}", key="recheck", horizontal=True)
    if st.button("Check my understanding", type="primary"):
        if choice == rq["answer"]: st.success("You got it! Your new answer shows progress on this concept.")
        else: st.info(f"Good try. The best answer is {rq['answer']}: {rq['options'][rq['answer']]}. Review the lesson once more, then try again.")
    if st.button("Finish and restart"): reset(); st.rerun()

st.markdown("<br><p class='muted' style='text-align:center'>ConceptBridge AI · A prototype for learning recovery</p>", unsafe_allow_html=True)
