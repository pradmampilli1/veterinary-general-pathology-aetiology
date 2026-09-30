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

if "live_session_data" not in st.session_state:
    st.session_state.live_session_data = None

if "completed_sessions" not in st.session_state:
    st.session_state.completed_sessions = []

if "current_session_num" not in st.session_state:
    st.session_state.current_session_num = 1

if "bystander_mode" not in st.session_state:
    st.session_state.bystander_mode = False

if "bystander_reason" not in st.session_state:
    st.session_state.bystander_reason = ""

if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = ""

if "show_next_button" not in st.session_state:
    st.session_state.show_next_button = False

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
# 4. MASTER CURRICULUM SYSTEM PROMPT (STRUCTURED JSON)
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = r"""
# SYSTEM PROMPT: STRUCTURED VETERINARY PATHOLOGY TUTOR

**MODULE:** ETIOLOGY AND CLASSIFICATION OF DISEASE  
**TARGET AUDIENCE:** BVSc & AH First-Year Students (CVAS Pookode)  
**PEDAGOGICAL STYLE:** Micro-Socratic, Ultra-Concise, Beginner Language, Strict MCQ-Driven.

You must output ONLY valid JSON matching this exact structure, with no markdown code blocks around it. Do not include conversational filler.

JSON STRUCTURE REQUIRED:
{
  "title": "Session Title (e.g., Session X of 7 - Topic)",
  "scenario": "Short clinical or farm scenario using simple livestock examples (under 70 words). Never define technical terms early.",
  "question": "The core question for the student.",
  "options": [
    "A) First choice text",
    "B) Second choice text",
    "C) Third choice text"
  ],
  "correct_option": "A",
  "feedback_correct": "Positive reinforcement and conceptual explanation.",
  "feedback_incorrect": "Gentle guidance without revealing the answer.",
  "term_card": {
    "term": "Technical term name",
    "meaning": "Simple everyday meaning",
    "example": "Primary veterinary example"
  },
  "recap": "One sentence summary recap."
}
"""

MODELS_TO_TRY = [
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

# -----------------------------------------------------------------------------
# 5. PRESERVED API KEY RETRIEVAL & ROTATION LOGIC
# -----------------------------------------------------------------------------
def load_backup_curriculum():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "curriculum_backup.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def get_all_keys():
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

def fetch_structured_session_from_ai(session_num, student_name):
    keys = get_all_keys()
    if not keys:
        st.session_state.bystander_reason = "No API Key found in Streamlit Secrets"
        return None

    random.shuffle(keys)
    prompt = f"Generate Session {session_num} of 7 for student {student_name} under the Department of Veterinary Pathology, CVAS Pookode. Focus strictly on the curriculum module: Etiology and Classification of Disease. Ensure exactly 3 distinct MCQ options (A, B, C)."

    payload = {
        "contents": [{"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": 800
        }
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    last_err = ""

    for key in keys:
        for model_name in MODELS_TO_TRY:
            # Using v1beta endpoint reliably
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
            req = urllib.request.Request(
                url, data=payload_bytes, headers={"Content-Type": "application/json"}, method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=12) as response:
                    if response.status == 200:
                        res_body = json.loads(response.read().decode("utf-8"))
                        candidates = res_body.get("candidates", [])
                        if candidates:
                            text_out = candidates[0].get("content", {}).get("parts", [])[0]["text"]
                            text_out = text_out.replace("```json", "").replace("```", "").strip()
                            return json.loads(text_out)
            except urllib.error.HTTPError as e:
                err_detail = e.read().decode("utf-8")
                last_err = f"HTTP {e.code} on {model_name}: {err_detail[:100]}"
                continue
            except Exception as e:
                last_err = f"Error on {model_name}: {str(e)}"
                continue

    st.session_state.bystander_reason = f"REST Error or Rate Limit: {last_err}"
    return None

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
        st.session_state.live_session_data = None
        st.session_state.completed_sessions = []
        st.session_state.current_session_num = 1
        st.session_state.bystander_mode = False
        st.rerun()

st.markdown(
    f"👋 **Welcome, {st.session_state.student_name}!**\n\n"
    f"*Department of Veterinary Pathology, CVAS, Pookode — BVSc & AH Curriculum*"
)
st.write("---")

# -----------------------------------------------------------------------------
# 7. INITIALIZE SESSION DATA
# -----------------------------------------------------------------------------
if st.session_state.current_session_num <= 7:
    if not st.session_state.live_session_data and not st.session_state.bystander_mode:
        with st.spinner(f"Preparing Session {st.session_state.current_session_num} of 7..."):
            ai_data = fetch_structured_session_from_ai(st.session_state.current_session_num, st.session_state.student_name)
            if ai_data:
                st.session_state.live_session_data = ai_data
            else:
                st.session_state.bystander_mode = True

# -----------------------------------------------------------------------------
# 8. RENDER COMPLETED EXPANDERS
# -----------------------------------------------------------------------------
for comp in st.session_state.completed_sessions:
    with st.expander(f"✅ Completed: {comp['title']}", expanded=False):
        st.write(comp['scenario'])
        st.success(comp['feedback'])
        term = comp['term_card']
        st.markdown(
            f"📌 **TERM: {term['term']}**\n"
            f"• **Simple meaning:** {term['meaning']}\n"
            f"• **Veterinary example:** {term['example']}"
        )

# -----------------------------------------------------------------------------
# 9. MAIN INTERACTIVE UI (LIVE OR OFFLINE BYSTANDER BACKUP)
# -----------------------------------------------------------------------------
if st.session_state.bystander_mode:
    st.warning("⚡ **Bystander Backup Engine Active** (Running in high-reliability offline mode)")
    if st.session_state.bystander_reason:
        st.caption(f"ℹ️ *Diagnostic Note: {st.session_state.bystander_reason}*")
    
    if st.button("🔄 Switch Back to Live AI Connection", type="primary"):
        st.session_state.bystander_mode = False
        st.session_state.bystander_reason = ""
        st.rerun()
    
    st.write("---")
    backup_data = load_backup_curriculum()
    sess_key = f"session_{st.session_state.current_session_num}"
    if backup_data and sess_key in backup_data:
        curr = backup_data[sess_key]
        active_data = {
            "title": curr["title"],
            "scenario": curr["scenario"],
            "question": curr["question"],
            "options": curr["options"],
            "correct_option": curr["correct_option"],
            "feedback_correct": curr["feedback_correct"],
            "feedback_incorrect": curr["feedback_incorrect"],
            "term_card": curr["term_card"],
            "recap": curr["recap"]
        }
    else:
        active_data = None
else:
    active_data = st.session_state.live_session_data

if st.session_state.current_session_num > 7:
    st.balloons()
    st.success(f"🎉 **CONGRATULATIONS {st.session_state.student_name.upper()}! MODULE COMPLETED SUCCESSFULLY!**")
    st.markdown(f"**Admission No:** `{st.session_state.student_id}`")
    
    backup_data = load_backup_curriculum()
    if backup_data and "completion_matrix" in backup_data:
        matrix = backup_data["completion_matrix"]
        st.markdown(f"### {matrix['header']}")
        table_md = "| Etiological Category | Primary Definition | Primary Veterinary Example |\n| :--- | :--- | :--- |\n"
        for row in matrix["rows"]:
            table_md += f"| **{row['category']}** | {row['definition']} | {row['example']} |\n"
        st.markdown(table_md)
    
    if st.button("🔄 Restart Module", type="primary"):
        st.session_state.current_session_num = 1
        st.session_state.completed_sessions = []
        st.session_state.live_session_data = None
        st.session_state.bystander_mode = False
        st.rerun()

elif active_data:
    st.subheader(active_data["title"])
    st.write(active_data["scenario"])
    st.write(f"**Question:** {active_data['question']}")
    
    user_choice = st.radio(
        "Select your answer:", 
        active_data["options"], 
        key=f"radio_session_{st.session_state.current_session_num}"
    )
    
    if not st.session_state.show_next_button:
        if st.button("Submit Answer", type="primary"):
            selected_letter = user_choice.split(")")[0].strip()
            
            if selected_letter == active_data["correct_option"]:
                st.session_state.last_feedback = f"✅ **Correct!** {active_data['feedback_correct']}"
                st.session_state.show_next_button = True
                
                if not any(c['title'] == active_data['title'] for c in st.session_state.completed_sessions):
                    st.session_state.completed_sessions.append({
                        "title": active_data["title"],
                        "scenario": active_data["scenario"],
                        "feedback": active_data["feedback_correct"],
                        "term_card": active_data["term_card"]
                    })
                st.rerun()
            else:
                st.warning(active_data["feedback_incorrect"])
    
    if st.session_state.show_next_button:
        st.success(st.session_state.last_feedback)
        term = active_data["term_card"]
        st.markdown(
            f"📌 **TERM: {term['term']}**\n"
            f"• **Simple meaning:** {term['meaning']}\n"
            f"• **Veterinary example:** {term['example']}"
        )
        st.write("---")
        st.write(f"**Recap:** {active_data['recap']}")
        
        next_num = st.session_state.current_session_num + 1
        btn_label = f"▶ TAP TO CONTINUE TO SESSION {next_num} OF 7" if next_num <= 7 else "🎉 VIEW FINAL MATRIX"
        
        if st.button(btn_label, type="primary", use_container_width=True):
            st.session_state.show_next_button = False
            st.session_state.last_feedback = ""
            st.session_state.current_session_num = next_num
            st.session_state.live_session_data = None
            st.rerun()
