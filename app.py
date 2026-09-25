import streamlit as st
import google.generativeai as genai
import requests

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Veterinary Pathology Socratic Tutor",
    page_icon="🔬",
    layout="centered"
)

st.title("🔬 Veterinary General Pathology Tutor")
st.caption("Etiology & Causation of Diseases — Interactive Socratic Practice")

# Read Secrets
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", None)
except Exception:
    st.error("Missing secrets! Please configure GEMINI_API_KEY in Streamlit Advanced Settings.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# 2. LOGGING HELPER FUNCTION
# ==========================================
def log_to_google_sheet(student_name, roll_number, step, user_input, ai_response):
    if not WEBHOOK_URL:
        return
    
    payload = {
        "name": student_name,
        "roll_number": roll_number,
        "step": step,
        "answer": user_input,
        "feedback": ai_response
    }
    
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=3)
    except Exception:
        pass

# ==========================================
# 3. STUDENT REGISTRATION (SIDEBAR)
# ==========================================
st.sidebar.header("📋 Student Information")
student_name = st.sidebar.text_input("Full Name", placeholder="e.g., Dr. Ananya")
roll_number = st.sidebar.text_input("Roll Number / ID", placeholder="e.g., VET2026-042")

if not student_name or not roll_number:
    st.info("👈 Please enter your **Full Name** and **Roll Number** in the sidebar to begin the tutorial session.")
    st.stop()

st.sidebar.success(f"Active Session: **{student_name}** ({roll_number})")

if st.sidebar.button("🔄 Restart Etiology Session"):
    for key in ["messages", "step_count", "working_model"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ==========================================
# 4. STRICT SOCRATIC SYSTEM PROMPT
# ==========================================
SOCRATIC_SYSTEM_PROMPT = f"""
You are an expert Veterinary Pathology Professor leading a 2nd-year BVSc & AH student named {student_name} through the VCI syllabus.

STRICT CURRICULUM BOUNDARY:
Your SOLE goal is to test and guide the student on "ETIOLOGY & CAUSATION OF DISEASES IN ANIMALS". Do not deviate into treatment, prognosis, or unrelated general knowledge.

TOPIC SYLLABUS TO COVER IN ORDER:
1. Intrinsic Predisposing Causes:
   - Species / Genus immunity (e.g., Rinderpest in cattle vs human)
   - Breed susceptibility (e.g., Melanoma in Grey horses, Tumors in Bulldogs/Great Danes)
   - Age susceptibility (e.g., Strangles in foals vs adult tumors)
   - Sex & Coat pigment / Photodynamic sensitivity
   - Genetic/Inherited anomalies (Lethal: Atresia coli; Sub-lethal: Imperforate anus, Deafness in white cats)
   - Developmental defects (Agenesis, Hypoplasia, Freemartin, Hermaphrodite)
2. Extrinsic Exciting Causes:
   - Physical: Radiation, Thermal (Frostbite/Necrosis), Electricity, Atmospheric pressure (Brisket disease)
   - Mechanical: Concussion, Perforation, Laceration

PEDAGOGICAL RULES:
- ALWAYS assess the student's answer against Etiology concepts first.
- Praise correct intuition, correct any wrong terminology, and ask EXACTLY ONE logical follow-up question strictly related to the etiology syllabus above.
- Never write long lectures. Keep answers under 3 short sentences.
"""

# ==========================================
# 5. DYNAMIC MODEL RETRIEVAL
# ==========================================
@st.cache_resource
def get_available_models():
    try:
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                clean_name = m.name.replace("models/", "")
                available.append(clean_name)
        flash_models = [m for m in available if "flash" in m]
        other_models = [m for m in available if "flash" not in m]
        return flash_models + other_models
    except Exception:
        return ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-2.0-flash"]

# ==========================================
# 6. INITIALIZATION
# ==========================================
if "step_count" not in st.session_state:
    st.session_state.step_count = 1

if "working_model" not in st.session_state:
    model_candidates = get_available_models()
    st.session_state.working_model = model_candidates[0] if model_candidates else "gemini-1.5-flash-latest"

if "messages" not in st.session_state:
    st.session_state.messages = []
    initial_greeting = f"""Welcome {student_name}! Today we will explore **Etiology: The Causation of Diseases in Animals**.

Let's start with an interesting case observation:

In equine practice, an old **Grey horse** is significantly more likely to develop **Malignant Melanoma** than a bay or chestnut horse of the same age. Similarly, white-skinned animals suffer more frequently from sun-induced skin inflammation.

In disease causation, would you classify coat color or breed as an **Intrinsic Predisposing Cause** or an **Extrinsic Exciting Cause** of disease? What is your reasoning?"""
    
    st.session_state.messages.append({"role": "assistant", "content": initial_greeting})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 7. USER INPUT & CONTEXT-LIMITED STREAMING
# ==========================================
if user_prompt := st.chat_input("Type your response here..."):
    st.chat_message("user").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        success = False
        
        # Truncate context to last 6 messages to prevent topic drift
        recent_history = st.session_state.messages[-6:-1]
        
        candidates = [st.session_state.working_model] + get_available_models()
        candidate_list = list(dict.fromkeys(candidates))
        
        for model_candidate in candidate_list:
            try:
                active_model = genai.GenerativeModel(
                    model_name=model_candidate,
                    system_instruction=SOCRATIC_SYSTEM_PROMPT
                )
                
                chat_history = []
                for m in recent_history:
                    role = "user" if m["role"] == "user" else "model"
                    chat_history.append({"role": role, "parts": [m["content"]]})
                
                chat_session = active_model.start_chat(history=chat_history)
                st.session_state.working_model = model_candidate

                response = chat_session.send_message(user_prompt, stream=True)
                for chunk in response:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                success = True
                break
                
            except Exception:
                continue
        
        if success:
            log_to_google_sheet(
                student_name=student_name,
                roll_number=roll_number,
                step=st.session_state.step_count,
                user_input=user_prompt,
                ai_response=full_response
            )
            st.session_state.step_count += 1
        else:
            st.error("Unable to reach Google API across active models. Please check your API key.")
