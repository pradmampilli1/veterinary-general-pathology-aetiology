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
st.subheader("Micro-Session General Pathology")

# Read Secrets
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", None)
except Exception:
    st.error("Missing secrets! Please configure GEMINI_API_KEY in Streamlit Advanced Settings.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# 2. MICRO-SESSION MODULE DEFINITIONS
# ==========================================
CHAPTER_PROMPTS = {
    "Micro-session 1: Why do animals become sick?": """
MICRO-SESSION 1 SCOPE: Why do animals become sick?
- Goal: Connect health change to underlying causes of disease.
- Keep focus on generating simple initial ideas (e.g., infections, poison, physical harm).
""",
    "Micro-session 2: What is the cause called? (Etiology)": """
MICRO-SESSION 2 SCOPE: What is the cause called? -> Etiology
- Goal: Introduce ordinary concept first, then label with pathology term 'Etiology' (the cause/initiator of disease).
""",
    "Micro-session 3: Can different causes produce the same sign?": """
MICRO-SESSION 3 SCOPE: Cause vs. Manifestation
- Goal: Clinical Sign != Etiology (e.g., Diarrhea or Jaundice can arise from completely different causes).
""",
    "Micro-session 4: Can we group causes?": """
MICRO-SESSION 4 SCOPE: Broad Etiological Categories
- Goal: Group causes into broad categories (Infectious, Physical, Chemical, Nutritional, Genetic, etc.) using concrete veterinary examples first.
""",
    "Micro-session 5: How does a cause produce disease?": """
MICRO-SESSION 5 SCOPE: Introduction to Pathogenesis
- Goal: Briefly introduce the chain: Cause -> Mechanism of injury (Pathogenesis).
""",
    "Micro-session 6: What happens to cells and tissues?": """
MICRO-SESSION 6 SCOPE: Morphological Changes
- Goal: Connect cause and mechanism to observable cell/tissue changes.
"""
}

# ==========================================
# 3. LOGGING HELPER FUNCTION
# ==========================================
def log_to_google_sheet(student_name, roll_number, chapter, step, user_input, ai_response):
    if not WEBHOOK_URL:
        return
    
    payload = {
        "name": student_name,
        "roll_number": roll_number,
        "chapter": chapter,
        "step": step,
        "answer": user_input,
        "feedback": ai_response
    }
    
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=3)
    except Exception:
        pass

# ==========================================
# 4. STUDENT REGISTRATION & SESSION SELECTION (SIDEBAR)
# ==========================================
st.sidebar.header("📋 Student Session Setup")
student_name = st.sidebar.text_input("Full Name", placeholder="e.g., Dr. Ananya")
roll_number = st.sidebar.text_input("Roll Number / ID", placeholder="e.g., VET2026-042")

selected_chapter = st.sidebar.selectbox(
    "Select Micro-Session:",
    list(CHAPTER_PROMPTS.keys())
)

st.caption(f"Active Scope: **{selected_chapter}**")

if not student_name or not roll_number:
    st.info("👈 Please enter your **Full Name**, **Roll Number**, and select a **Micro-Session** in the sidebar to begin.")
    st.stop()

# Reset chat session if session selection changes
if "current_chapter" in st.session_state and st.session_state.current_chapter != selected_chapter:
    for key in ["messages", "step_count"]:
        if key in st.session_state:
            del st.session_state[key]

st.session_state.current_chapter = selected_chapter

if st.sidebar.button("🔄 Restart Micro-Session"):
    for key in ["messages", "step_count", "working_model"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ==========================================
# 5. INTEGRATED SYSTEM PROMPT
# ==========================================
current_step = st.session_state.get("step_count", 1)

SOCRATIC_SYSTEM_PROMPT = f"""
SYSTEM PROMPT: AI MICRO-SESSION TUTOR FOR BEGINNING GENERAL VETERINARY PATHOLOGY

ROLE:
You are an engaging AI tutor for BVSc & AH students named {student_name} who are beginning General Veterinary Pathology.
Your goal is NOT to finish a textbook topic in one session. Your goal is to make students curious, think, answer, understand, and want to continue.
Keep interactions short, conversational, and enjoyable.

ACTIVE MICRO-SESSION:
{CHAPTER_PROMPTS[selected_chapter]}
CURRENT PROGRESS: Step {current_step} of 4.

THE GOLDEN RULE & LOOP:
Use: CASE -> THINK -> ANSWER -> EXPLAIN -> ONE MORE -> STOP.
Do NOT use: LECTURE -> DEFINITIONS -> CLASSIFICATION -> LONG EXPLANATION -> TEST.

PEDAGOGICAL & CONVERSATIONAL RULES:
1. ASK ONLY ONE QUESTION AT A TIME: Never give a list of questions. Ask one question, wait, then respond.
2. KEEP THE STUDENT TALKING: Aim for student doing 50-70% of thinking. Keep AI responses short (30-50% word count, under 3 short sentences max).
3. WRONG ANSWERS: Never say "Wrong". Say "Good attempt. Think about what actually initiated the disease..." and give a small clue.
4. CORRECT ANSWERS: Avoid excessive praise ("Fantastic!", "Amazing!"). Use natural responses: "Exactly.", "Yes—that's the idea.", "Right."
5. USE REAL VETERINARY PATHOLOGY: Prefer common animals (dogs, cattle, cats, calves, horses, poultry) and clear simple situations.
6. THE STOP RULE (CRITICAL):
   - If current_step < 3: Guide with 1 short thinking question.
   - If current_step >= 3: Provide a brief 1-2 sentence closing reflection, reinforce the single key takeaway, and STOP the micro-session cleanly (e.g., "You've got the basic idea! Next time we'll look at..."). Do NOT ask any further questions once step is 3 or higher.
"""

# ==========================================
# 6. DYNAMIC MODEL RETRIEVAL
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
# 7. INITIALIZATION
# ==========================================
if "step_count" not in st.session_state:
    st.session_state.step_count = 1

if "working_model" not in st.session_state:
    model_candidates = get_available_models()
    st.session_state.working_model = model_candidates[0] if model_candidates else "gemini-1.5-flash-latest"

if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # Custom short hooks per micro-session
    if "Micro-session 1" in selected_chapter:
        initial_greeting = f"Welcome {student_name}! A cow on a farm suddenly stops eating and becomes dull. What could have started this change in the animal?"
    elif "Micro-session 2" in selected_chapter:
        initial_greeting = f"Welcome {student_name}! A dog develops severe illness after swallowing a toxic substance. What actually started the disease here?"
    elif "Micro-session 3" in selected_chapter:
        initial_greeting = f"Welcome {student_name}! Two different dogs come into your clinic with diarrhoea. Would you expect the exact cause of disease to be the same in both?"
    elif "Micro-session 4" in selected_chapter:
        initial_greeting = f"Welcome {student_name}! Rabies virus causes severe disease in dogs. What broad category of cause does a virus belong to?"
    elif "Micro-session 5" in selected_chapter:
        initial_greeting = f"Welcome {student_name}! A calf ingests a toxic plant and later develops liver failure. How does the toxin actually go from ingestion to damaging the liver cells?"
    else:
        initial_greeting = f"Welcome {student_name}! When a severe injury occurs in muscle tissue, what kind of structural changes would you expect to see in those cells?"

    st.session_state.messages.append({"role": "assistant", "content": initial_greeting})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 8. USER INPUT & STREAMED RESPONSE WITH AUTO-FAILOVER
# ==========================================
if user_prompt := st.chat_input("Type your response or thoughts here..."):
    st.chat_message("user").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        success = False
        
        # Buffer containing recent messages (last 6 turns)
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
                chapter=selected_chapter,
                step=st.session_state.step_count,
                user_input=user_prompt,
                ai_response=full_response
            )
            st.session_state.step_count += 1
        else:
            st.error("Unable to reach Google API. Please check your API key.")
