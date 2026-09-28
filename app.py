import os
import random
import streamlit as st
from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# 1. STREAMLIT PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Veterinary Pathology AI Tutor",
    page_icon="🐾",
    layout="centered",
)

st.title("🐾 General Veterinary Pathology AI Tutor")
st.caption("Module: Etiology and Classification of Disease (BVSc & AH)")

# -----------------------------------------------------------------------------
# 2. SYSTEM PROMPT DEFINITION
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = r"""
# SYSTEM PROMPT: AI PEDAGOGICAL AGENT FOR BEGINNING GENERAL VETERINARY PATHOLOGY

**MODULE:** GENERAL VETERINARY PATHOLOGY – ETIOLOGY AND CLASSIFICATION OF DISEASE  
**TARGET AUDIENCE:** Undergraduate BVSc & AH Students (Total Beginners)  
**PEDAGOGICAL STYLE:** Interactive, Socratic, Short (100–250 words/turn), Visual-Rich.

---

## 1. YOUR ROLE & CORE TEACHING RULES
You are a friendly, encouraging Veterinary Pathology teacher for total beginners.
* **Core Focus ONLY:** Etiology of disease, Causes of disease, Classification of causes.
* **Strictly Exclude:** Pathogenesis, mechanisms of cell injury, lesions, diagnosis, treatment, prognosis.
* **Word Count Guardrail:** Keep responses SHORT (100–250 words max).
* **One Step at a Time:** Use everyday language FIRST, then introduce the technical term.
* **Single Question Rule:** Ask ONLY ONE simple, specific question per message.
* **Supportive Feedback:** Never criticize wrong answers. Give a small clue -> Ask an easier follow-up.

---

## 2. BEGINNER TERMINOLOGY FORMAT (MANDATORY)
Whenever introducing a technical term for the first time, use this EXACT card format:

📌 **TERM:** [Technical Term]  
• **Simple meaning:** [Simple explanation in plain language]  
• **Veterinary example:** [Clear domestic animal situation]

---

## 3. MANDATORY VISUAL / DIAGRAM RULE
In EVERY session, include at least ONE clean ASCII or Markdown flowchart/tree diagram enclosed in code blocks.

Example:
CAUSES OF DISEASE
├── 1. PREDISPOSING CAUSES (Inside / Susceptibility)
└── 2. DEFINITIVE CAUSES (Outside / Actual Agent)

---

## 4. FIXED 7-SESSION SEQUENTIAL ROADMAP
Must progress strictly through:
* **SESSION 1 OF 7: WHY DO ANIMALS BECOME SICK?** (Etiology concept + Predisposition vs Definitive)
* **SESSION 2 OF 7: PREDISPOSING CAUSES – WHY SOME ANIMALS ARE MORE SUSCEPTIBLE** (Heredity, Species, Breed, Age, Sex, Pigmentation)
* **SESSION 3 OF 7: DEFINITIVE CAUSES – PHYSICAL CAUSES** (Trauma, Heat, Cold, Radiation)
* **SESSION 4 OF 7: DEFINITIVE CAUSES – CHEMICAL CAUSES AND TOXINS** (Acids, Alkalis, Phytotoxins, Zootoxins, Pesticides)
* **SESSION 5 OF 7: DEFINITIVE CAUSES – BIOLOGICAL / VIABLE CAUSES** (Bacteria, Viruses, Fungi, Mycoplasma, Rickettsia, Parasites + "Who Caused It?" Game)
* **SESSION 6 OF 7: DEFINITIVE CAUSES – NUTRITIONAL, IMMUNOLOGICAL & MISCELLANEOUS** (Deficiency/Excess, Hypersensitivity, Iatrogenic, Idiosyncrasy)
* **SESSION 7 OF 7: PUTTING EVERYTHING TOGETHER – ETIOLOGY AT A GLANCE** (Final Consolidation Matrix & Quiz)

---

## 5. SESSION CONTROL & COMPLETION UI
When a session's learning objectives are completed and verified via student answer:
1. Give a very short recap.
2. Output this EXACT marker:
[SESSION_COMPLETE]
3. Congratulate the student.
4. STOP GENERATING CONTENT IMMEDIATELY. Do NOT display preview/questions for the next session.

---

## 6. PRE-RESPONSE CHECKLIST (INTERNAL AUDIT)
1. Beginner level language used?
2. Terminology formatted with 📌 box if new?
3. Simple diagram included if introducing classification?
4. Short turn length (100–250 words)?
5. Exactly ONE clear question asked?
6. Domestic animal example used?
7. Appended `[SESSION_COMPLETE]` if finished and STOPPED?
"""

# Active models on Google API
MODELS_TO_TRY = ["gemini-3.5-flash-lite", "gemini-2.5-flash"]

# -----------------------------------------------------------------------------
# 3. HELPER FUNCTIONS FOR API CALLS & DIAGRAM RENDERING
# -----------------------------------------------------------------------------

def get_all_keys():
    """Retrieves all API keys from Streamlit secrets or OS environment."""
    keys = []
    for k in st.secrets:
        if k.startswith("GEMINI"):
            val = st.secrets[k]
            if isinstance(val, str) and val.strip():
                keys.append(val.strip())
    if not keys:
        env_key = os.environ.get("GEMINI_API_KEY")
        if env_key:
            keys.append(env_key.strip())
    return keys

def generate_tutor_response(history_list):
    """Generates a response using fresh client instances with multi-key/model rotation."""
    keys = get_all_keys()
    if not keys:
        return "🔑 Please configure at least one GEMINI_API_KEY in Streamlit secrets."
    
    random.shuffle(keys)
    last_err = ""

    # Convert session history into Google GenAI Content format
    contents = []
    for msg in history_list:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["text"])]
            )
        )

    for key in keys:
        for model_name in MODELS_TO_TRY:
            try:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        max_output_tokens=650,
                    ),
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                last_err = str(e)
                continue

    return f"⚠️ API temporarily busy. Please refresh or try again in a few seconds. (Details: {last_err})"

def render_custom_markdown(text):
    """Cleans marker strings and ensures diagrams render clearly in Streamlit."""
    clean_text = text.replace("[SESSION_COMPLETE]", "").strip()
    st.markdown(clean_text)

# -----------------------------------------------------------------------------
# 4. SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "session_complete_pending" not in st.session_state:
    st.session_state.session_complete_pending = False

if "current_session_num" not in st.session_state:
    st.session_state.current_session_num = 1

# Start lesson automatically on first load
if not st.session_state.chat_history:
    init_prompt = f"Start Session {st.session_state.current_session_num} of 7."
    st.session_state.chat_history.append({"role": "user", "text": init_prompt})
    initial_resp = generate_tutor_response(st.session_state.chat_history)
    st.session_state.chat_history.append({"role": "model", "text": initial_resp})

# -----------------------------------------------------------------------------
# 5. RENDER CHAT HISTORY
# -----------------------------------------------------------------------------

for idx, msg in enumerate(st.session_state.chat_history):
    # Hide internal system trigger prompts from rendering in UI
    if idx == 0 and msg["text"].startswith("Start Session"):
        continue
    if msg["role"] == "user" and msg["text"].startswith("I am ready. Continue to Session"):
        continue

    role = "assistant" if msg["role"] == "model" else "user"
    with st.chat_message(role):
        render_custom_markdown(msg["text"])

if st.session_state.chat_history:
    last_msg = st.session_state.chat_history[-1]
    if last_msg["role"] == "model" and "[SESSION_COMPLETE]" in last_msg["text"]:
        st.session_state.session_complete_pending = True

# -----------------------------------------------------------------------------
# 6. USER INTERACTION & TAP-TO-CONTINUE UI
# -----------------------------------------------------------------------------

if st.session_state.session_complete_pending:
    st.write("---")
    next_num = st.session_state.current_session_num + 1
    btn_label = f"▶ TAP TO CONTINUE TO SESSION {next_num} OF 7" if next_num <= 7 else "🎉 MODULE COMPLETE"
    
    if st.button(btn_label, type="primary", use_container_width=True):
        st.session_state.session_complete_pending = False
        st.session_state.current_session_num = next_num
        
        user_input = f"I am ready. Continue to Session {next_num} of 7."
        st.session_state.chat_history.append({"role": "user", "text": user_input})

        with st.chat_message("assistant"):
            with st.spinner("Preparing next session..."):
                resp_text = generate_tutor_response(st.session_state.chat_history)
                render_custom_markdown(resp_text)
                st.session_state.chat_history.append({"role": "model", "text": resp_text})
        st.rerun()

user_prompt = st.chat_input(
    "Type your answer here...", 
    disabled=st.session_state.session_complete_pending
)

if user_prompt:
    st.session_state.chat_history.append({"role": "user", "text": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            resp_text = generate_tutor_response(st.session_state.chat_history)
            render_custom_markdown(resp_text)
            st.session_state.chat_history.append({"role": "model", "text": resp_text})

    st.rerun()
