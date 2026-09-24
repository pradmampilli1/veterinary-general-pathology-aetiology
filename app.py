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
        # Fire-and-forget post request with a short timeout so app UI stays fast
        requests.post(WEBHOOK_URL, json=payload, timeout=3)
    except Exception as e:
        # Silently fail or log locally so student experience is never interrupted
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

# Reset Session Button
if st.sidebar.button("🔄 Restart Case Study"):
    st.session_state.messages = []
    st.session_state.step_count = 1
    st.rerun()

# ==========================================
# 4. SOCRATIC AI SYSTEM INSTRUCTIONS
# ==========================================
SOCRATIC_SYSTEM_PROMPT = f"""
You are an expert Veterinary Pathology Professor tutoring a undergraduate veterinary student named {student_name}.
Your goal is to guide them through diagnostic reasoning on General Pathology / Aetiology concepts using the Socratic method.

CRITICAL RULES:
1. NEVER give the direct answer or list full diagnoses immediately.
2. Ask ONE focused, thought-provoking question at a time to lead the student to the correct answer.
3. If the student gives an incorrect or incomplete answer, gently point out what they missed or offer a subtle hint, then ask a follow-up guiding question.
4. If the student gives a good answer, validate them briefly and move to the next logical step in diagnostic reasoning (e.g., physical lesion description -> probable cause -> mechanism -> confirmation method).
5. Keep your tone encouraging, scholarly, and supportive. Keep responses concise (under 3-4 sentences per turn).
"""

# ==========================================
# 5. CHAT INITIALIZATION & HISTORY
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "step_count" not in st.session_state:
    st.session_state.step_count = 1

# Initialize Gemini Model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SOCRATIC_SYSTEM_PROMPT
)

# Start conversation if fresh
if len(st.session_state.messages) == 0:
    initial_greeting = f"Welcome {student_name}! Let's begin today's general pathology diagnostic case. \n\nImagine you perform a post-mortem on a bird or animal and observe marked focal liver necrosis with hyperaemic zones. Before jumping to specific pathogens, what initial gross morphological features should you evaluate to differentiate between an acute hypoxic lesion and a primary infectious aetiology?"
    st.session_state.messages.append({"role": "model", "parts": [initial_greeting]})

# Display previous chat messages
for msg in st.session_state.messages:
    role = "user" if msg["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(msg["parts"][0])

# ==========================================
# 6. USER INPUT & RESPONSE INTERACTION
# ==========================================
if user_prompt := st.chat_input("Type your response or diagnostic step here..."):
    # Display User Input
    st.chat_message("user").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "parts": [user_prompt]})
    
    # Generate Socratic AI Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your response..."):
            try:
                # Format conversation history for Gemini
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
                
                # Log interaction to Google Sheets via Webhook
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
