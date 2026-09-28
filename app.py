import os
import random
import json
import concurrent.futures
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
STRICT SOCRATIC OPENING RULE (NO EARLY DEFINITIONS)
When starting a session:
1. Begin with a short domestic animal situation.
2. Ask ONE simple question or MCQ to make the student think.
3. NEVER introduce technical terms (like "Etiology" or "Predisposition") in your first message. Introduce terms ONLY AFTER the student answers!

==================================================
TEACHING STYLE & FORMAT
* Use 60–150 words per turn.
* Format MCQs on separate lines (A) ..., B) ..., C) ...). NEVER use raw HTML tags like `<br>`.
* Never say "Wrong." Use "Good attempt..." + 1 clue.

==================================================
TECHNICAL TERMINOLOGY FORMAT
📌 **TERM:** [Technical Term]  
• **Simple meaning:** [Simple explanation]  
• **Veterinary example:** [Clear animal situation]

==================================================
SESSION ENDING
When a session's objectives are met:
1. Give a brief recap.
2. Output: [SESSION_COMPLETE]
3. STOP GENERATING CONTENT IMMEDIATELY.
"""

MODELS_TO_TRY = ["gemini-3.5-flash-lite"]

# -----------------------------------------------------------------------------
# 3. HELPER FUNCTIONS FOR API & BYSTANDER FALLBACK
# -----------------------------------------------------------------------------

def load_backup_curriculum():
    """Loads the frozen fallback JSON dataset."""
    try:
        with open("curriculum_backup.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

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

def _single_api_call(key, contents):
    """Executes a single API request."""
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
        except Exception:
            continue
    return None

def generate_tutor_response(history_list):
    """Generates response using live API with a strict 8-second timeout."""
    keys = get_all_keys()
    if not keys:
        return None

    random.shuffle(keys)
    contents = []
    for msg in history_list:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["text"])]
            )
        )

    # Try keys with a strict 8-second execution cap
    for key in keys:
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_single_api_call, key, contents)
                result = future.result(timeout=8) # 8-second timeout cap
                if result:
                    return result
        except Exception:
            continue

    return None

def render_custom_markdown(text):
    """Cleans marker strings and renders Markdown."""
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

if "bystander_mode" not in st.session_state:
    st.session_state.bystander_mode = False

# Start lesson on first load
if not st.session_state.chat_history:
    init_prompt = (
        "Begin Session 1 of 7 now. "
        "Start with the scenario of two calves on the same farm where one becomes sick and one stays healthy. "
        "Ask ONE MCQ to make the student think about why. "
        "Do NOT introduce technical terms like 'Etiology' yet."
    )
    st.session_state.chat_history.append({"role": "user", "text": init_prompt})
    
    live_resp = generate_tutor_response(st.session_state.chat_history)
    if live_resp:
        st.session_state.chat_history.append({"role": "model", "text": live_resp})
    else:
        st.session_state.bystander_mode = True

# -----------------------------------------------------------------------------
# 5. BYSTANDER MODE RENDERER (OFFLINE FALLBACK ENGINE)
# -----------------------------------------------------------------------------

if st.session_state.bystander_mode:
    st.info("⚡ **Bystander Backup Engine Active** (Running in high-reliability offline mode)")
    
    backup_data = load_backup_curriculum()
    sess_key = f"session_{st.session_state.current_session_num}"
    
    if backup_data and sess_key in backup_data:
        curr_session = backup_data[sess_key]
        
        st.subheader(curr_session["title"])
        st.write(curr_session["scenario"])
        st.write(f"**Question:** {curr_session['question']}")
        
        user_choice = st.radio(
            "Select your answer:", 
            curr_session["options"], 
            key=f"radio_{st.session_state.current_session_num}"
        )
        
        if st.button("Submit Answer", type="primary"):
            selected_letter = user_choice.split(")")[0].strip()
            
            if selected_letter == curr_session["correct_option"]:
                st.success(curr_session["feedback_correct"])
                
                term = curr_session["term_card"]
                st.markdown(
                    f"📌 **TERM: {term['term']}**\n"
                    f"• **Simple meaning:** {term['meaning']}\n"
                    f"• **Veterinary example:** {term['example']}"
                )
                
                st.write("---")
                st.write(f"**Recap:** {curr_session['recap']}")
                st.session_state.session_complete_pending = True
            else:
                st.warning("Good attempt! Think about what specifically acted upon or entered the sick animal.")
        
        if st.session_state.session_complete_pending:
            st.write("---")
            next_num = st.session_state.current_session_num + 1
            btn_label = f"▶ TAP TO CONTINUE TO SESSION {next_num} OF 7" if next_num <= 7 else "🎉 MODULE COMPLETE"
            
            if st.button(btn_label, type="primary", use_container_width=True):
                st.session_state.session_complete_pending = False
                st.session_state.current_session_num = next_num
                st.rerun()
    else:
        st.error("Backup curriculum file missing or unreadable.")

# -----------------------------------------------------------------------------
# 6. LIVE AI MODE RENDERER
# -----------------------------------------------------------------------------

else:
    for idx, msg in enumerate(st.session_state.chat_history):
        if idx == 0 and "Begin Session 1 of 7 now" in msg["text"]:
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

    if st.session_state.session_complete_pending:
        st.write("---")
        next_num = st.session_state.current_session_num + 1
        btn_label = f"▶ TAP TO CONTINUE TO SESSION {next_num} OF 7" if next_num <= 7 else "🎉 MODULE COMPLETE"
        
        if st.button(btn_label, type="primary", use_container_width=True):
            st.session_state.session_complete_pending = False
            st.session_state.current_session_num = next_num
            
            user_input = (
                f"I am ready. Begin Session {next_num} of 7 now. "
                f"Start with a simple story/scenario and ask ONE question. Do NOT define terms in the opening message."
            )
            st.session_state.chat_history.append({"role": "user", "text": user_input})

            with st.chat_message("assistant"):
                with st.spinner("Preparing next session..."):
                    resp_text = generate_tutor_response(st.session_state.chat_history)
                    if resp_text:
                        render_custom_markdown(resp_text)
                        st.session_state.chat_history.append({"role": "model", "text": resp_text})
                    else:
                        st.session_state.bystander_mode = True
                        st.rerun()
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
                if resp_text:
                    render_custom_markdown(resp_text)
                    st.session_state.chat_history.append({"role": "model", "text": resp_text})
                else:
                    st.session_state.bystander_mode = True
                    st.rerun()

        st.rerun()
