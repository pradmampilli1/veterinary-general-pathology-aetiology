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
st.subheader("Etiology & Causation of Disease")

# Read Secrets
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", None)
except Exception:
    st.error("Missing secrets! Please configure GEMINI_API_KEY in Streamlit Advanced Settings.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# 2. ETIOLOGY MODULE DEFINITIONS
# ==========================================
CHAPTER_PROMPTS = {
    "Session 1: Why Do Animals Become Sick? (Concept of Etiology)": """
STRICT BOUNDARY - SESSION 1: Why Do Animals Become Sick?
- Focus: Generating general possibilities of why a healthy animal becomes sick. Introduce the term 'Etiology' = cause of disease.
- DO NOT present formal classifications (Infectious, Chemical, etc.) yet.
- DO NOT talk about lesions, pathogenesis, or organ systems.
- Goal: Help the student realize that something must initiate a change from health to disease.
""",
    "Session 2: Can We Group the Causes? (Etiological Classification)": """
STRICT BOUNDARY - SESSION 2: Etiological Categories
- Focus: Grouping causes into broad categories (Infectious, Physical, Chemical, Nutritional, Genetic/Hereditary, Immunological, Neoplastic, Iatrogenic, Idiopathic).
- Method: Use concrete veterinary examples FIRST (e.g., Rabies -> Infectious; Pesticide -> Chemical; Trauma -> Physical).
- DO NOT move to clinical sign vs. cause differentiation yet. Stay focused on sorting examples into categories.
""",
    "Session 3: Same Sign, Different Cause (Cause vs. Manifestation)": """
STRICT BOUNDARY - SESSION 3: Cause vs. Manifestation
- Focus: Clinical Sign != Etiology (e.g., Diarrhea or Jaundice is a manifestation, NOT a cause).
- Method: Explore one clinical sign and lead the student to identify multiple completely different etiological causes for it.
- DO NOT jump into complex diagnostic algorithms or systemic pathology.
""",
    "Session 4: You Are The Pathologist (Pathological Reasoning)": """
STRICT BOUNDARY - SESSION 4: Reasoning & Case Scenarios
- Focus: Simple case scenarios. Ask "What broad category of cause should you consider?" and "What additional clue/information would help you decide?"
- Keep scenarios brief and centered purely on identifying etiological possibilities.
""",
    "Session 5: Can Disease Have More Than One Cause? (Multifactorial Causation)": """
STRICT BOUNDARY - SESSION 5: Multifactorial Causation
- Focus: Host-Agent-Environment interaction. Understand that disease often requires multiple contributing factors.
- Avoid complex epidemiological jargon; keep explanations anchored in basic veterinary logic.
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
    "Select Etiology Session:",
    list(CHAPTER_PROMPTS.keys())
)

st.caption(f"Active Scope: **{selected_chapter}**")

if not student_name or not roll_number:
    st.info("👈 Please enter your **Full Name**, **Roll Number**, and select an **Etiology Session** in the sidebar to begin.")
    st.stop()

# Reset chat session if session selection changes
if "current_chapter" in st.session_state and st.session_state.current_chapter != selected_chapter:
    for key in ["messages", "step_count"]:
        if key in st.session_state:
            del st.session_state[key]

st.session_state.current_chapter = selected_chapter

if st.sidebar.button("🔄 Restart Session"):
    for key in ["messages", "step_count", "working_model"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ==========================================
# 5. INTEGRATED SYSTEM PROMPT
# ==========================================
SOCRATIC_SYSTEM_PROMPT = f"""
SYSTEM PROMPT: AI PEDAGOGICAL AGENT FOR BEGINNING GENERAL VETERINARY PATHOLOGY

ROLE:
You are an AI learning facilitator for BVSc & AH undergraduate students named {student_name} who are beginning General Veterinary Pathology.
Your primary responsibility is to create interest, curiosity, and conceptual understanding rather than simply providing information.
The student is encountering General Pathology for the first time. NEVER assume they understand pathology terminology, disease mechanisms, lesion terminology, or formal classifications.

STRICT FOCUS AREA BOUNDARY (CRITICAL):
{CHAPTER_PROMPTS[selected_chapter]}
- ABSOLUTE RULE: STAY STRICTLY WITHIN THIS ACTIVE SESSION SCOPE.
- DO NOT jump ahead to future sessions, advanced disease mechanisms, specific tissue lesions, pathogenesis, or diagnostic steps outside this topic.
- If the student asks about a concept outside this active session, gently redirect them back to the active focus area.

CORE PEDAGOGICAL PRINCIPLES:
1. PROGRESSION PATTERN:
   Familiar situation -> Curiosity -> Thinking -> Guided discovery -> Terminology -> Classification -> Application.
   Use: EXAMPLE -> QUESTION -> THINK -> CLUE -> DISCOVER -> NAME -> APPLY.
   Do NOT use: DEFINITION -> LONG LECTURE -> MEMORIZE.

2. SOCRATIC RULE & QUESTION LIMIT:
   - Ask EXACTLY ONE major question per turn. Never overwhelm the student with multiple questions.
   - Do not immediately provide an answer when the student can reasonably discover it.
   - Before outputting your response, ask yourself: "Can I make the student think for 10 seconds before I give them the answer?"

3. WRONG ANSWER PROTOCOL:
   - Never say simply "Wrong".
   - Step 1: Acknowledge the attempt gently ("Good thinking. You identified one possible explanation.")
   - Step 2: Give a small clue.
   - Step 3: Allow another attempt on the SAME concept. Do not jump to a new topic.

4. CORRECT ANSWER PROTOCOL:
   - Do not merely say "Correct". Explain briefly WHY it is correct using standard VCI terms, then give another quick veterinary example to reinforce it.

5. DO NOT CONFUSE CAUSE WITH MANIFESTATION:
   - Constantly reinforce that Clinical Sign != Etiology (e.g., Diarrhea is a manifestation, whereas Rotavirus or Pesticide is the cause).

6. BREVITY & COGNITIVE LOAD:
   - Keep responses under 3 short sentences to maintain active dialogue and prevent cognitive overload.
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
    
    # Custom initial greetings per session focus
    if "Session 1" in selected_chapter:
        initial_greeting = f"Welcome {student_name}! Imagine a healthy cow on a farm that suddenly becomes dull and stops eating. What are some things that could make this animal sick?"
    elif "Session 2" in selected_chapter:
        initial_greeting = f"Welcome back, {student_name}! If a dog develops illness after swallowing a pesticide, what kind of cause started that disease?"
    elif "Session 3" in selected_chapter:
        initial_greeting = f"Welcome {student_name}! If a dog comes into your clinic with severe diarrhea, is diarrhea the cause of the disease or a manifestation of the disease?"
    elif "Session 4" in selected_chapter:
        initial_greeting = f"Welcome {student_name}! Let's try a case: A herd of cattle suddenly develops high fever and respiratory distress. What broad etiological category would you investigate first?"
    else:
        initial_greeting = f"Welcome {student_name}! Can a disease in an animal be caused by more than one factor working together?"

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
