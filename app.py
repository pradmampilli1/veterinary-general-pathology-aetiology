import streamlit as st
import google.generativeai as genai
import requests
import json

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Veterinary Pathology Socratic Tutor",
    page_icon="🔬",
    layout="centered"
)

st.title("🔬 Veterinary General Pathology Tutor")
st.caption("Aetiology & Diagnostic Reasoning Interactive Practice")

# Read Secrets
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", None)
except Exception:
    st.error("Missing secrets! Please configure GEMINI_API_KEY in Streamlit Advanced Settings.")
    st.stop()

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# 2. LOGGING HELPER FUNCTION
# ==========================================
def log_to_google_sheet(student_name, roll_number, step, user_input, ai_response):
    """Sends student interaction data to Google Apps Script Webhook asynchronously."""
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

if st.sidebar.button("🔄 Restart Case Study"):
    st.session_state.messages = []
    st.session_state.step_count = 1
    st.rerun()

# ==========================================
# 4. SOCRATIC AI SYSTEM INSTRUCTIONS (VCI 2nd Year Level)
# ==========================================
SOCRATIC_SYSTEM_PROMPT = f"""
You are an encouraging Veterinary Pathology Professor tutoring a 2nd-year BVSc & AH student named {student_name} under the VCI syllabus.
The student has completed Anatomy and Physiology but is NEW to General Pathology and Aetiology.

PEDAGOGICAL STRATEGY:
1. Start from basic physiological/anatomical principles (e.g., normal blood supply, cell structures, membrane integrity) and bridge them to pathological mechanisms (etiology, cell injury, necrosis, inflammation, circulatory disturbances).
2. NEVER ask complex clinical differential diagnosis questions or expect advanced gross pathology terminology yet.
3. Keep questions simple, conceptual, and foundational. Ask ONE simple question at a time.
4. If the student answers using basic anatomy or common sense, praise them and connect it to the proper pathology term (e.g., if they say 'lack of oxygen', introduce 'hypoxia').
5. Keep answers under 3 sentences so it remains an active conversation.
"""

# ==========================================
# 5. CHAT INITIALIZATION & HISTORY
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "step_count" not in st.session_state:
    st.session_state.step_count = 1

# Updated model configuration for stability
model = genai.GenerativeModel(
    model_name="gemini-3.8-flash",
    system_instruction=SOCRATIC_SYSTEM_PROMPT
)

# Foundational Opening Question
if len(st.session_state.messages) == 0:
    initial_greeting = f"""Welcome {student_name}! Welcome to General Pathology & Aetiology practice.

You already know from Anatomy and Physiology that a healthy liver is reddish-brown, smooth, and firm with normal blood circulation. 

Imagine during a post-mortem or lab examination, you notice a liver that looks dark red, swollen, and soft. Before thinking about specific diseases, what fundamental cause or mechanism could disrupt normal blood flow or cause tissue cells to swell and die?"""
    
    st.session_state.messages.append({"role": "model", "parts": [initial_greeting]})

for msg in st.session_state.messages:
    role = "user" if msg["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(msg["parts"][0])

# ==========================================
# 6. USER INPUT & RESPONSE INTERACTION
# ==========================================
if user_prompt := st.chat_input("Type your response or answer here..."):
    st.chat_message("user").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "parts": [user_prompt]})
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your response..."):
            try:
                formatted_history = []
                for m in st.session_state.messages:
                    formatted_history.append({
                        "role": m["role"],
                        "parts": m["parts"]
                    })
                
                chat = model.start_chat(history=formatted_history[:-1])
                response = chat.send_message(user_prompt)
                ai_reply = response.text
                
                st.markdown(ai_reply)
                st.session_state.messages.append({"role": "model", "parts": [ai_reply]})
                
                log_to_google_sheet(
                    student_name=student_name,
                    roll_number=roll_number,
                    step=st.session_state.step_count,
                    user_input=user_prompt,
                    ai_response=ai_reply
                )
                
                st.session_state.step_count += 1
                
            except Exception as e:
                st.error(f"Error communicating with Gemini API: {str(e)}")
