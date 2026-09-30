import os
import random
import json
import streamlit as st

# -----------------------------------------------------------------------------
# 1. STREAMLIT PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Veterinary Pathology AI Tutor",
    page_icon="🐾",
    layout="centered",
)

# -----------------------------------------------------------------------------
# 2. SESSION STATE & AUTHENTICATION INITIALIZATION
# -----------------------------------------------------------------------------
if "student_logged_in" not in st.session_state:
    st.session_state.student_logged_in = False

if "student_name" not in st.session_state:
    st.session_state.student_name = ""

if "student_id" not in st.session_state:
    st.session_state.student_id = ""

if "completed_sessions" not in st.session_state:
    st.session_state.completed_sessions = []

if "current_session_num" not in st.session_state:
    st.session_state.current_session_num = 1

if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = ""

if "show_next_button" not in st.session_state:
    st.session_state.show_next_button = False

# -----------------------------------------------------------------------------
# 3. ISOLATED STUDENT LOGIN SCREEN
# -----------------------------------------------------------------------------
if not st.session_state.student_logged_in:
    st.title("🐾 General Veterinary Pathology AI Tutor")
    st.caption("Module: Etiology and Classification of Disease (BVSc & AH)")
    st.markdown("*Department of Veterinary Pathology, CVAS, Pookode*")
    st.write("---")
    
    st.subheader("👨‍🎓 Student Access Login")
    st.info("Please enter your details to start the learning session.")
    
    with st.form("student_login_form"):
        name_input = st.text_input("Full Name:", placeholder="e.g., Ananya R.")
        id_input = st.text_input("Admission Number / Roll No:", placeholder="e.g., 2024-04-102")
        submit_button = st.form_submit_button("🚀 Start Learning Session", type="primary")
        
        if submit_button:
            if name_input.strip() and id_input.strip():
                st.session_state.student_name = name_input.strip()
                st.session_state.student_id = id_input.strip()
                st.session_state.student_logged_in = True
                st.rerun()
            else:
                st.error("Please enter both your Full Name and Admission Number to proceed.")
    
    st.stop()

# -----------------------------------------------------------------------------
# 4. FULL 7-SESSION CURRICULUM DATABASE (COMPLETE & UNABRIDGED)
# -----------------------------------------------------------------------------
CURRICULUM_SESSIONS = {
    1: {
        "title": "Session 1 of 7 — What is Etiology?",
        "intro": "Welcome! As first-year veterinary students, our central question throughout this module is simply: **WHY did this animal become sick?** Let's start with a real farm observation.",
        "scenario": "Two dairy calves are housed under identical management conditions on the CVAS Pookode farm. After a sudden cold night and heavy rain, Calf B develops a severe cough and high fever, while Calf A remains completely healthy and active.",
        "question": "What is the most logical reason or factor that explains why Calf B fell sick while Calf A stayed healthy?",
        "options": [
            "A) Calf B encountered an environmental stressor or agent that triggered disease",
            "B) Calf B completed its normal surgical recovery cycle",
            "C) Calf B underwent standard microscopic cellular staining"
        ],
        "correct_option": "A",
        "feedback_correct": "Spot on! Investigating *why* and *how* a disease process starts is the fundamental foundation of pathology.",
        "feedback_incorrect": "Good attempt. Think about what we are trying to find out—we are searching for the underlying trigger or agent that caused the sickness.",
        "term_card": {
            "term": "ETIOLOGY",
            "meaning": "The study of the cause of disease (Core question: WHY did the animal become sick?).",
            "example": "Finding out why a calf developed a sudden fever after cold weather exposure."
        },
        "recap": "Etiology is the study of disease causes, starting with the central question: Why did this animal become sick?"
    },
    2: {
        "title": "Session 2 of 7 — Predisposing Causes",
        "intro": "Now that we know etiology deals with causes, let's explore factors that do not directly cause disease on their own, but make an animal more vulnerable.",
        "scenario": "A herd of mixed-breed cattle is exposed to intense tropical sunlight. White-faced Hereford cattle develop skin cancer lesions on their unpigmented eyelids, while fully pigmented Angus cattle in the same field show no lesions.",
        "question": "Why did only the Hereford cattle develop sun-related eye lesions under the exact same sunlight?",
        "options": [
            "A) Their specific breed trait and lack of pigment made them more susceptible",
            "B) They were infected by a bacterial virus spread through water",
            "C) They consumed toxic pasture weeds"
        ],
        "correct_option": "A",
        "feedback_correct": "Correct! Factors like breed, age, sex, and pigmentation make an animal more vulnerable. These are called **Predisposing Causes**.",
        "feedback_incorrect": "Good try. Both cattle groups faced the exact same environment, but one group's biological traits made them more susceptible.",
        "term_card": {
            "term": "PREDISPOSING CAUSE",
            "meaning": "A factor that makes an animal more susceptible or vulnerable to disease.",
            "example": "Breed-associated pigmentation making Hereford cattle prone to eye cancer under sunlight."
        },
        "recap": "Predisposing causes (like breed, age, sex, and heredity) make an animal more susceptible to disease."
    },
    3: {
        "title": "Session 3 of 7 — Definitive Causes: Physical",
        "intro": "While predisposing factors make an animal susceptible, **Definitive Causes** are the actual agents or forces that directly produce disease or tissue injury.",
        "scenario": "An adult German Shepherd dog is hit by a speeding vehicle on a village road, resulting in a fractured femur and severe soft tissue damage.",
        "question": "What broad category of definitive disease causes does a vehicular impact represent?",
        "options": [
            "A) Physical cause (Mechanical trauma)",
            "B) Nutritional deficiency",
            "C) Biological bacterial infection"
        ],
        "correct_option": "A",
        "feedback_correct": "Excellent! Mechanical trauma, extreme heat, cold, and radiation are all **Physical Causes** of disease.",
        "feedback_incorrect": "Not quite. A physical impact or crash force is an external energy transfer, making it a physical cause.",
        "term_card": {
            "term": "PHYSICAL CAUSE",
            "meaning": "Harmful physical force, energy, or extremes of temperature/radiation that injure tissues.",
            "example": "A dog injured in a road accident (mechanical trauma)."
        },
        "recap": "Physical definitive causes include trauma, heat, cold, and radiation."
    },
    4: {
        "title": "Session 4 of 7 — Chemical Causes and Toxins",
        "intro": "Moving forward with definitive causes, chemicals and poisons represent a major group of disease agents in veterinary practice.",
        "scenario": "Several sheep grazing near a sprayed agricultural field suddenly show severe muscle tremors, excessive salivation, and respiratory distress after ingesting organophosphate-contaminated grass.",
        "question": "How should this poisoning incident be classified under definitive veterinary causes?",
        "options": [
            "A) Chemical cause / Pesticide toxicity",
            "B) Hereditary genetic mutation",
            "C) Vitamin deficiency"
        ],
        "correct_option": "A",
        "feedback_correct": "Correct! Chemicals, heavy metals, and agricultural toxins (like pesticides, phytotoxins, or zootoxins) act as direct chemical disease agents.",
        "feedback_incorrect": "Good attempt. Contaminated spray represents an external chemical substance poisoning the animal.",
        "term_card": {
            "term": "CHEMICAL CAUSE / TOXIN",
            "meaning": "Harmful chemical substances, acids, alkalis, or biological poisons capable of producing poisoning.",
            "example": "Pesticide toxicity in grazing livestock."
        },
        "recap": "Chemical causes and toxins (including plant, animal, and chemical poisons) directly injure tissues."
    },
    5: {
        "title": "Session 5 of 7 — Biological / Viable Causes",
        "intro": "Let's examine living agents that invade animal bodies and cause infectious diseases. The core question here is: **'WHO caused the disease?'**",
        "scenario": "A dairy goat herd experiences sudden high fever, weakness, and severe pale mucous membranes due to heavy blood-feeding internal parasite infestations in the abomasum.",
        "question": "Which major category of definitive causes do internal parasites belong to?",
        "options": [
            "A) Biological / Viable causes (Parasites)",
            "B) Physical radiation",
            "C) Inorganic acid burns"
        ],
        "correct_option": "A",
        "feedback_correct": "Spot on! Bacteria, viruses, fungi, mycoplasma, rickettsiae, and parasites are all living **Biological / Viable Causes**.",
        "feedback_incorrect": "Good try. Remember that living organisms (bacteria, viruses, parasites) fall under biological causes.",
        "term_card": {
            "term": "BIOLOGICAL / VIABLE CAUSE",
            "meaning": "Disease-causing living organisms or infectious agents (bacteria, viruses, fungi, parasites).",
            "example": "Haemonchus parasite infection in sheep and goats."
        },
        "recap": "Biological causes are living infectious agents like bacteria, viruses, fungi, and parasites."
    },
    6: {
        "title": "Session 6 of 7 — Other Definitive Causes (Nutritional, Immunological & Miscellaneous)",
        "intro": "Besides physical, chemical, and biological agents, diseases can also arise from nutrient imbalances, immune reactions, or medical interventions.",
        "scenario": "A high-yielding dairy cow collapses in sternal recumbency unable to stand right after calving due to a sharp drop in blood calcium levels.",
        "question": "How is milk fever around parturition classified in veterinary pathology?",
        "options": [
            "A) Nutritional / Metabolic imbalance (Calcium deficiency)",
            "B) Viral infection",
            "C) Traumatic bone fracture"
        ],
        "correct_option": "A",
        "feedback_correct": "Correct! Nutritional imbalances (deficiency/excess), immunological reactions (anaphylaxis/hypersensitivity), and miscellaneous causes (iatrogenic or idiosyncrasy) complete our definitive causes.",
        "feedback_incorrect": "Good attempt. This condition stems directly from a metabolic/nutritional mineral imbalance around calving.",
        "term_card": {
            "term": "NUTRITIONAL / IATROGENIC CAUSE",
            "meaning": "Nutritional excess/deficiency, or unintended conditions caused by veterinary intervention (iatrogenic).",
            "example": "Milk fever in dairy cattle due to calcium imbalance."
        },
        "recap": "Nutritional, immunological, and miscellaneous (iatrogenic/idiosyncrasy) factors form the remaining definitive causes."
    },
    7: {
        "title": "Session 7 of 7 — Complete Classification and Application",
        "intro": "Welcome to our final consolidation session! Let's review our complete framework before looking at the Master Etiology Classification Matrix.",
        "scenario": "A cat develops severe facial swelling and respiratory difficulty within minutes after receiving an injection of a standard antibiotic drug.",
        "question": "How should this rapid, severe immune-mediated drug reaction be classified?",
        "options": [
            "A) Immunological cause (Hypersensitivity / Anaphylaxis)",
            "B) Mechanical trauma",
            "C) Vitamin A deficiency"
        ],
        "correct_option": "A",
        "feedback_correct": "Outstanding! You have successfully mastered the disease etiology framework.",
        "feedback_incorrect": "Good try. A rapid, severe systemic immune reaction is classified under immunological hypersensitivity.",
        "term_card": {
            "term": "IMMUNOLOGICAL CAUSE",
            "meaning": "An abnormal or exaggerated immune response causing tissue injury or anaphylaxis.",
            "example": "Anaphylactic reaction to a drug injection."
        },
        "recap": "You can now classify any veterinary disease cause into predisposing or definitive categories."
    }
}

# -----------------------------------------------------------------------------
# 5. HEADER & SIDEBAR PROFILE DISPLAY
# -----------------------------------------------------------------------------
st.title("🐾 General Veterinary Pathology AI Tutor")
st.caption("Module: Etiology and Classification of Disease (BVSc & AH)")

with st.sidebar:
    st.header("👨‍🎓 Student Profile")
    st.write(f"**Name:** {st.session_state.student_name}")
    st.write(f"**Admission No:** {st.session_state.student_id}")
    st.write(f"**Current Session:** {st.session_state.current_session_num} / 7")
    st.write("---")
    
    if st.button("🚪 Logout / Switch Student"):
        st.session_state.student_logged_in = False
        st.session_state.completed_sessions = []
        st.session_state.current_session_num = 1
        st.rerun()

st.markdown(
    f"👋 **Welcome, {st.session_state.student_name}!**\n\n"
    f"*Department of Veterinary Pathology, CVAS, Pookode — BVSc & AH Curriculum*"
)
st.write("---")

# -----------------------------------------------------------------------------
# 6. RENDER COMPLETED SESSIONS EXPANDERS
# -----------------------------------------------------------------------------
for comp in st.session_state.completed_sessions:
    with st.expander(f"✅ Completed: {comp['title']}", expanded=False):
        st.write(comp['scenario'])
        st.success(comp['feedback'])
        term = comp['term_card']
        st.markdown(
            f"📌 **TERM: {term['term']}**\n"
            f"• **Simple meaning:** {term['meaning']}\n"
            f"• **Veterinary example:** {term['example']}"
        )

# -----------------------------------------------------------------------------
# 7. MAIN SESSION INTERACTIVE LOGIC
# -----------------------------------------------------------------------------
current_num = st.session_state.current_session_num

if current_num > 7:
    st.balloons()
    st.success(f"🎉 **CONGRATULATIONS {st.session_state.student_name.upper()}! MODULE COMPLETED SUCCESSFULLY!**")
    st.markdown(f"**Admission No:** `{st.session_state.student_id}`")
    st.markdown("*Department of Veterinary Pathology, CVAS, Pookode*")
    st.write("---")
    
    st.markdown("### 📋 ETIOLOGY OF DISEASE — MASTER CLASSIFICATION MATRIX")
    matrix_md = """
| Etiological Category | Primary Definition | Primary Veterinary Example |
| :--- | :--- | :--- |
| **1. PREDISPOSING CAUSES** | Factors making an animal more susceptible (Heredity, Species, Breed, Age, Sex, Pigmentation) | Hereford cattle prone to cancer eye due to unpigmented eyelids. |
| **2. DEFINITIVE CAUSES** | Actual agents that directly produce disease or tissue injury: | |
| &nbsp;&nbsp;&nbsp;&nbsp;• **Physical** | Mechanical trauma, heat, cold, radiation | Dog injured in a road accident (trauma). |
| &nbsp;&nbsp;&nbsp;&nbsp;• **Chemical & Toxins** | Acids, alkalis, inorganic/organic chemicals, phytotoxins, zootoxins, pesticides | Pesticide toxicity in grazing livestock. |
| &nbsp;&nbsp;&nbsp;&nbsp;• **Biological / Viable** | Bacteria, viruses, fungi, mycoplasma, rickettsiae, parasites | Haemonchus parasite infection in sheep. |
| &nbsp;&nbsp;&nbsp;&nbsp;• **Nutritional** | Deficiencies or excesses of essential nutrients | Milk fever in dairy cattle (calcium imbalance). |
| &nbsp;&nbsp;&nbsp;&nbsp;• **Immunological** | Hypersensitivity and anaphylaxis reactions | Anaphylactic reaction to a drug injection. |
| &nbsp;&nbsp;&nbsp;&nbsp;• **Miscellaneous** | Iatrogenic (intervention-caused) & Idiosyncrasy (unusual drug reaction) | Unintended tissue reaction following treatment. |
"""
    st.markdown(matrix_md)
    st.write("---")
    
    if st.button("🔄 Restart Module", type="primary"):
        st.session_state.current_session_num = 1
        st.session_state.completed_sessions = []
        st.session_state.show_next_button = False
        st.rerun()

elif current_num in CURRICULUM_SESSIONS:
    sess = CURRICULUM_SESSIONS[current_num]
    
    st.subheader(sess["title"])
    st.write(sess["intro"])
    st.info(sess["scenario"])
    st.write(f"**Question:** {sess['question']}")
    
    user_choice = st.radio(
        "Select your answer:", 
        sess["options"], 
        key=f"radio_session_{current_num}"
    )
    
    if not st.session_state.show_next_button:
        if st.button("Submit Answer", type="primary"):
            selected_letter = user_choice.split(")")[0].strip()
            
            if selected_letter == sess["correct_option"]:
                st.session_state.last_feedback = sess["feedback_correct"]
                st.session_state.show_next_button = True
                
                if not any(c['title'] == sess['title'] for c in st.session_state.completed_sessions):
                    st.session_state.completed_sessions.append({
                        "title": sess["title"],
                        "scenario": sess["scenario"],
                        "feedback": sess["feedback_correct"],
                        "term_card": sess["term_card"]
                    })
                st.rerun()
            else:
                st.warning(sess["feedback_incorrect"])
    
    if st.session_state.show_next_button:
        st.success(f"✅ **Correct!** {st.session_state.last_feedback}")
        term = sess["term_card"]
        st.markdown(
            f"📌 **TERM: {term['term']}**\n"
            f"• **Simple meaning:** {term['meaning']}\n"
            f"• **Veterinary example:** {term['example']}"
        )
        st.write("---")
        st.write(f"**Recap:** {sess['recap']}")
        
        next_num = current_num + 1
        btn_label = f"▶ TAP TO CONTINUE TO SESSION {next_num} OF 7" if next_num <= 7 else "🎉 VIEW FINAL MATRIX"
        
        if st.button(btn_label, type="primary", use_container_width=True):
            st.session_state.show_next_button = False
            st.session_state.last_feedback = ""
            st.session_state.current_session_num = next_num
            st.rerun()
