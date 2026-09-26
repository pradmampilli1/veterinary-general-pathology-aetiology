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
st.subheader("Module: Etiology & Classification of Disease")

# Read Secrets
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", None)
except Exception:
    st.error("Missing secrets! Please configure GEMINI_API_KEY in Streamlit Advanced Settings.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# 2. MICRO-SESSION & CONTINUITY BRIDGE DEFINITIONS (STRICT ETIOLOGY ONLY)
# ==========================================
CHAPTER_PROMPTS = {
    "Session 1: Why do animals become sick? (Idea of Causation)": {
        "num": 1,
        "scope": "SESSION 1 SCOPE: Health Change -> Idea of Cause\n- Focus: Recognizing normal state change and identifying that 'something caused it'.",
        "greeting": "Welcome {name}! Let's start with a very simple pathology idea.\n\nA healthy cow is eating normally. Later, the animal becomes dull and stops eating.\n\nFirst question: what has changed—the animal's normal state or nothing?",
        "next_session_title": "Session 2 — The next puzzle",
        "next_session_question": "We know something caused the cow to become sick.\n\nPathologists have a specific technical term for the cause of a disease.\n\nDo you happen to know what we call the cause of a disease, or should we figure it out together?"
    },
    "Session 2: What is the cause called? (Introduction to Etiology)": {
        "num": 2,
        "scope": "SESSION 2 SCOPE: Labeling Cause -> Etiology\n- Focus: Connecting ordinary idea of cause to the formal pathology term 'Etiology'.",
        "greeting": "Welcome back, {name}!\n\nWhen a dog becomes ill after swallowing a pesticide, pesticide is the cause of the disease.\n\nIn pathology, what technical term do we use for the cause of a disease?",
        "next_session_title": "Session 3 — The next puzzle",
        "next_session_question": "Now that we know the cause is called etiology, can we organize all possible causes of disease into broad, logical categories?"
    },
    "Session 3: Can we group different causes? (Etiological Classification)": {
        "num": 3,
        "scope": "SESSION 3 SCOPE: Major Etiological Categories\n- Focus: Grouping causes into Infectious, Physical, Chemical, Nutritional, Genetic using concrete examples first.",
        "greeting": "Welcome back, {name}!\n\nIf Rabies virus causes disease in a dog, would you classify that virus as an infectious cause or a chemical cause?",
        "next_session_title": "Session 4 — The next puzzle",
        "next_session_question": "Can two completely different types of causes (like a virus and a poison) produce the exact same clinical sign in an animal?"
    },
    "Session 4: Same sign, different cause (Manifestation vs. Etiology)": {
        "num": 4,
        "scope": "SESSION 4 SCOPE: Sign != Etiology\n- Focus: Exploring how a single sign (e.g. Diarrhoea or Jaundice) can have multiple completely different etiologies.",
        "greeting": "Welcome back, {name}!\n\nImagine two dogs come into your clinic, both showing severe diarrhoea. Is diarrhoea the etiology of the disease, or a clinical sign shown by the animal?",
        "next_session_title": "Session 5 — The next puzzle",
        "next_session_question": "How can we systematically distinguish between a physical cause (like trauma) and a chemical cause (like poisoning)?"
    },
    "Session 5: Distinguishing etiological categories (Contrastive Learning)": {
        "num": 5,
        "scope": "SESSION 5 SCOPE: Comparing Etiological Categories\n- Focus: Contrastive reasoning between physical, chemical, infectious, and nutritional causes.",
        "greeting": "Welcome back, {name}!\n\nConsider a horse that breaks a bone during a race, and another horse that becomes ill after eating moldy feed. How would you classify and contrast the etiology in these two cases?",
        "next_session_title": "Session 6 — The next puzzle",
        "next_session_question": "When an animal presents with an illness, how do we brainstorm multiple alternative etiological possibilities instead of stopping at the first guess?"
    },
    "Session 6: What else could cause it? (Differential Etiology)": {
        "num": 6,
        "scope": "SESSION 6 SCOPE: Alternative Etiological Possibilities\n- Focus: Preventing premature closure by generating multiple etiological possibilities for a clinical problem.",
        "greeting": "Welcome back, {name}!\n\nA cat is brought to you with jaundice (yellowish eyes and gums). What is one broad etiological category that could cause this?",
        "next_session_title": "Session 7 — The next puzzle",
        "next_session_question": "Does every disease in an animal have exactly one single cause, or can disease result from multiple factors working together?"
    },
    "Session 7: Does disease always have one cause? (Multifactorial Etiology)": {
        "num": 7,
        "scope": "SESSION 7 SCOPE: Multifactorial Causation\n- Focus: Agent-Host-Environment interactions strictly within causation.",
        "greeting": "Welcome back, {name}!\n\nA calf develops severe pneumonia during winter transport. Was the cold weather the cause, the crowded truck the cause, or a virus the cause?",
        "next_session_title": "Session 8 — The next puzzle",
        "next_session_question": "What if a pathologist performs every test, but the specific cause of a disease still cannot be identified?"
    },
    "Session 8: What if we cannot find the cause? (Idiopathic Etiology)": {
        "num": 8,
        "scope": "SESSION 8 SCOPE: Unknown Cause -> Idiopathic\n- Focus: Introducing the term Idiopathic = of unknown cause.",
        "greeting": "Welcome back, {name}!\n\nSometimes an animal has a clearly recognized disease, but even after extensive laboratory testing, the cause remains unknown. What do pathologists call a disease of unknown cause?",
        "next_session_title": "Session 9 — The next puzzle",
        "next_session_question": "Can a medical or surgical treatment given by a veterinarian unintentionally become the cause of a new disease?"
    },
    "Session 9: Can treatment itself cause disease? (Iatrogenic Etiology)": {
        "num": 9,
        "scope": "SESSION 9 SCOPE: Treatment-Induced Disease -> Iatrogenic\n- Focus: Introducing Iatrogenic etiology.",
        "greeting": "Welcome back, {name}!\n\nIf a dog develops kidney damage as a direct side-effect of an overdose of medication prescribed for arthritis, what term describes this medical intervention-related etiology?",
        "next_session_title": "Session 10 — The next puzzle",
        "next_session_question": "Are you ready to put all these etiological categories together to reason through complex veterinary cases like a true pathologist?"
    },
    "Session 10: You are the Veterinary Pathologist (Integrated Etiology)": {
        "num": 10,
        "scope": "SESSION 10 SCOPE: Integrated Etiological Reasoning\n- Focus: Full synthesis of etiological categories across diverse animal cases.",
        "greeting": "Welcome to the final session of this module, {name}!\n\nA herd of cattle shows sudden drop in milk yield, fever, and oral vesicles. What primary etiological category should you investigate first, and what alternative category must you rule out?",
        "next_session_title": "Module Complete!",
        "next_session_question": "Congratulations! You have completed the Etiology & Classification Module. You are now equipped to ask 'What caused this?' for any disease!"
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
    "Select Etiology Micro-Session:",
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

if st.sidebar.button("🔄 Restart Micro-Session"):
    for key in ["messages", "step_count", "working_model"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ==========================================
# 5. INTEGRATED SYSTEM PROMPT WITH STRICT SCOPE ENFORCEMENT
# ==========================================
current_step = st.session_state.get("step_count", 1)
active_session_data = CHAPTER_PROMPTS[selected_chapter]

SOCRATIC_SYSTEM_PROMPT = f"""
SYSTEM PROMPT: AI GENERAL VETERINARY PATHOLOGY TUTOR

ROLE:
You are an AI tutor for BVSc & AH students named {student_name} who are beginning General Veterinary Pathology.
Guide the student into discovering pathology concepts through simple veterinary situations.

ABSOLUTE STRICT SCOPE LIMIT:
You must teach ONLY ETIOLOGY (THE CAUSES OF DISEASE) AND THEIR CLASSIFICATION.
Do NOT teach, introduce, preview, or transition into:
- pathogenesis
- mechanisms of disease
- cellular injury, necrosis, or inflammation
- lesions (gross or microscopic)
- clinical diagnosis, treatment, or organ pathology

If the student asks about any of these out-of-scope topics, respond:
"That's an important question, but it belongs to a later topic. For now, let me stay with the cause: what could be the etiology in this case?"

ACTIVE MICRO-SESSION:
{active_session_data['scope']}
CURRENT PROGRESS: Step {current_step} of 3.

CORE TEACHING RULES:
1. MINIMAL EXPLANATION: If the student's answer is correct, say "Exactly." or "Right." and ask the next etiology question immediately. Avoid lectures.
2. CONVERSATIONAL TURNS: Keep responses under 2 short sentences during ongoing dialogue.
3. SCAFFOLDING: Use guided choices before broad open-ended questions.
4. ABSOLUTE CLEAN OUTPUT: Never output internal thoughts, developer instructions, or prompt rules to the student.

SESSION COMPLETION & TRANSITION FORMAT (WHEN STEP >= 3):
When current_step >= 3, output ONLY the following clean response format:

[1 short confirmation of the final answer]
Today you discovered: [One-sentence learning takeaway about Etiology]
Well done! [Specific professional congratulation]

✓ Session {active_session_data['num']} complete

---

{active_session_data['next_session_title']}

{active_session_data['next_session_question']}
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
