import os
import random
import json
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
# 4. SYSTEM PROMPT DEFINITION
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
1. Address the student respectfully and warmly by name only (e.g., "Welcome, [Name]!").
2. Begin with a short domestic animal situation.
3. Ask ONE simple question or MCQ to make the student think.
4. NEVER introduce technical terms (like "Etiology" or "Predisposition") in your first message. Introduce terms ONLY AFTER the student answers!

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

# Verified Active Gemini Model Priority Chain
MODELS_TO_TRY = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash"
]

# -----------------------------------------------------------------------------
# 5. HELPER FUNCTIONS FOR API & BYSTANDER FALLBACK
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

def _single_api_call(key, contents):
    """Executes API request using the official Google GenAI SDK with active models."""
    last_err = None
    
    # Primary GenAI SDK
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)
        for model_name in MODELS_TO_TRY:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        max_output_tokens=650,
                    ),
                )
                if response and response.text:
                    return response.text, None
            except Exception as err:
                last_err = str(err)
                continue
    except Exception as err:
        last_err = str(err)

    # Legacy Fallback GenAI SDK
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=key)
        for model_name in MODELS_TO_TRY:
            try:
                model = legacy_genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=SYSTEM_PROMPT
                )
                formatted_prompt = contents[-1]["parts"][0] if isinstance(contents[-1], dict) else str(contents[-1])
                response = model.generate_content(formatted_prompt)
                if response and response.text:
                    return response.text, None
            except Exception as err:
                last_err = str(err)
                continue
    except Exception as err:
        last_err = str(err)

    return None, last_err

def generate_tutor_response(history_list):
    """Generates response using live API with an 8-second timeout."""
    keys = get_all_keys()
    if not keys:
        st.session_state.bystander_reason = "No API Key found in Streamlit Secrets"
        return None

    random.shuffle(keys)
    contents = []
    for msg in history_list:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            {
                "role": role,
                "parts": [msg["text"]]
            }
        )

    for key in keys:
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_single_api_call, key, contents)
                result, err_msg = future.result(timeout=8)
                if result:
                    return result
                elif err_msg:
                    st.session_state.bystander_reason = f"API Error: {err_msg}"
        except Exception as e:
            st.session_state.bystander_reason = f"API Timeout or Connection Exception: {str(e)}"
            continue

    if not st.session_state.bystander_reason:
        st.session_state.bystander_reason = "All model attempts failed or key quota exceeded"
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
        f"Begin Session 1 of 7 now. Welcome the student warmly: 'Welcome, {st.session_state.student_name}! "
        f"Department of Veterinary Pathology, CVAS, Pookode welcomes you to Session 1.' "
        f"Start with the scenario of two calves at CVAS Pookode where one becomes sick and one stays healthy. "
        f"Ask ONE MCQ to make the student think about why. "
        f"Do NOT introduce technical terms like 'Etiology' yet."
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
            
            if next_num > 7:
                st.session_state.bystander_mode = True
                st.rerun()
            else:
                user_input = (
                    f"I am ready. Begin Session {next_num} of 7 now. Address {st.session_state.student_name} warmly by name. "
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
