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

# Read Secrets
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", None)
except Exception:
    st.error("Missing secrets! Please configure GEMINI_API_KEY in Streamlit Advanced Settings.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# 2. CHAPTER SYLLABUS DEFINITIONS
# ==========================================
CHAPTER_PROMPTS = {
    "1. Etiology & Causation of Diseases": """
STRICT TOPIC SCOPE: Chapter 1 - Etiology & Causation of Diseases
Focus ONLY on classification of etiologic agents and brief veterinary examples. DO NOT dive into detailed pathogenesis or full disease descriptions.

1. Intrinsic Predisposing Causes (Classification & Examples):
   - Genus & Breed predisposition (e.g., Hereford cattle and ocular squamous cell carcinoma, Bulldogs and dystocia).
   - Age, Sex, & Pigment factors (e.g., Squamous cell carcinoma in unpigmented skin).
   - Inherited/Genetic Anomalies: Lethal factors (e.g., Atresia coli in foals) vs Sub-lethal factors (e.g., Congenital deafness in white cats).
   - Developmental Anomalies: Basic definitions & examples of Agenesis, Hypoplasia, Aplasia, Atresia, Freemartinism, and Hermaphroditism.

2. Extrinsic Exciting Causes (Classification & Examples):
   - Physical Agents: Thermal (Burns/Frostbite), Radiation, Electricity, Atmospheric pressure (Brisket Disease / High altitude disease in cattle).
   - Mechanical Trauma: Laceration, Concussion, Perforation, Rupture.
   - Chemical & Biotic Agents: Toxins, Infectious microbes, Parasites (Brief naming and classification only).
""",
    "2. Retrograde Tissue Changes (Degenerations)": """
STRICT TOPIC SCOPE: Chapter 2 - Retrograde Tissue Changes
1. Cloudy swelling, Hydropic degeneration, Fatty change (Steatosis) vs Fatty infiltration.
2. Hyaline, Amyloid, Mucoid, and Myxomatous degenerations.
3. Pathological Calcification: Dystrophic vs Metastatic calcification.
4. Necrosis vs Apoptosis: Types of necrosis (Coagulative, Liquefactive, Caseous, Fat necrosis, Gangrene).
""",
    "3. Disturbances of Circulation": """
STRICT TOPIC SCOPE: Chapter 3 - Disturbances of Circulation
1. Hyperemia & Congestion (Active vs Passive, Chronic Passive Congestion of Liver/Nutmeg liver and Lungs/Heart failure cells).
2. Hemorrhage, Hemostasis, and Thrombosis (Virchow's Triad, Types of Thrombi).
3. Embolism, Ischemia, Infarction, and Edema (Pathophysiology & Transudate vs Exudate).
4. Shock: Hypovolemic, Cardiogenic, Vasogenic, Septic.
""",
    "4. Inflammation & Healing": """
STRICT TOPIC SCOPE: Chapter 4 - Inflammation & Tissue Repair
1. Vascular and Cellular events of Acute Inflammation (Vasodilation, Margination, Diapedesis, Chemotaxis, Phagocytosis).
2. Chemical Mediators of Inflammation.
3. Morphological patterns: Serous, Fibrinous, Purulent/Suppurative, Catarrhal, Hemorrhagic, Granulomatous.
4. Tissue Repair: Granulation tissue formation, Healing by Primary & Secondary intention.
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
# 4. STUDENT REGISTRATION & CHAPTER SELECTION (SIDEBAR)
# ==========================================
st.sidebar.header("📋 Student Session Setup")
student_name = st.sidebar.text_input("Full Name", placeholder="e.g., Dr. Ananya")
roll_number = st.sidebar.text_input("Roll Number / ID", placeholder="e.g., VET2026-042")

selected_chapter = st.sidebar.selectbox(
    "Select Pathology Chapter:",
    list(CHAPTER_PROMPTS.keys())
)

st.caption(f"Active Topic: **{selected_chapter}**")

if not student_name or not roll_number:
    st.info("👈 Please enter your **Full Name**, **Roll Number**, and select a **Chapter** in the sidebar to begin.")
    st.stop()

# Reset chat session if chapter selection changes
if "current_chapter" in st.session_state and st.session_state.current_chapter != selected_chapter:
    for key in ["messages", "step_count"]:
        if key in st.session_state:
            del st.session_state[key]

st.session_state.current_chapter = selected_chapter

if st.sidebar.button("🔄 Restart Chapter Session"):
    for key in ["messages", "step_count", "working_model"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ==========================================
# 5. DYNAMIC SOCRATIC SYSTEM PROMPT
# ==========================================
SOCRATIC_SYSTEM_PROMPT = f"""
You are an expert Veterinary Pathology Professor tutoring a 2nd-year BVSc & AH student named {student_name} under the VCI syllabus.

{CHAPTER_PROMPTS[selected_chapter]}

STRICT PEDAGOGICAL & SCOPE RULES:
1. FOCUS ON CLASSIFICATION & EXAMPLES: Keep Chapter 1 strictly about naming/classifying causes and providing classical veterinary examples. Do not ask for or explain full disease mechanisms or clinical features.
2. FOCUS ON ONE CONCEPT AT A TIME: Do not switch sub-topics until the current classification or term is clearly understood.
3. HANDLING 'DON'T KNOW' OR INCORRECT ANSWERS:
   - If the student says "don't know", gives an incomplete answer, or gets it wrong, DO NOT jump to a new topic.
   - Explain the current classification briefly (1–2 sentences) with a clean veterinary example.
   - Ask a simple follow-up question ON THE SAME CONCEPT to check understanding.
4. SOCRATIC FEEDBACK LOOP:
   - Praise correct reasoning and correct terminology errors using standard VCI terms.
   - End EVERY turn with EXACTLY ONE logical question.
   - Keep responses concise (2–3 sentences max).
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
    initial_greeting = f"""Welcome {student_name}! Today we will review **{selected_chapter}**.

We will focus on classifying disease causes and their classic veterinary examples. Are you ready to start?"""
    
    st.session_state.messages.append({"role": "assistant", "content": initial_greeting})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 8. USER INPUT & STREAMED RESPONSE WITH AUTO-FAILOVER
# ==========================================
if user_prompt := st.chat_input("Type your answer or response here..."):
    st.chat_message("user").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        success = False
        
        # Capped history buffer (last 6 messages) to maintain prompt adherence
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
