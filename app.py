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
st.subheader("Module: Etiology & Classification of Disease (7 Micro-Sessions)")

# Read Secrets
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", None)
except Exception:
    st.error("Missing secrets! Please configure GEMINI_API_KEY in Streamlit Advanced Settings.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# 2. MICRO-SESSION DEFINITIONS WITH INLINE SVG SKETCHES
# ==========================================
CHAPTER_PROMPTS = {
    1: {
        "title": "Session 1: Why do animals become sick? (Idea of Causation)",
        "scope": "SESSION 1 OF 7 SCOPE: Health Change -> Idea of Cause\n- Focus: Recognizing normal state change and identifying that 'something caused it'.",
        "greeting": "Welcome {name}! Let's start with a simple pathology observation.\n\nTake a look at the sketch above: A healthy cow is eating normally. Later, the same cow becomes dull and stops eating.\n\nFirst question: what has changed—the animal's normal state or nothing?",
        "sketch": """
        <svg width="100%" height="110" viewBox="0 0 320 110" xmlns="http://www.w3.org/2000/svg">
          <rect width="320" height="110" fill="#f8f9fa" rx="8"/>
          <!-- Healthy Cow -->
          <g transform="translate(15,15)">
            <rect x="10" y="25" width="55" height="35" rx="6" fill="#8d6e63"/>
            <circle cx="70" cy="30" r="14" fill="#8d6e63"/>
            <circle cx="75" cy="27" r="2" fill="#ffffff"/>
            <text x="5" y="75" font-size="11" font-weight="bold" fill="#2e7d32"> Eating / Grazing</text>
            <text x="12" y="88" font-size="10" fill="#555555">(Normal State)</text>
          </g>
          <!-- Transition Arrow -->
          <path d="M 125 45 L 175 45" stroke="#757575" stroke-width="3" fill="none"/>
          <polygon points="175,40 185,45 175,50" fill="#757575"/>
          <text x="135" y="38" font-size="10" font-weight="bold" fill="#d32f2f">Something</text>
          <text x="138" y="58" font-size="10" font-weight="bold" fill="#d32f2f">Happened</text>
          <!-- Sick Cow -->
          <g transform="translate(200,15)">
            <rect x="10" y="25" width="55" height="35" rx="6" fill="#b0bec5"/>
            <circle cx="70" cy="42" r="14" fill="#b0bec5"/>
            <circle cx="75" cy="40" r="1.5" fill="#37474f"/>
            <text x="8" y="75" font-size="11" font-weight="bold" fill="#c62828"> Dull / Off-feed</text>
            <text x="8" y="88" font-size="10" fill="#555555">(Altered State)</text>
          </g>
        </svg>
        """
    },
    2: {
        "title": "Session 2: What is the cause called? (Introduction to Etiology)",
        "scope": "SESSION 2 OF 7 SCOPE: Labeling Cause -> Etiology\n- Focus: Connecting ordinary idea of cause to the formal pathology term 'Etiology'.",
        "greeting": "Welcome to Session 2 of 7, {name}!\n\nWhen a dog becomes ill after swallowing pesticide, pesticide is the cause of the disease.\n\nIn pathology, what technical term do we use for the cause of a disease?",
        "sketch": """
        <svg width="100%" height="100" viewBox="0 0 320 100" xmlns="http://www.w3.org/2000/svg">
          <rect width="320" height="100" fill="#f8f9fa" rx="8"/>
          <g transform="translate(20,20)">
            <rect x="10" y="10" width="35" height="45" rx="4" fill="#e53935"/>
            <text x="27" y="35" font-size="16" fill="#ffffff" text-anchor="middle" font-weight="bold">☠</text>
            <text x="0" y="70" font-size="11" font-weight="bold" fill="#c62828">Pesticide (Cause)</text>
          </g>
          <path d="M 100 42 L 170 42" stroke="#1565c0" stroke-width="3" fill="none"/>
          <polygon points="170,37 180,42 170,47" fill="#1565c0"/>
          <text x="110" y="34" font-size="11" font-weight="bold" fill="#1565c0">Technical Term?</text>
          <g transform="translate(200,20)">
            <circle cx="35" cy="30" r="22" fill="#bbdefb" stroke="#1976d2" stroke-width="2"/>
            <text x="35" y="36" font-size="18" fill="#1976d2" text-anchor="middle" font-weight="bold">?</text>
            <text x="10" y="70" font-size="11" font-weight="bold" fill="#1565c0">Pathology Term</text>
          </g>
        </svg>
        """
    },
    3: {
        "title": "Session 3: Can we group different causes? (Etiological Classification)",
        "scope": "SESSION 3 OF 7 SCOPE: Major Etiological Categories\n- Focus: Grouping causes into Infectious, Physical, Chemical, Nutritional, Genetic using concrete examples first.",
        "greeting": "Welcome to Session 3 of 7, {name}!\n\nIf Rabies virus causes disease in a dog, would you classify that virus as an infectious cause or a chemical cause?",
        "sketch": """
        <svg width="100%" height="110" viewBox="0 0 320 110" xmlns="http://www.w3.org/2000/svg">
          <rect width="320" height="110" fill="#f8f9fa" rx="8"/>
          <text x="160" y="22" font-size="12" font-weight="bold" fill="#333333" text-anchor="middle">ETIOLOGICAL CATEGORIES</text>
          <g transform="translate(15,35)">
            <rect x="0" y="0" width="60" height="55" rx="5" fill="#e8f5e9" stroke="#2e7d32" stroke-width="1.5"/>
            <text x="30" y="25" font-size="16" text-anchor="middle">🦠</text>
            <text x="30" y="44" font-size="9" font-weight="bold" fill="#2e7d32" text-anchor="middle">Infectious</text>
          </g>
          <g transform="translate(90,35)">
            <rect x="0" y="0" width="60" height="55" rx="5" fill="#ffebee" stroke="#c62828" stroke-width="1.5"/>
            <text x="30" y="25" font-size="16" text-anchor="middle">🧪</text>
            <text x="30" y="44" font-size="9" font-weight="bold" fill="#c62828" text-anchor="middle">Chemical</text>
          </g>
          <g transform="translate(165,35)">
            <rect x="0" y="0" width="60" height="55" rx="5" fill="#fff3e0" stroke="#ef6c00" stroke-width="1.5"/>
            <text x="30" y="25" font-size="16" text-anchor="middle">🔨</text>
            <text x="30" y="44" font-size="9" font-weight="bold" fill="#ef6c00" text-anchor="middle">Physical</text>
          </g>
          <g transform="translate(240,35)">
            <rect x="0" y="0" width="60" height="55" rx="5" fill="#e0f7fa" stroke="#00838f" stroke-width="1.5"/>
            <text x="30" y="25" font-size="16" text-anchor="middle">🌾</text>
            <text x="30" y="44" font-size="9" font-weight="bold" fill="#00838f" text-anchor="middle">Nutritional</text>
          </g>
        </svg>
        """
    },
    4: {
        "title": "Session 4: Same sign, different cause (Manifestation vs. Etiology)",
        "scope": "SESSION 4 OF 7 SCOPE: Sign != Etiology\n- Focus: Exploring how a single sign (e.g., Diarrhoea or Jaundice) can have multiple completely different etiologies.",
        "greeting": "Welcome to Session 4 of 7, {name}!\n\nImagine two dogs come into your clinic, both showing severe diarrhoea. Is diarrhoea the etiology of the disease, or a clinical sign shown by the animal?",
        "sketch": """
        <svg width="100%" height="110" viewBox="0 0 320 110" xmlns="http://www.w3.org/2000/svg">
          <rect width="320" height="110" fill="#f8f9fa" rx="8"/>
          <g transform="translate(20,15)">
            <rect x="0" y="0" width="75" height="30" rx="4" fill="#e8f5e9" stroke="#2e7d32"/>
            <text x="37" y="19" font-size="10" font-weight="bold" fill="#2e7d32" text-anchor="middle">Infectious (Virus)</text>
          </g>
          <g transform="translate(225,15)">
            <rect x="0" y="0" width="75" height="30" rx="4" fill="#ffebee" stroke="#c62828"/>
            <text x="37" y="19" font-size="10" font-weight="bold" fill="#c62828" text-anchor="middle">Chemical (Toxin)</text>
          </g>
          <path d="M 60 48 L 130 70" stroke="#757575" stroke-width="2" fill="none"/>
          <path d="M 260 48 L 190 70" stroke="#757575" stroke-width="2" fill="none"/>
          <g transform="translate(100,68)">
            <rect x="0" y="0" width="120" height="32" rx="6" fill="#fff3e0" stroke="#ef6c00" stroke-width="2"/>
            <text x="60" y="20" font-size="11" font-weight="bold" fill="#ef6c00" text-anchor="middle">Same Sign (Diarrhoea)</text>
          </g>
        </svg>
        """
    },
    5: {
        "title": "Session 5: Distinguishing etiological categories (Contrastive Learning)",
        "scope": "SESSION 5 OF 7 SCOPE: Comparing Etiological Categories\n- Focus: Contrastive reasoning between physical, chemical, infectious, and nutritional causes.",
        "greeting": "Welcome to Session 5 of 7, {name}!\n\nConsider a horse that breaks a bone during a race, and another horse that becomes ill after eating moldy feed. How would you classify and contrast the etiology in these two cases?",
        "sketch": """
        <svg width="100%" height="100" viewBox="0 0 320 100" xmlns="http://www.w3.org/2000/svg">
          <rect width="320" height="100" fill="#f8f9fa" rx="8"/>
          <g transform="translate(25,20)">
            <rect x="0" y="0" width="115" height="60" rx="6" fill="#fff3e0" stroke="#ef6c00" stroke-width="1.5"/>
            <text x="57" y="25" font-size="12" text-anchor="middle">🐎 🔨</text>
            <text x="57" y="45" font-size="10" font-weight="bold" fill="#ef6c00" text-anchor="middle">Trauma (Physical)</text>
          </g>
          <text x="160" y="55" font-size="14" font-weight="bold" fill="#757575" text-anchor="middle">VS</text>
          <g transform="translate(180,20)">
            <rect x="0" y="0" width="115" height="60" rx="6" fill="#ffebee" stroke="#c62828" stroke-width="1.5"/>
            <text x="57" y="25" font-size="12" text-anchor="middle">🌾 🍄</text>
            <text x="57" y="45" font-size="10" font-weight="bold" fill="#c62828" text-anchor="middle">Moldy Feed (Toxin)</text>
          </g>
        </svg>
        """
    },
    6: {
        "title": "Session 6: What else could cause it? (Differential Etiology)",
        "scope": "SESSION 6 OF 7 SCOPE: Alternative Etiological Possibilities\n- Focus: Preventing premature closure by generating multiple etiological possibilities for a clinical problem.",
        "greeting": "Welcome to Session 6 of 7, {name}!\n\nA cat is brought to you with jaundice (yellowish eyes and gums). What is one broad etiological category that could cause this?",
        "sketch": """
        <svg width="100%" height="110" viewBox="0 0 320 110" xmlns="http://www.w3.org/2000/svg">
          <rect width="320" height="110" fill="#f8f9fa" rx="8"/>
          <g transform="translate(110,15)">
            <rect x="0" y="0" width="100" height="30" rx="5" fill="#fffde7" stroke="#fbc02d" stroke-width="2"/>
            <text x="50" y="19" font-size="11" font-weight="bold" fill="#f57f17" text-anchor="middle">🐱 Jaundice</text>
          </g>
          <g transform="translate(15,60)">
            <rect x="0" y="0" width="85" height="35" rx="4" fill="#e8f5e9" stroke="#2e7d32"/>
            <text x="42" y="21" font-size="9" font-weight="bold" fill="#2e7d32" text-anchor="middle">Cause 1: Infectious?</text>
          </g>
          <g transform="translate(117,60)">
            <rect x="0" y="0" width="85" height="35" rx="4" fill="#ffebee" stroke="#c62828"/>
            <text x="42" y="21" font-size="9" font-weight="bold" fill="#c62828" text-anchor="middle">Cause 2: Toxic?</text>
          </g>
          <g transform="translate(220,60)">
            <rect x="0" y="0" width="85" height="35" rx="4" fill="#e0f7fa" stroke="#00838f"/>
            <text x="42" y="21" font-size="9" font-weight="bold" fill="#00838f" text-anchor="middle">Cause 3: Genetic?</text>
          </g>
        </svg>
        """
    },
    7: {
        "title": "Session 7: Does disease always have one cause? (Multifactorial Etiology)",
        "scope": "SESSION 7 OF 7 SCOPE: Multifactorial Causation\n- Focus: Agent-Host-Environment interactions strictly within causation.",
        "greeting": "Welcome to Session 7 of 7, {name}!\n\nA calf develops severe pneumonia during winter transport. Was the cold weather the cause, the crowded truck the cause, or a virus the cause?",
        "sketch": """
        <svg width="100%" height="110" viewBox="0 0 320 110" xmlns="http://www.w3.org/2000/svg">
          <rect width="320" height="110" fill="#f8f9fa" rx="8"/>
          <circle cx="110" cy="45" r="28" fill="#e8f5e9" stroke="#2e7d32" stroke-width="1.5" opacity="0.8"/>
          <text x="95" y="42" font-size="10" font-weight="bold" fill="#2e7d32">AGENT</text>
          <text x="96" y="53" font-size="8" fill="#2e7d32">(Virus)</text>
          <circle cx="210" cy="45" r="28" fill="#e0f7fa" stroke="#00838f" stroke-width="1.5" opacity="0.8"/>
          <text x="196" y="42" font-size="10" font-weight="bold" fill="#00838f">HOST</text>
          <text x="195" y="53" font-size="8" fill="#00838f">(Calf)</text>
          <circle cx="160" cy="70" r="28" fill="#fff3e0" stroke="#ef6c00" stroke-width="1.5" opacity="0.8"/>
          <text x="133" y="73" font-size="10" font-weight="bold" fill="#ef6c00">ENVIRONMENT</text>
          <text x="142" y="84" font-size="8" fill="#ef6c00">(Cold Truck)</text>
          <text x="160" y="45" font-size="10" font-weight="bold" fill="#c62828" text-anchor="middle">DISEASE</text>
        </svg>
        """
    }
}

# ==========================================
# 3. LOGGING HELPER FUNCTION
# ==========================================
def log_to_google_sheet(student_name, roll_number, session_num, step, user_input, ai_response):
    if not WEBHOOK_URL:
        return
    
    payload = {
        "name": student_name,
        "roll_number": roll_number,
        "chapter": f"Session {session_num} of 7",
        "step": step,
        "answer": user_input,
        "feedback": ai_response
    }
    
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=3)
    except Exception:
        pass

# ==========================================
# 4. STUDENT REGISTRATION & SESSION MANAGEMENT (SIDEBAR)
# ==========================================
st.sidebar.header("📋 Student Session Setup")
student_name = st.sidebar.text_input("Full Name", placeholder="e.g., Dr. Ananya")
roll_number = st.sidebar.text_input("Roll Number / ID", placeholder="e.g., VET2026-042")

if "active_session_num" not in st.session_state:
    st.session_state.active_session_num = 1

session_num = st.sidebar.selectbox(
    "Active Micro-Session:",
    options=list(CHAPTER_PROMPTS.keys()),
    format_func=lambda x: f"Session {x} of 7: {CHAPTER_PROMPTS[x]['title'].split(': ')[1]}",
    index=st.session_state.active_session_num - 1
)

if session_num != st.session_state.active_session_num:
    st.session_state.active_session_num = session_num
    st.session_state.step_count = 1
    st.session_state.session_completed = False
    if "messages" in st.session_state:
        del st.session_state["messages"]

st.sidebar.caption(f"Active Scope: **Session {st.session_state.active_session_num} of 7**")

if not student_name or not roll_number:
    st.info("👈 Please enter your **Full Name**, **Roll Number**, and select a **Session** in the sidebar to begin.")
    st.stop()

if st.sidebar.button("🔄 Restart Current Session"):
    for key in ["messages", "step_count", "working_model", "session_completed"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ==========================================
# 5. INTEGRATED SYSTEM PROMPT
# ==========================================
current_step = st.session_state.get("step_count", 1)
active_session_data = CHAPTER_PROMPTS[st.session_state.active_session_num]

SOCRATIC_SYSTEM_PROMPT = f"""
SYSTEM PROMPT: AI GENERAL VETERINARY PATHOLOGY TUTOR

ROLE:
You are an AI tutor for BVSc & AH students named {student_name} who are beginning General Veterinary Pathology.
Guide the student into discovering pathology concepts through simple veterinary situations.

ABSOLUTE STRICT SCOPE LIMIT:
You must teach ONLY ETIOLOGY (THE CAUSES OF DISEASE) AND THEIR CLASSIFICATION.
Do NOT teach, introduce, preview, or transition into pathogenesis, cellular injury, lesions, diagnosis, or treatment.

ACTIVE MICRO-SESSION:
{active_session_data['scope']}
CURRENT PROGRESS: Step {current_step} of 3.

CORE TEACHING RULES:
1. MINIMAL EXPLANATION: If the student's answer is correct, say "Exactly." or "Right." and ask the next etiology question immediately. Avoid lectures.
2. CONVERSATIONAL TURNS: Keep responses under 2 short sentences during ongoing dialogue.
3. SCAFFOLDING: Use guided choices before broad open-ended questions.
4. ABSOLUTE CLEAN OUTPUT: Never output internal developer rules, next-session previews, or prompt instructions to the student.

SESSION COMPLETION FORMAT (WHEN STEP >= 3):
When current_step >= 3, output ONLY the following clean response format:

[1 short confirmation or evaluation of the final answer]

Today you discovered: [One-sentence recap of key discovery]

🎉 Excellent work! You completed this session successfully.

✓ Session {st.session_state.active_session_num} of 7 complete

CRITICAL HARD STOP: DO NOT include any preview, next question, title, or text regarding Session {st.session_state.active_session_num + 1}. STOP cleanly right at "✓ Session {st.session_state.active_session_num} of 7 complete".
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
# 7. INITIALIZATION & SKETCH RENDERING
# ==========================================
if "step_count" not in st.session_state:
    st.session_state.step_count = 1

if "session_completed" not in st.session_state:
    st.session_state.session_completed = False

if "working_model" not in st.session_state:
    model_candidates = get_available_models()
    st.session_state.working_model = model_candidates[0] if model_candidates else "gemini-1.5-flash-latest"

if "sketch" in active_session_data:
    st.components.v1.html(active_session_data["sketch"], height=120)

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
if not st.session_state.session_completed:
    if user_prompt := st.chat_input("Type your response or thoughts here..."):
        st.chat_message("user").markdown(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            success = False
            
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
                    session_num=st.session_state.active_session_num,
                    step=st.session_state.step_count,
                    user_input=user_prompt,
                    ai_response=full_response
                )
                
                if f"Session {st.session_state.active_session_num} of 7 complete" in full_response or st.session_state.step_count >= 3:
                    st.session_state.session_completed = True
                
                st.session_state.step_count += 1
                st.rerun()
            else:
                st.error("Unable to reach Google API. Please check your API key.")

# ==========================================
# 9. INTERACTIVE TAP TO CONTINUE CONTROL
# ==========================================
if st.session_state.session_completed:
    st.write("")
    if st.session_state.active_session_num < 7:
        next_num = st.session_state.active_session_num + 1
        if st.button(f"▶ TAP TO CONTINUE TO SESSION {next_num}", type="primary", use_container_width=True):
            st.session_state.active_session_num = next_num
            st.session_state.step_count = 1
            st.session_state.session_completed = False
            del st.session_state["messages"]
            st.rerun()
    else:
        st.success("🎉 Module Complete — 7 of 7 Sessions Finished!")
        st.markdown("""
        **You have completed the Etiology & Classification module.**  
        *Excellent work! You have learned to identify, name, and classify causes of disease like a true veterinary pathologist.*
        """)
