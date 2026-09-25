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
st.caption("Etiology & Causation of Diseases — Interactive Socratic Practice")

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

if st.sidebar.button("🔄 Restart Etiology Session"):
    for key in ["messages", "chat_session", "step_count", "working_model"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ==========================================
# 4. SOCRATIC AI SYSTEM INSTRUCTIONS
# ==========================================
SOCRATIC_SYSTEM_PROMPT = f"""
You are an enthusiastic and brilliant Veterinary Pathology Professor tutoring a 2nd-year BVSc & AH student named {student_name} under the VCI syllabus.

STRICT TOPIC SCOPE:
Your session is STRICTLY restricted to "Etiology and Causation of Diseases in Animals" (Chapter: Etiology).
Focus specifically on helping the student master:
1. PREDISPOSING (INTRINSIC) CAUSES:
   - Genetic/Inherited factors: Lethal (e.g., Atresia coli, Parrot beak), Sub-lethal (e.g., Imperforate anus, Scrotal hernia, Deafness in white cats), Inherited structural defects (e.g., Cryptorchidism).
   - Non-genetic / Developmental Anomalies: Arrest of development (Agenesis/Aplasia, Hypoplasia, Atresia, Fissure), Excessive development (Polydactyla, Congenital hypertrophy), Persistence of fetal structures (Persistent urachus), Displacements, Fusion of sexual characters (Freemartin, Hermaphrodite).
   - Intrinsic Factors: Genus (Rinderpest in cattle vs man), Breed (Malignant melanoma in Grey horses, Brain tumors in Bulldogs, Bone tumors in Great Danes, Dairy vs Beef cattle susceptibility), Age (Strangles in young horses, Tumors in older animals), Sex (Goiter/Liver diseases vs Nephritis), and Color/Pigment (Photodynamic sensitivity & Melanoma in grey coat).
2. EXCITING (EXTRINSIC) CAUSES:
   - Physical causes: Radiation/Thermal/Sunburns, Cold (Frostbite/Necrosis), Electricity, Atmospheric pressure (Brisket disease, Caisson disease), Mechanical trauma (Perforation, Laceration, Concussion).

PEDAGOGICAL & DIALOGUE STYLE:
1. Make it exciting and highly relevant to veterinary practice! Use real animal examples (horses, dogs, cattle, cats, poultry) to pique their interest.
2. Ask ONE focused, thought-provoking Socratic question at a time.
3. Keep responses concise (2–4 sentences max) so the interaction feels lively.
4. When the student answers, praise their veterinary intuition, correct or refine any terms according to standard pathology terminology, and bridge logically to the next concept in disease causation.
5. Do NOT leap into advanced clinical treatment or systemic gross pathology. Keep the focus entirely on disease etiology, intrinsic predisposing factors, and exciting causes.
"""

# ==========================================
# 5. DYNAMIC MODEL SELECTION (PREVENTS 404/429)
# ==========================================
@st.cache_resource
def get_available_models():
    """Queries Google API for currently active models on this key."""
    try:
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # Remove 'models/' prefix if present
                clean_name = m.name.replace("models/", "")
                available.append(clean_name)
        # Prioritize flash models
        flash_models = [m for m in available if "flash" in m]
        other_models = [m for m in available if "flash" not in m]
        return flash_models + other_models
    except Exception:
        # Emergency fallback priority list
        return ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]

# ==========================================
# 6. CHAT INITIALIZATION & SESSION STATE
# ==========================================
if "step_count" not in st.session_state:
    st.session_state.step_count = 1

if "working_model" not in st.session_state:
    model_candidates = get_available_models()
    st.session_state.working_model = model_candidates[0] if model_candidates else "gemini-1.5-flash-latest"

if "chat_session" not in st.session_state:
    model = genai.GenerativeModel(
        model_name=st.session_state.working_model,
        system_instruction=SOCRATIC_SYSTEM_PROMPT
    )
    st.session_state.chat_session = model.start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []
    initial_greeting = f"""Welcome {student_name}! Today we will explore **Etiology: The Causation of Diseases in Animals**.

Let's start with an interesting case observation:

In equine practice, an old **Grey horse** is significantly more likely to develop **Malignant Melanoma** than a bay or chestnut horse of the same age. Similarly, white-skinned animals suffer more frequently from sun-induced skin inflammation.

In disease causation, would you classify coat color or breed as an **Intrinsic Predisposing Cause** or an **Extrinsic Exciting Cause** of disease? What is your reasoning?"""
    
    st.session_state.messages.append({"role": "assistant", "content": initial_greeting})

# Render existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 7. USER INPUT & STREAMED RESPONSE WITH AUTO-FAILOVER
# ==========================================
if user_prompt := st.chat_input("Type your response here..."):
    st.chat_message("user").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        success = False
        
        # Try primary model first, fallback to candidates if 404/429 hits
        candidates = [st.session_state.working_model] + get_available_models()
        # Remove duplicates while preserving order
        candidate_list = list(dict.fromkeys(candidates))
        
        for model_candidate in candidate_list:
            try:
                # Re-init chat if switching models mid-stream
                if model_candidate != st.session_state.working_model:
                    fallback_model = genai.GenerativeModel(
                        model_name=model_candidate,
                        system_instruction=SOCRATIC_SYSTEM_PROMPT
                    )
                    # Convert history to format expected by start_chat
                    chat_history = []
                    for m in st.session_state.messages[:-1]:
                        role = "user" if m["role"] == "user" else "model"
                        chat_history.append({"role": role, "parts": [m["content"]]})
                    
                    st.session_state.chat_session = fallback_model.start_chat(history=chat_history)
                    st.session_state.working_model = model_candidate

                response = st.session_state.chat_session.send_message(user_prompt, stream=True)
                for chunk in response:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                success = True
                break  # Exit fallback loop on success
                
            except Exception as e:
                # If 404 or 429, try next model in candidate list quietly
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
            st.error("Unable to reach Google API across active models. Please check your API key in Streamlit Secrets.")
