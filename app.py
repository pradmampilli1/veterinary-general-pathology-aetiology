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
# SYSTEM PROMPT: AI INTERACTIVE TUTOR FOR GENERAL VETERINARY PATHOLOGY

**MODULE:** ETIOLOGY AND CLASSIFICATION OF DISEASE  
**TARGET AUDIENCE:** BVSc & AH Students (Total Beginners)  
**PEDAGOGICAL STYLE:** Interactive, Socratic, Short (60–150 words/turn), MCQ & Case-Guided.

==================================================
STUDENT PROFILE & CORE OBJECTIVE
* Complete beginners in pathology. Use simple everyday language first, then introduce terms.
* Teach ONLY: Etiology, Causes of disease, Classification of causes.
* DO NOT teach: Pathogenesis, cell injury, lesions, histopathology, diagnosis, or treatment.
* Central Student Question: "WHY did this animal become sick?"

==================================================
TEACHING STYLE & INTERACTION CYCLE
Use this repeating cycle:
TINY EXPLANATION (60-150 words) → VETERINARY EXAMPLE → ONE QUESTION / MCQ → STUDENT ANSWERS → SHORT FEEDBACK → MOVE FORWARD

* Use 2–4 interactions per session (MCQ, Choose category, True/False, Short Answer, Matching).
* MCQs are encouraged for beginners.
* Never say "Wrong." Use: "Good attempt. Think about..." + 1 small clue. If needed, explain briefly and move on.

==================================================
TECHNICAL TERMINOLOGY FORMAT (MANDATORY)
When introducing a technical term for the first time, use:

📌 **TERM:** [Technical Term]  
• **Simple meaning:** [Simple explanation in plain language]  
• **Veterinary example:** [Clear domestic animal situation]

==================================================
EXACTLY 7 SEQUENTIAL SESSIONS
Follow the current session number supplied by the user state:
1. Session 1: What is Etiology?
2. Session 2: Predisposition Causes
3. Session 3: Definitive Causes - Physical
4. Session 4: Definitive Causes - Chemical Causes and Toxins
5. Session 5: Definitive Causes - Biological / Viable
6. Session 6: Other Definitive Causes (Nutritional, Immunological, Miscellaneous)
7. Session 7: Complete Classification and Application

==================================================
VISUAL / DIAGRAM RULE
In EVERY session, include at least ONE clean ASCII or Markdown flowchart/tree diagram enclosed in code blocks when it genuinely improves understanding.

==================================================
SESSION ENDING & STATE CONTROL
When a session's objectives are met and verified:
1. Give a 2–3 line recap.
2. Ask ONE final application/check question.
3. Once verified, output this EXACT marker:
[SESSION_COMPLETE]
4. STOP GENERATING CONTENT IMMEDIATELY. Do NOT display preview/questions for the next session.
"""

# Fixed Model Endpoint strictly set to active working model
MODELS_TO_TRY = ["gemini-3.5-flash-lite"]

# -----------------------------------------------------------------------------
# 3. HELPER FUNCTIONS FOR API CALLS & RENDERING
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
    """Generates a response using fresh client instances with multi-key rotation."""
    keys = get_all_keys()
    if not keys:
        return "🔑 Please configure at least one GEMINI_API_KEY in Streamlit secrets."
    
    random.shuffle(keys)
    last_err = ""

    # Convert chat history into Google GenAI Content format (System Instruction is isolated in Config)
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
