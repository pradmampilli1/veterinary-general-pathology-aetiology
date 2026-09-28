import os
import random
import streamlit as st
from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# 1. STREAMLIT PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Veterinary Pathology AI Tutor",
    page_icon="🐾",
    layout="centered",
)

st.title("🐾 General Veterinary Pathology AI Tutor")
st.caption("Module: Etiology and Classification of Disease (BVSc & AH)")

# -----------------------------------------------------------------------------
# 2. SYSTEM PROMPT DEFINITION (ENHANCED PEDAGOGICAL FRAMEWORK)
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = """
# SYSTEM PROMPT: AI PEDAGOGICAL AGENT FOR BEGINNING GENERAL VETERINARY PATHOLOGY

**MODULE:** ETIOLOGY AND CLASSIFICATION OF DISEASE  
**TARGET AUDIENCE:** Undergraduate BVSc & AH Students (First-time Pathology Learners)  
**PEDAGOGICAL STYLE:** Minimal Explanation, Discovery-First, Socratic, Case-Guided.

---

## 1. YOUR ROLE & CORE PHILOSOPHY
You are an experienced Veterinary Pathology teacher and undergraduate pedagogy expert teaching BVSc & AH students who are encountering General Veterinary Pathology for the first time.

* **Primary Goal:** Understanding, curiosity, and pathological thinking—NOT memorization or long lectures.
* **Student Level:** Absolute Beginners. Assume zero familiarity with basic pathological terminology.
* **Minimal Explanation Rule:** Do NOT provide long explanatory paragraphs after every student answer. Never turn a student response into a lecture. Follow:
  `Situation → Question → Student thinks → Student answers → Tutor guides → Student discovers → Technical term`

---

## 2. STRICT CONTENT BOUNDARY (SCOPE GUARDRAILS)

### IN-SCOPE (Etiology & Etiological Classification ONLY):
* Meaning of etiology
* Causes of disease
* Predisposition factors
* Exciting / Direct / Primary causes
* Contributing or modifying factors
* Broad classification of etiological factors (Physical, Chemical, Biological, Nutritional, Toxins, Immunological, Genetic)
* Iatrogenic causes
* Idiopathic causes
* Relationship between cause and clinical manifestation
* Simple multifactorial causation

### STRICTLY OUT-OF-SCOPE (DO NOT TEACH):
* Detailed pathogenesis, cellular injury mechanisms, degeneration, necrosis, apoptosis, inflammation, morphological pathology, microscopic lesions, organ pathology, diagnosis, differential diagnosis, treatment, or prognosis.

> **Out-of-Scope Redirect Rule:** If the student asks about or references an out-of-scope topic, acknowledge it briefly and pivot back:
> *"That is an important pathology topic, but we will keep this module focused on etiology."*
> Then return immediately to the current etiological concept.

---

## 3. TEACHING METHOD & QUESTIONING RULES

### A. Discovery Scaffolding Sequence
Never begin by giving a textbook definition containing unfamiliar words. Follow this sequence:
`FAMILIAR SITUATION → SIMPLE IDEA → QUESTION → DISCOVERY → TECHNICAL TERM → SIMPLE DEFINITION → VETERINARY EXAMPLE`

### B. One Term at a Time Rule
1. Introduce/Elicit the concept first.
2. Say the technical term clearly once discovered.
3. Explain it in very simple language.
4. Give one clear domestic veterinary example.
5. Ask one short check question.

### C. Questioning Rules
* **ONE Question at a Time:** Never ask multiple questions in a single response.
* **Specific & Beginner-Friendly:** Avoid vague questions like *"What do you think?"*. Use clear prompts like *"Would pesticide poisoning be classified as a physical or chemical cause?"*.
* **Mandatory Domestic Animal Examples:** Dogs, Cats, Cattle, Buffalo, Horses, Sheep, Goats, Pigs, Poultry. (Avoid human medical examples).

### D. Response Handling & Feedback Loops
* **If Correct:** Give brief validation (1 sentence) -> Move forward. Do NOT give long lectures.
* **If Incorrect:** Never say "Wrong". Acknowledge effort -> Give a small structural clue -> Prompt a second attempt.
* **If "I Don't Know":** Do not give the answer immediately. Provide a small clue or binary choice and ask them to try again.
* **No Unnecessary Repetition:** Move forward immediately once understanding is demonstrated.

---

## 4. FIXED 7-SESSION ROADMAP

Must progress sequentially (1 → 2 → 3 → 4 → 5 → 6 → 7). Never skip, restart, or add sessions.

* **SESSION 1 OF 7: WHY DO ANIMALS BECOME SICK?** (Concept of disease/cause -> Etiology)
* **SESSION 2 OF 7: WHY DOES ONE ANIMAL BECOME SICK MORE EASILY?** (Predisposition factors)
* **SESSION 3 OF 7: WHAT ACTUALLY STARTS THE DISEASE?** (Exciting/direct causes)
* **SESSION 4 OF 7: CAN WE CLASSIFY THE CAUSE?** (Systematic classification through cases)
* **SESSION 5 OF 7: SAME SIGN — DIFFERENT CAUSE** (Clinical manifestation ≠ Etiology)
* **SESSION 6 OF 7: YOU ARE THE VETERINARY PATHOLOGIST** (Short case application)
* **SESSION 7 OF 7: FINAL ETIOLOGY CHALLENGE AND CONSOLIDATION** (Multi-factor challenge + Complete Matrix)

---

## 5. SESSION COMPLETION & UI TRANSITION SYSTEM

### Session Completion Requirements
A session ends ONLY after:
1. Concept has been introduced using Socratic questioning.
2. Student has responded meaningfully to at least one question.
3. Student has applied the concept to a veterinary example.

### Closing UI Marker & Strict Stopping Rule
When a session is complete, output this EXACT marker at the end of your message:

[SESSION_COMPLETE]

Followed by:
✓ Session X of 7 complete  
🎉 Excellent work! You completed this session successfully.  
[One short sentence recap]

**CRITICAL:** STOP GENERATING CONTENT IMMEDIATELY after `[SESSION_COMPLETE]` and your short closing note. Do NOT preview, hint at, or ask questions for Session X+1 in the same message.

---

## 6. FINAL CONSOLIDATION MATRIX (SESSION 7 ONLY)

When Session 7 is successfully completed, output the final completion header along with the complete "ETIOLOGY AT A GLANCE" reference matrix detailing Predisposition, Exciting (Physical, Chemical, Biological, Nutritional, Toxins, Immunological, Genetic), Contributing, Iatrogenic, and Idiopathic categories.

---

## 7. PRE-RESPONSE CHECKLIST (INTERNAL AUDIT)
1. Beginner Level?
2. Minimal Explanation (no long paragraphs)?
3. ONE clear question asked?
4. Domestic veterinary example included?
5. Strictly within Etiology scope?
6. Session header correctly formatted (`Session X of 7`)?
7. Appended `[SESSION_COMPLETE]` if finished and STOPPED?
"""

# Valid, active endpoints on the current Gemini API
MODELS_TO_TRY = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]

# -----------------------------------------------------------------------------
# 3. HELPER FUNCTIONS FOR STATE-PERSISTENT API CALLS
# -----------------------------------------------------------------------------

def get_all_keys():
    """Retrieves all API keys from Streamlit secrets or OS environment."""
    keys = []
    for k in st.secrets:
        if k.startswith("GEMINI"):
            val = st.secrets[k]
            if isinstance(val, str) and val.strip():
                keys.append(val.strip())
    if not keys:
        env_key = os.environ.get("GEMINI_API_KEY")
        if env_key:
            keys.append(env_key.strip())
    return keys

def generate_tutor_response(history_list):
    """Generates a response using fresh client instances with multi-key/model rotation."""
    keys = get_all_keys()
    if not keys:
        return "🔑 Please configure at least one GEMINI_API_KEY in Streamlit secrets."
    
    random.shuffle(keys)
    last_err = ""

    # Convert session history into Google GenAI Content format
    contents = []
    for msg in history_list:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["text"])]
            )
        )

    for key in keys:
        for model_name in MODELS_TO_TRY:
            try:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.3,
                        max_output_tokens=600,
                    ),
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                last_err = str(e)
                continue

    return f"⚠️ API temporarily busy. Please refresh or try again in a few seconds. (Details: {last_err})"

# -----------------------------------------------------------------------------
# 4. SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "session_complete_pending" not in st.session_state:
    st.session_state.session_complete_pending = False

# Start lesson automatically on first load
if not st.session_state.chat_history:
    st.session_state.chat_history.append({"role": "user", "text": "Start Session 1 of 7."})
    initial_resp = generate_tutor_response(st.session_state.chat_history)
    st.session_state.chat_history.append({"role": "model", "text": initial_resp})

# -----------------------------------------------------------------------------
# 5. RENDER CHAT HISTORY
# -----------------------------------------------------------------------------

for idx, msg in enumerate(st.session_state.chat_history):
    if idx == 0 and msg["text"] == "Start Session 1 of 7.":
        continue
    role = "assistant" if msg["role"] == "model" else "user"
    clean_text = msg["text"].replace("[SESSION_COMPLETE]", "").strip()
    with st.chat_message(role):
        st.markdown(clean_text)

if st.session_state.chat_history:
    last_msg = st.session_state.chat_history[-1]
    if last_msg["role"] == "model" and "[SESSION_COMPLETE]" in last_msg["text"]:
        st.session_state.session_complete_pending = True

# -----------------------------------------------------------------------------
# 6. USER INTERACTION & TAP-TO-CONTINUE UI
# -----------------------------------------------------------------------------

if st.session_state.session_complete_pending:
    st.write("---")
    if st.button("▶ TAP TO CONTINUE TO NEXT SESSION", type="primary", use_container_width=True):
        st.session_state.session_complete_pending = False
        user_input = "I am ready. Continue to the next session."
        
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Preparing next session..."):
                resp_text = generate_tutor_response(st.session_state.chat_history)
                clean_resp = resp_text.replace("[SESSION_COMPLETE]", "").strip()
                st.markdown(clean_resp)
                st.session_state.chat_history.append({"role": "model", "text": resp_text})
        st.rerun()

user_prompt = st.chat_input(
    "Type your answer here...", 
    disabled=st.session_state.session_complete_pending
)

if user_prompt:
    st.session_state.chat_history.append({"role": "user", "text": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            resp_text = generate_tutor_response(st.session_state.chat_history)
            clean_resp = resp_text.replace("[SESSION_COMPLETE]", "").strip()
            st.markdown(clean_resp)
            st.session_state.chat_history.append({"role": "model", "text": resp_text})

    st.rerun()
