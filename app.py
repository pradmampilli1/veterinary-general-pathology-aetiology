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
# 2. MICRO-SESSION & CONTINUITY BRIDGE DEFINITIONS
# ==========================================
CHAPTER_PROMPTS = {
    "Micro-session 1: Why do animals become sick?": {
        "scope": "MICRO-SESSION 1 SCOPE: Health Change -> Cause -> Etiology\n- Goal: Recognize normal to abnormal transition, identify that something caused it, label cause as 'Etiology'.",
        "greeting": "Welcome {name}! Let's start with a very simple pathology idea.\n\nA healthy cow is eating normally. Later, the animal becomes dull and stops eating.\n\nFirst question: what has changed—the animal's normal state or nothing?",
        "bridge_puzzle": "We know what caused the disease (etiology)—but how does that cause actually produce disease inside the animal?"
    },
    "Micro-session 2: How does a cause produce disease? (Pathogenesis)": {
        "scope": "MICRO-SESSION 2 SCOPE: Mechanism of Injury -> Pathogenesis\n- Goal: Explore how a cause creates damage step-by-step, then label that process 'Pathogenesis'.",
        "greeting": "Welcome back, {name}! Last time, you discovered that the cause of disease is called etiology.\n\nLet's take the next step: A toxin enters an animal's body. The toxin is the cause, but how could that chemical actually turn into damage inside the body? What do you think happens between the cause and the final disease?",
        "bridge_puzzle": "If disease develops through a mechanism (pathogenesis), what actually changes inside the individual cells and tissues?"
    },
    "Micro-session 3: What happens to cells and tissues? (Cell Injury)": {
        "scope": "MICRO-SESSION 3 SCOPE: Cellular Injury & Morphological Changes\n- Goal: Connect mechanism/pathogenesis to structural cell and tissue changes.",
        "greeting": "Welcome back, {name}! In our last session, we saw that disease develops through a step-by-step mechanism called pathogenesis.\n\nToday's question: When a toxin or injury acts on an organ, what do you think happens to the individual cells that make up that tissue?",
        "bridge_puzzle": "If individual cells in an organ are injured, how does that cell damage lead to clinical signs that you observe in the living animal?"
    },
    "Micro-session 4: Cause vs. Manifestation": {
        "scope": "MICRO-SESSION 4 SCOPE: Sign != Etiology\n- Goal: Distinguish between clinical manifestation (what the animal shows) and etiology (what caused it).",
        "greeting": "Welcome back, {name}! Today we tackle a critical question every veterinarian asks.\n\nImagine two dogs come into your clinic, both showing severe diarrhoea. Is diarrhoea the cause of the disease, or something the animal is showing because of the disease?",
        "bridge_puzzle": "Since clinical signs aren't causes, how can we organize all the different possible causes into broad, understandable groups?"
    },
    "Micro-session 5: Can we group causes?": {
        "scope": "MICRO-SESSION 5 SCOPE: Broad Etiological Categories\n- Goal: Group causes into broad categories (Infectious, Physical, Chemical, Nutritional, Genetic).",
        "greeting": "Welcome back, {name}! Last time, you discovered that diarrhoea is a sign, but its cause could be many different things.\n\nToday: If Rabies virus causes disease in a dog, would you classify that virus as an infectious cause or a physical cause?",
        "bridge_puzzle": "Can a single animal's disease be caused by more than one of these categories acting together?"
    },
    "Micro-session 6: Multifactorial Causation": {
        "scope": "MICRO-SESSION 6 SCOPE: Host-Agent-Environment Interaction\n- Goal: Understand that disease often results from multiple contributing factors working together.",
        "greeting": "Welcome back, {name}! So far we've looked at single causes like viruses or toxins.\n\nToday's puzzle: Can an animal become sick due to two or three different factors working together, or does every disease have only one cause?",
        "bridge_puzzle": "You have mastered the core framework of Etiology and Pathogenesis! Next time, we'll begin investigating specific cell injury patterns."
    }
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
# 5. INTEGRATED SYSTEM PROMPT WITH CONTINUITY RULES
# ==========================================
current_step = st.session_state.get("step_count", 1)
active_session_data = CHAPTER_PROMPTS[selected_chapter]

SOCRATIC_SYSTEM_PROMPT = f"""
SYSTEM PROMPT: AI GENERAL VETERINARY PATHOLOGY TUTOR

ROLE:
You are an AI tutor for BVSc & AH students named {student_name} who are beginning General Veterinary Pathology.
Your job is not to deliver a lecture, but to guide the student into discovering pathology concepts through simple veterinary situations.
Move gradually: familiar situation -> observation -> simple thinking -> guided choice -> concept -> terminology -> application.

ACTIVE MICRO-SESSION:
{active_session_data['scope']}
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

SESSION COMPLETION & CURIOSITY BRIDGE RULES (STEP >= 3):
When current_step >= 3, conclude the micro-session cleanly using this EXACT short format:

Today you discovered: [One sentence describing the key concept discovered today]
Well done: [One personalized, professional congratulatory statement based on their performance]
Next puzzle: {active_session_data['bridge_puzzle']}

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
    initial_greeting = active_session_data["greeting"].format(name=student_name)
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
