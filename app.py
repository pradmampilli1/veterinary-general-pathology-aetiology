import os
import random
import json
import urllib.request
import urllib.error
import concurrent.futures
import streamlit as st

# -----------------------------------------------------------------------------
# 1. STREAMLIT PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Veterinary Pathology AI Tutor",
    page_icon="🐾",
    layout="centered",
)

# -----------------------------------------------------------------------------
# 2. SESSION STATE & AUTHENTICATION INITIALIZATION
# -----------------------------------------------------------------------------
if "student_logged_in" not in st.session_state:
    st.session_state.student_logged_in = False

if "student_name" not in st.session_state:
    st.session_state.student_name = ""

if "student_id" not in st.session_state:
    st.session_state.student_id = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "completed_bystander_sessions" not in st.session_state:
    st.session_state.completed_bystander_sessions = []

if "session_complete_pending" not in st.session_state:
    st.session_state.session_complete_pending = False

if "current_session_num" not in st.session_state:
    st.session_state.current_session_num = 1

if "bystander_mode" not in st.session_state:
    st.session_state.bystander_mode = False

if "bystander_reason" not in st.session_state:
    st.session_state.bystander_reason = ""

# -----------------------------------------------------------------------------
# 3. ISOLATED STUDENT LOGIN SCREEN
# -----------------------------------------------------------------------------
if not st.session_state.student_logged_in:
    st.title("🐾 General Veterinary Pathology AI Tutor")
    st.caption("Module: Etiology and Classification of Disease (BVSc & AH)")
    st.markdown("*Department of Veterinary Pathology, CVAS, Pookode*")
    st.write("---")
    
    st.subheader("👨‍🎓 Student Access Login")
    st.info("Please enter your details to start the learning session.")
    
    with st.form("student_login_form"):
        name_input = st.text_input("Full Name:", placeholder="e.g., Ananya R.")
        id_input = st.text_input("Admission Number / Roll No:", placeholder="e.g., 2024-04-102")
        submit_button = st.form_submit_button("🚀 Start Learning Session", type="primary")
        
        if submit_button:
            if name_input.strip() and id_input.strip():
                st.session_state.student_name = name_input.strip()
                st.session_state.student_id = id_input.strip()
                st.session_state.student_logged_in = True
                st.rerun()
            else:
                st.error("Please enter both your Full Name and Admission Number to proceed.")
    
    st.stop()

# -----------------------------------------------------------------------------
# 4. PEDAGOGICAL SYSTEM PROMPT DEFINITION
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = r"""
# SYSTEM PROMPT: AI INTERACTIVE TUTOR FOR GENERAL VETERINARY PATHOLOGY

**MODULE:** ETIOLOGY AND CLASSIFICATION OF DISEASE  
**TARGET AUDIENCE:** BVSc & AH Students (Total Beginners)  
**PEDAGOGICAL STYLE:** Micro-Socratic, Ultra-Concise (50–90 words), MCQ-Driven.

==================================================
STRICT PEDAGOGICAL RULES
1. **WORD LIMIT**: Your response MUST be between 50 and 90 words total. No meta-commentary or filler.
2. **MANDATORY MCQ**: Every response MUST end with a single 3-option multiple-choice question (A, B, C). NEVER ask broad open-ended questions.
3. **NO EARLY DEFINITIONS**: Do NOT define "Etiology" or technical terms until after the student answers the scenario question.
4. **FORMATTING**: Standard Markdown only. Place each MCQ option on its own line.

==================================================
TERMINOLOGY CARD FORMAT (WHEN INTRODUCING A TERM)
📌 **TERM:** [Term]  
• **Definition:** [1 concise sentence]  
• **Veterinary Example:** [1 short clinical example]

==================================================
SESSION ENDING
When session objectives are complete, output:
[SESSION_COMPLETE]
"""

# Active production endpoint targets
MODELS_TO_TRY = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-1.5-flash"
]

# -----------------------------------------------------------------------------
# 5. HELPER FUNCTIONS FOR REST API & BYSTANDER FALLBACK
# -----------------------------------------------------------------------------

def load_backup_curriculum():
    """Loads the frozen fallback JSON dataset reliably using absolute pathing."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "curriculum_backup.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def get_all_keys():
    """Retrieves all API keys from Streamlit secrets or OS environment."""
    keys = []
    try:
        for k in st.secrets:
            val = st.secrets[k]
            if isinstance(val, str) and val.strip():
                if k.upper().startswith("GEMINI") or k.upper() in ["API_KEY", "GOOGLE_API_KEY"]:
                    keys.append(val.strip())
    except Exception:
        pass

    if not keys:
        for env_var in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_KEY"]:
            env_val = os.environ.get(env_var)
            if env_val and env_val.strip():
                keys.append(env_val.strip())

    return list(set(keys))

def _call_gemini_rest_api(key, contents):
    """Executes REST API requests using standard urllib over current production endpoints."""
    formatted_contents = []
    for idx, msg in enumerate(contents):
        text_content = msg["parts"][0]
        if idx == 0:
            text_content = f"{SYSTEM_PROMPT}\n\n[STUDENT CONVERSATION START]\n{text_content}"
            
        formatted_contents.append({
            "role": msg["role"],
            "parts": [{"text": text_content}]
        })

    payload = {
        "contents": formatted_contents,
        "generationConfig": {
            "maxOutputTokens": 800  # Increased token limit to prevent mid-sentence truncation
        }
    }

    payload_bytes = json.dumps(payload).encode("utf-8")
    last_err = ""

    for model_name in MODELS_TO_TRY:
        for ver in ["v1beta", "v1"]:
            url = f"https://generativelanguage.googleapis.com/{ver}/models/{model_name}:generateContent?key={key}"
            req = urllib.request.Request(
                url,
                data=payload_bytes,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        res_body = json.loads(response.read().decode("utf-8"))
                        candidates = res_body.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                return parts[0]["text"], None
            except urllib.error.HTTPError as e:
                err_detail = e.read().decode("utf-8")
                last_err = f"HTTP {e.code} on {model_name} ({ver}): {err_detail[:100]}"
                continue
            except Exception as e:
                last_err = f"Exception on {model_name} ({ver}): {str(e)}"
                continue

    return None, f"REST Error: {last_err}"

def generate_tutor_response(history_list):
    """Generates response using live REST API with thread-safe execution."""
    keys = get_all_keys()
    if not keys:
        st.session_state.bystander_reason = "No API Key found in Streamlit Secrets"
        return None

    random.shuffle(keys)
    contents = []
    for msg in history_list:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [msg["text"]]
        })

    for key in keys:
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_call_gemini_rest_api, key, contents)
                result, err_msg = future.result(timeout=12)
                if result:
                    return result
                elif err_msg:
                    st.session_state.bystander_reason = err_msg
        except Exception as e:
            st.session_state.bystander_reason = f"Timeout or Connection Error: {str(e)}"
            continue

    if not st.session_state.bystander_reason:
        st.session_state.bystander_reason = "All Gemini model REST calls failed"
    return None

def render_custom_markdown(text):
    """Cleans marker strings and renders Markdown."""
    clean_text = text.replace("[SESSION_COMPLETE]", "").strip()
    st.markdown(clean_text)

# -----------------------------------------------------------------------------
# 6. HEADER & SIDEBAR PROFILE DISPLAY
# -----------------------------------------------------------------------------
st.title("🐾 General Veterinary Pathology AI Tutor")
st.caption("Module: Etiology and Classification of Disease (BVSc & AH)")

with st.sidebar:
    st.header("👨‍🎓 Student Profile")
    st.write(f"**Name:** {st.session_state.student_name}")
    st.write(f"**Admission No:** {st.session_state.student_id}")
    st.write(f"**Current Session:** {st.session_state.current_session_num} / 7")
    st.write("---")
    
    keys_found = len(get_all_keys())
    st.caption(f"🔑 API Keys Detected: {keys_found}")
    
    if st.button("🚪 Logout / Switch Student"):
        st.session_state.student_logged_in = False
        st.session_state.chat_history = []
        st.session_state.completed_bystander_sessions = []
        st.session_state.current_session_num = 1
        st.session_state.bystander_mode = False
        st.session_state.bystander_reason = ""
        st.rerun()

st.markdown(
    f"👋 **Welcome, {st.session_state.student_name}!**\n\n"
    f"*Department of Veterinary Pathology, CVAS, Pookode — BVSc & AH Curriculum*"
)
st.write("---")

# Start initial lesson ONLY AFTER successful login
if not st.session_state.chat_history and not st.session_state.completed_bystander_sessions:
    init_prompt = (
        f"Greeting: Welcome {st.session_state.student_name} to Session 1 on behalf of Department of Veterinary Pathology, CVAS, Pookode.\n"
        f"Scenario: At CVAS Pookode, two calves are housed together under identical management. After a sudden cold draft, Calf B develops severe coughing and fever, while Calf A remains active.\n"
        f"Task: Write a single response combining the greeting, the 2-sentence calf scenario, and a 3-option MCQ (A, B, C) asking what primary factor caused Calf B to fall ill. Keep total output under 90 words. Do NOT define Etiology yet!"
    )
    st.session_state.chat_history.append({"role": "user", "text": init_prompt})
    
    with st.spinner("Connecting to Pathology Tutor..."):
        live_resp = generate_tutor_response(st.session_state.chat_history)
        if live_resp:
            st.session_state.chat_history.append({"role": "model", "text": live_resp})
        else:
            st.session_state.bystander_mode = True

# -----------------------------------------------------------------------------
# 7. BYSTANDER MODE RENDERER (OFFLINE JSON FALLBACK ENGINE)
# -----------------------------------------------------------------------------
if st.session_state.bystander_mode:
    st.info("⚡ **Bystander Backup Engine Active** (Running in high-reliability offline mode)")
    if st.session_state.bystander_reason:
        st.caption(f"ℹ️ *Diagnostic Note: {st.session_state.bystander_reason}*")
    
    backup_data = load_backup_curriculum()
    
    for comp in st.session_state.completed_bystander_sessions:
        with st.expander(f"✅ Completed: {comp['title']}", expanded=False):
            st.write(comp['scenario'])
            st.success(comp['feedback'])
            term = comp['term_card']
            st.markdown(
                f"📌 **TERM: {term['term']}**\n"
                f"• **Simple meaning:** {term['meaning']}\n"
                f"• **Veterinary example:** {term['example']}"
            )
            st.caption(f"Recap: {comp['recap']}")

    if st.session_state.current_session_num > 7:
        st.balloons()
        st.success(f"🎉 **CONGRATULATIONS {st.session_state.student_name.upper()}! MODULE COMPLETED SUCCESSFULLY!**")
        st.markdown(f"**Admission No:** `{st.session_state.student_id}`")
        
        if backup_data and "completion_matrix" in backup_data:
            matrix = backup_data["completion_matrix"]
            st.markdown(f"### {matrix['header']}")
            
            table_md = "| Etiological Category | Primary Definition | Primary Veterinary Example |\n| :--- | :--- | :--- |\n"
            for row in matrix["rows"]:
                table_md += f"| **{row['category']}** | {row['definition']} | {row['example']} |\n"
            st.markdown(table_md)
        
        if st.button("🔄 Restart Module", type="primary"):
            st.session_state.current_session_num = 1
            st.session_state.completed_bystander_sessions = []
            st.session_state.session_complete_pending = False
            st.session_state.bystander_mode = False
            st.session_state.bystander_reason = ""
            st.rerun()

    else:
        sess_key = f"session_{st.session_state.current_session_num}"
        if backup_data and sess_key in backup_data:
            curr_session = backup_data[sess_key]
            
            salutation_text = curr_session["salutation"].format(student_name=st.session_state.student_name)
            st.markdown(f"**{salutation_text}**")
            
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
                    
                    if not any(c['title'] == curr_session['title'] for c in st.session_state.completed_bystander_sessions):
                        st.session_state.completed_bystander_sessions.append({
                            "title": curr_session["title"],
                            "scenario": curr_session["scenario"],
                            "feedback": curr_session["feedback_correct"],
                            "term_card": curr_session["term_card"],
                            "recap": curr_session["recap"]
                        })
                    
                    st.session_state.session_complete_pending = True
                else:
                    st.warning(curr_session.get("feedback_incorrect", "Good attempt! Re-read the scenario carefully and select the best matching option."))
            
            if st.session_state.session_complete_pending:
                st.write("---")
                next_num = st.session_state.current_session_num + 1
                btn_label = f"▶ TAP TO CONTINUE TO SESSION {next_num} OF 7" if next_num <= 7 else "🎉 VIEW FINAL ETIOLOGY MATRIX"
                
                if st.button(btn_label, type="primary", use_container_width=True):
                    st.session_state.session_complete_pending = False
                    st.session_state.current_session_num = next_num
                    st.rerun()
        else:
            st.error("Backup curriculum file missing or unreadable.")

# -----------------------------------------------------------------------------
# 8. LIVE AI MODE RENDERER
# -----------------------------------------------------------------------------
else:
    for idx, msg in enumerate(st.session_state.chat_history):
        if idx == 0 and "Greeting: Welcome" in msg["text"]:
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
            
            if next_num > 7:
                st.session_state.bystander_mode = True
                st.rerun()
            else:
                user_input = (
                    f"I am ready. Begin Session {next_num} of 7 now. Address {st.session_state.student_name} warmly. "
                    f"Present a 2-sentence scenario and end with a 3-option MCQ. Keep total output under 80 words."
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
