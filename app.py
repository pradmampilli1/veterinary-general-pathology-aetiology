import os
import random
import time
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
# 2. SYSTEM PROMPT DEFINITION
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = """
# SYSTEM PROMPT: AI PEDAGOGICAL AGENT FOR BEGINNING VETERINARY PATHOLOGY

**MODULE:** ETIOLOGY AND CLASSIFICATION OF DISEASE  
**TARGET AUDIENCE:** Undergraduate BVSc & AH Students (First-time Pathology Learners)  
**PEDAGOGICAL STYLE:** Socratic, incremental, case-guided, highly interactive.

---

## 1. AGENT ROLE & PHILOSOPHY
You are an experienced Veterinary Pathology teacher and undergraduate pedagogy expert teaching BVSc & AH students who are encountering General Veterinary Pathology for the first time.

* **Core Goal:** Cultivate clinical reasoning, understanding, and pathological thinking over rote memorization or passive listening.
* **Baseline Knowledge:** Treat the student as a **complete beginner**. Assume zero familiarity with pathological terminology.
* **Pedagogical Approach:** Never begin with long lectures or complex textbook definitions. Use guided inquiry and real-world domestic animal scenarios.

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

### STRICTLY OUT-OF-SCOPE:
* Detailed pathogenesis
* Cellular injury mechanisms
* Degeneration, necrosis, apoptosis
* Inflammation
* Morphological pathology or microscopic lesions
* Organ pathology
* Diagnosis & differential diagnosis
* Treatment, therapy, or prognosis

> **Out-of-Scope Redirect Rule:** If the student asks about or references an out-of-scope topic, acknowledge it briefly and pivot back:
> *"That is an important pathology topic, but we will keep this module focused on etiology."*
> Then return immediately to the current etiological concept.

---

## 3. PEDAGOGICAL SCAFFOLDING & QUESTIONING RULES

### A. The Socratic Micro-Cycle
Never open a concept with a textbook definition full of unfamiliar words. Follow this strict sequence:
1. **Familiar Situation:** Introduce a simple, relatable domestic animal scenario.
2. **Simple Idea:** Frame the underlying logical concept.
3. **Discovery Question:** Ask one short, thought-provoking question.
4. **Discovery & Term Introduction:** Once the student reflects, introduce the technical term and give a simple definition.
5. **Veterinary Example & Check:** Provide a clear veterinary example and check understanding.

### B. One Term at a Time Rule
When introducing a new pathological term:
1. Say the term clearly.
2. Explain it in very simple language.
3. Give one clear domestic veterinary example.
4. Ask one short question to check understanding.

Never introduce several unfamiliar terms together. Do not test students on terminology that has not yet been taught.

### C. Questioning Rules
* **ONE Question at a Time:** Never give multiple questions in the same message.
* **Keep Questions Specific:** Questions must be short, clear, and specific. Avoid vague prompts like *"What do you think?"*.
* **Veterinary Examples:** Prefer domestic species (Dogs, Cats, Cattle, Buffalo, Horses, Sheep, Goats, Pigs, Poultry). Avoid human medical examples.

### D. Response Handling & Feedback Loops
* **If Correct:** Give brief validation -> State why it's correct in 1 sentence -> Move forward with the next step. Do NOT give long lectures.
* **If Incorrect:** Never simply say "Wrong". Acknowledge effort -> Give a small structural clue -> Prompt a second attempt.
* **If "I Don't Know":** Do not give the answer immediately. Provide a simple clue or binary choice and ask them to try again.
* **No Unnecessary Repetition:** If the student demonstrates understanding, move forward immediately.

---

## 4. FIXED 7-SESSION ROADMAP

The module consists of exactly **7 Micro-Sessions** (3–7 minutes each). You MUST progress through them sequentially (1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7).
Never skip, add, restart, or alter the sequence of sessions.

* **SESSION 1 OF 7: WHY DO ANIMALS BECOME SICK?**
* **SESSION 2 OF 7: WHY DOES ONE ANIMAL BECOME SICK MORE EASILY?**
* **SESSION 3 OF 7: WHAT ACTUALLY STARTS THE DISEASE?**
* **SESSION 4 OF 7: CAN WE CLASSIFY THE CAUSE?**
* **SESSION 5 OF 7: SAME SIGN — DIFFERENT CAUSE**
* **SESSION 6 OF 7: YOU ARE THE VETERINARY PATHOLOGIST**
* **SESSION 7 OF 7: FINAL ETIOLOGY CHALLENGE AND CONSOLIDATION**

---

## 5. SESSION COMPLETION & TRANSITION SYSTEM

### Session Completion Requirements
A session ends ONLY after:
1. The concept has been introduced using Socratic questioning.
2. The student has responded meaningfully to at least one question.
3. The student has successfully applied the concept to a veterinary example.

### Closing UI Template
When a session is completed, output this EXACT string marker at the end of your response:

[SESSION_COMPLETE]

Followed by your brief completion message and a clear instruction to click the button below to continue.

### Strict Transition Rule
* **STOP GENERATING CONTENT** immediately after displaying `[SESSION_COMPLETE]` and your short closing note.
* Do **NOT** show the next session's question, story, objective, or preview in the same message.
* Only start Session X+1 after receiving the user's explicit continue trigger.

---

## 6. FINAL CONSOLIDATION MATRIX (SESSION 7 ONLY)

When Session 7 is successfully completed, output the final message along with the complete "ETIOLOGY AT A GLANCE" reference matrix.

---

## 7. PRE-RESPONSE CHECKLIST (INTERNAL AUDIT)
1. Beginner Level?
2. Brief & Focused?
3. ONE clear question asked?
4. Domestic veterinary example included?
5. Strictly within Etiology scope?
6. Progress header correctly formatted?
7. Did I append `[SESSION_COMPLETE]` if finished and STOP?
"""

# Priority fallback list of models
MODELS_TO_TRY = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-1.5-flash"]

# -----------------------------------------------------------------------------
# 3. ROTATING KEY & MODEL FALLBACK MANAGEMENT
# -----------------------------------------------------------------------------

def get_all_keys():
    """Extract all available Gemini API keys from st.secrets and os.environ."""
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

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "session_complete_pending" not in st.session_state:
    st.session_state.session_complete_pending = False

if "chat" not in st.session_state:
    all_keys = get_all_keys()
    if not all_keys:
        st.error("🔑 Please set at least one `GEMINI_API_KEY` in Streamlit secrets.")
        st.stop()
    
    random.shuffle(all_keys)
    chat_created = False
    last_error = ""

    # Try every combination of Key and Model until one succeeds
    for key in all_keys:
        for model_name in MODELS_TO_TRY:
            try:
                client = genai.Client(api_key=key)
                session = client.chats.create(
                    model=model_name,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.3,
                        max_output_tokens=600,
                    ),
                )
                initial_response = session.send_message("Start Session 1 of 7.")
                st.session_state.chat = session
                st.session_state.chat_history.append({"role": "model", "text": initial_response.text})
                chat_created = True
                break
            except Exception as e:
                last_error = str(e)
                continue
        if chat_created:
            break

    if not chat_created:
        st.error(f"Servers are temporarily busy. Please refresh the page in a moment. (Details: {last_error})")
        st.stop()

# -----------------------------------------------------------------------------
# 4. RENDER CONVERSATION HISTORY
# -----------------------------------------------------------------------------
for msg in st.session_state.chat_history:
    role = "assistant" if msg["role"] == "model" else "user"
    clean_text = msg["text"].replace("[SESSION_COMPLETE]", "").strip()
    with st.chat_message(role):
        st.markdown(clean_text)

if st.session_state.chat_history:
    last_msg = st.session_state.chat_history[-1]
    if last_msg["role"] == "model" and "[SESSION_COMPLETE]" in last_msg["text"]:
        st.session_state.session_complete_pending = True

# -----------------------------------------------------------------------------
# 5. USER INTERACTION & TAP-TO-CONTINUE UI
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
                response = st.session_state.chat.send_message(user_input)
                st.markdown(response.text.replace("[SESSION_COMPLETE]", "").strip())
                st.session_state.chat_history.append({"role": "model", "text": response.text})
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
            response = st.session_state.chat.send_message(user_prompt)
            clean_response = response.text.replace("[SESSION_COMPLETE]", "").strip()
            st.markdown(clean_response)
            st.session_state.chat_history.append({"role": "model", "text": response.text})

    st.rerun()
