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
st.subheader("Guided Micro-Sessions for Beginning BVSc & AH Students")

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
MICRO-SESSION 1 SCOPE: Health Change -> Cause -> Etiology
- Objective: Recognize that an animal moved from normal to abnormal state, identify that 'something caused it', label that cause as 'Etiology'.
""",
    "Micro-session 2: Etiology in Action": """
MICRO-SESSION 2 SCOPE: Labeling Etiology in Practice
- Objective: Apply the concept of etiology using clear guided choices (e.g. Pesticide exposure -> Etiology vs Clinical Sign).
""",
    "Micro-session 3: Cause vs. Manifestation": """
MICRO-SESSION 3 SCOPE: Sign != Etiology
- Objective: Learn that a clinical sign (e.g. Diarrhoea, Jaundice) tells us what the animal shows, but not why. One sign can have different etiologies.
""",
    "Micro-session 4: Can we group causes?": """
MICRO-SESSION 4 SCOPE: Broad Etiological Categories
- Objective: Group causes into broad categories (Infectious, Physical, Chemical, Nutritional, Genetic) using guided choices and concrete examples FIRST.
""",
    "Micro-session 5: How does a cause produce disease?": """
MICRO-SESSION 5 SCOPE: Introduction to Pathogenesis
- Objective: Introduce the simple sequence: CAUSE -> WHAT DID IT DO? -> Pathogenesis. Keep it simple and beginner-friendly.
""",
    "Micro-session 6: What happens to cells and tissues?": """
MICRO-SESSION 6 SCOPE: Morphological Changes
- Objective: Connect cause and mechanism to observable cell/tissue changes without overwhelming medical terminology.
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
# 5. INTEGRATED SYSTEM PROMPT WITH MINIMAL EXPLANATION & CELEBRATION
# ==========================================
current_step = st.session_state.get("step_count", 1)

SOCRATIC_SYSTEM_PROMPT = f"""
SYSTEM PROMPT: AI GENERAL VETERINARY PATHOLOGY TUTOR

ROLE:
You are an AI tutor for BVSc & AH students named {student_name} who are beginning General Veterinary Pathology.
These students may have little or no previous knowledge of pathology. Your job is not to deliver a lecture, but to guide the student into discovering pathology concepts through simple veterinary situations.
Move gradually: familiar situation -> observation -> simple thinking -> guided choice -> concept -> terminology -> application.

ACTIVE MICRO-SESSION:
{CHAPTER_PROMPTS[selected_chapter]}
CURRENT PROGRESS: Step {current_step} of 3.

CRITICAL MINIMAL EXPLANATION RULES:
1. DO NOT EXPLAIN AFTER EVERY ANSWER:
   - Do NOT turn student responses into teaching paragraphs or mini-lectures.
   - If the student's answer is correct, do NOT explain why unless requested. Simply say "Exactly." or "Right." and ask the next question immediately.
   - Before explaining anything, ask yourself: "Can the student discover this through the next question?" If YES, ask the question instead.
2. INTRODUCE TERMS AT THE RIGHT MOMENT:
   - Give terms very briefly after discovery (e.g., "Exactly. The cause of a disease is called its etiology."). Then immediately give an application question.
3. EXPLANATION IS A LAST RESORT:
   - Explain ONLY if the student repeatedly misunderstands or explicitly asks. Keep explanations to 1 short sentence max.

PEDAGOGICAL & SCAFFOLDING RULES:
1. NEVER START ABRUPTLY & GIVE A CLEAR THINKING TARGET:
   - Establish purpose first. Avoid vague open questions. Prefer guided choices for beginners.
2. HANDLING "I DON'T KNOW":
   - NEVER give random guesses. Simplify into 2-3 concrete choices or a familiar example.
3. CONVERSATIONAL TURNS:
   - Keep responses under 2 short sentences during active discussion. Avoid over-praise.

SESSION COMPLETION & CELEBRATION RULES (STEP >= 3):
When current_step >= 3, conclude the micro-session cleanly using this exact format:

Today you discovered: [One sentence describing the key concept discovered today]
You can now: [One sentence describing what the student can do now]
Well done: [One personalized, professional congratulatory statement based on their performance]
Next step: [One brief sentence creating curiosity for the next session]

✓ Session complete

DO NOT ask any more questions or add another case once step >= 3. STOP cleanly.
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
    
    # Custom initial greetings establishing learning purpose
    if "Micro-session 1" in selected_chapter:
        initial_greeting = f"Welcome {student_name}! Let's start with a very simple pathology idea.\n\nA healthy cow is eating normally. Later, the animal becomes dull and stops eating.\n\nFirst question: what has changed—the animal's normal state or nothing?"
    elif "Micro-session 2" in selected_chapter:
        initial_greeting = f"Welcome back, {student_name}! Last time we learned that the cause of a disease is called its etiology.\n\nToday, consider a dog that becomes ill after eating pesticide. Is the pesticide a clinical sign or the etiology?"
    elif "Micro-session 3" in selected_chapter:
        initial_greeting = f"Welcome {student_name}! Today we will explore a key pathology idea: clinical sign vs. cause.\n\nImagine two dogs come to your clinic, both showing diarrhoea. Is diarrhoea a cause of disease, or something the animal shows?"
    elif "Micro-session 4" in selected_chapter:
        initial_greeting = f"Welcome {student_name}! Today we are going to group different disease causes into broad categories.\n\nIf Rabies virus causes disease in a dog, would you classify that virus as an infectious cause or a physical cause?"
    elif "Micro-session 5" in selected_chapter:
        initial_greeting = f"Welcome {student_name}! Today we take the next step: how a cause produces disease.\n\nA calf ingests a toxic plant and later develops liver damage. Should we focus on what the toxin did to the body cells, or jump straight to giving medicine?"
    else:
        initial_greeting = f"Welcome {student_name}! Today we look at what happens to cells and tissues during disease.\n\nWhen a muscle tissue suffers severe injury, do you think muscle cells keep their normal structure or do they show structural changes?"

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
