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

if "challenge_score" not in st.session_state:
    st.session_state.challenge_score = 0

if "challenge_submitted" not in st.session_state:
    st.session_state.challenge_submitted = False

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
# 4. JSON CURRICULUM DATABASE (8 SESSIONS)
# -----------------------------------------------------------------------------
CURRICULUM_DATA = {
  "module_title": "General Veterinary Pathology – Etiology and Classification of Disease",
  "module_subtitle": "BVSc & AH | Beginner Module",
  "total_sessions": 8,
  "sessions": [
    {
      "session_number": 1,
      "title": "Session 1 of 8 — Why Does an Animal Become Sick?",
      "intro": "Let's step straight onto the farm and investigate a real clinical mystery.",
      "scenario": "Two dairy calves face identical management. Following a cold rain, Calf B develops a high fever, while Calf A remains healthy.",
      "question": "Both calves faced the same environment, yet only one fell sick. What is the core question a veterinary pathologist must answer first?",
      "options": [
        "A) Why did Calf B become sick while Calf A stayed healthy?",
        "B) What is the normal surgical recovery rate?",
        "C) How do we stain tissue under the microscope?",
        "D) What is the market value of the calf?"
      ],
      "correct_option": "A",
      "feedback_correct": "Spot on! Our central mission in pathology always starts with asking WHY an animal became sick.",
      "feedback_incorrect": "Good attempt. Think about what we are trying to uncover first when investigating a sick animal.",
      "term_card": {
        "term": "ETIOLOGY",
        "meaning": "The study of the cause or origin of disease.",
        "example": "Investigating why respiratory infection broke out in a newly transported batch of piglets."
      },
      "recap": "Etiology asks WHY an animal became sick."
    },
    {
      "session_number": 2,
      "title": "Session 2 of 8 — Predisposing Causes",
      "intro": "Some factors do not directly cause disease on their own, but make certain animals more vulnerable.",
      "scenario": "A herd of mixed cattle is exposed to intense sunlight. White-faced Hereford cattle develop ocular squamous cell carcinoma ('cancer eye'), while fully pigmented Angus cattle in the same field remain unaffected.",
      "question": "Why did only the Hereford cattle develop sun-related lesions under identical sunlight exposure?",
      "options": [
        "A) Their breed trait and lack of pigmentation increased susceptibility",
        "B) They were infected by an acute viral respiratory pathogen",
        "C) They ingested toxic pasture weeds",
        "D) They suffered severe mechanical bone fractures"
      ],
      "correct_option": "A",
      "feedback_correct": "Correct! Lack of pigment and breed traits increase vulnerability without directly causing the injury themselves.",
      "feedback_incorrect": "Good try. Look at the biological difference between the cattle groups facing the same sun.",
      "term_card": {
        "term": "PREDISPOSING CAUSE",
        "meaning": "A factor that makes an animal more susceptible or vulnerable to disease.",
        "example": "Age-related immune decline making older dogs prone to chronic dental disease."
      },
      "recap": "Predisposing causes (like breed, age, sex, and pigmentation) increase susceptibility to disease."
    },
    {
      "session_number": 3,
      "title": "Session 3 of 8 — Definitive Causes: Physical",
      "intro": "While predisposing factors increase vulnerability, **Definitive Causes** are the actual active agents that produce tissue injury.",
      "scenario": "An adult German Shepherd dog is rushed to the clinic after being struck by a motor vehicle, presenting with a compound femoral fracture and soft tissue contusions.",
      "question": "What broad category of definitive disease causes does this vehicular impact represent?",
      "options": [
        "A) Nutritional mineral deficiency",
        "B) Physical cause (Mechanical trauma)",
        "C) Biological bacterial infection",
        "D) Immunological hypersensitivity"
      ],
      "correct_option": "B",
      "feedback_correct": "Excellent! Mechanical trauma, extreme heat, cold, and radiation are direct physical exciting causes.",
      "feedback_incorrect": "Not quite. An external crash force or impact is classified under physical exciting causes.",
      "term_card": {
        "term": "PHYSICAL CAUSE",
        "meaning": "Harmful physical force, extreme temperature, or radiation that injures tissues.",
        "example": "Severe skin burns sustained by livestock during a farm barn fire."
      },
      "recap": "Physical definitive causes include mechanical trauma, heat, cold, and radiation."
    },
    {
      "session_number": 4,
      "title": "Session 4 of 8 — Chemical Causes and Toxins",
      "intro": "Chemical agents and poisons act as major direct disease triggers in veterinary practice.",
      "scenario": "Several sheep grazing near a freshly sprayed agricultural field suddenly exhibit excessive salivation, muscle tremors, and respiratory distress.",
      "question": "How should this poisoning incident be classified under definitive veterinary causes?",
      "options": [
        "A) Chemical cause / Pesticide toxicity",
        "B) Predisposing breed factor",
        "C) Physical radiation injury",
        "D) Hereditary genetic defect"
      ],
      "correct_option": "A",
      "feedback_correct": "Well done! Chemical substances and agricultural toxins act as direct exciting causes of poisoning.",
      "feedback_incorrect": "Good attempt. Exposure to agricultural poisons or chemicals falls under chemical causes.",
      "term_card": {
        "term": "CHEMICAL CAUSE / TOXIN",
        "meaning": "Acids, alkalis, heavy metals, phytotoxins, zootoxins, and pesticides capable of producing poisoning.",
        "example": "Ingestion of neurotoxic snake venom (zootoxin) by a working farm dog."
      },
      "recap": "Chemical causes and toxins act as direct exciting causes that poison and injure tissues."
    },
    {
      "session_number": 5,
      "title": "Session 5 of 8 — Biological Causes: Microbial Agents",
      "intro": "Now let's ask: **WHO** caused the disease? Many infections are driven by microscopic living agents.",
      "scenario": "A group of cattle on a farm develops sudden high fever, systemic shock, and rapid death following exposure to a spore-forming rod bacterium.",
      "question": "Which major category of definitive causes do bacteria, viruses, and fungi belong to?",
      "options": [
        "A) Physical thermal burns",
        "B) Biological / Viable causes",
        "C) Nutritional mineral imbalances",
        "D) Chemical acid corrosion"
      ],
      "correct_option": "B",
      "feedback_correct": "Correct! Living infectious microorganisms are classified as biological or viable causes.",
      "feedback_incorrect": "Good try. Living microscopic pathogens fall under biological/viable causes.",
      "term_card": {
        "term": "BIOLOGICAL / VIABLE CAUSE",
        "meaning": "Disease-causing living organisms including bacteria, viruses, fungi, mycoplasma, and rickettsia.",
        "example": "Foot-and-Mouth Disease virus spreading rapidly through a dairy herd."
      },
      "recap": "Microbial biological causes include bacteria, viruses, fungi, mycoplasma, and rickettsial organisms."
    },
    {
      "session_number": 6,
      "title": "Session 6 of 8 — Biological Causes: Parasites",
      "intro": "Some biological causes are macro-parasites that inhabit internal or external body compartments.",
      "scenario": "A sheep flock in Wayanad experiences severe anemia, weakness, and submandibular edema ('bottle jaw') due to heavy blood-feeding parasite burdens in the abomasum.",
      "question": "Which specific group of biological causes do internal worms like Haemonchus belong to?",
      "options": [
        "A) Chemical pesticide",
        "B) Physical mechanical trauma",
        "C) Biological cause – Helminth (Parasitic worm)",
        "D) Nutritional deficiency"
      ],
      "correct_option": "C",
      "feedback_correct": "Great! Parasitic worms (helminths), protozoa, and arthropods are biological parasite causes.",
      "feedback_incorrect": "Good try. Parasitic worms fall under biological helminth causes.",
      "term_card": {
        "term": "HELMINTH (PARASITIC WORM)",
        "meaning": "A multicellular parasitic worm infecting internal organs or tissues.",
        "example": "Liver fluke (Fasciola hepatica) causing bile duct fibrosis in cattle."
      },
      "recap": "Parasitic causes are biological causes spanning protozoa, helminths, trematodes, cestodes, and arthropods."
    },
    {
      "session_number": 7,
      "title": "Session 7 of 8 — Nutritional, Immunological and Miscellaneous Causes",
      "intro": "To complete our definitive causes, let's examine nutrient imbalances, immune reactions, and medical interventions.",
      "scenario": "A high-producing dairy cow collapses in sternal recumbency unable to stand right after calving, with blood biochemistry revealing severely depressed calcium levels.",
      "question": "How should milk fever around parturition be classified in veterinary pathology?",
      "options": [
        "A) Nutritional / Metabolic cause (Calcium deficiency)",
        "B) Physical trauma injury",
        "C) Biological viral infection",
        "D) Chemical heavy metal poisoning"
      ],
      "correct_option": "A",
      "feedback_correct": "Excellent! Deficiencies or excesses of essential nutrients and minerals are classified as nutritional causes.",
      "feedback_incorrect": "Good attempt. Metabolic mineral imbalances around parturition stem directly from nutrition/metabolism.",
      "term_card": {
        "term": "NUTRITIONAL CAUSE",
        "meaning": "Disease resulting from deficiency, excess, or imbalance of essential nutrients or minerals.",
        "example": "White muscle disease in goat kids due to selenium and vitamin E deficiency."
      },
      "recap": "Nutritional, immunological, and miscellaneous (iatrogenic/idiosyncrasy) factors complete our definitive causes."
    },
    {
      "session_number": 8,
      "title": "Session 8 of 8 — You Are the Pathologist! Final Challenge",
      "intro": "Put your knowledge into practice! Test your ability to classify different veterinary disease scenarios.",
      "scenario": "Review the clinical challenge cases below to complete your pathology training.",
      "question": "Complete the final challenge cases to test your clinical classification skills.",
      "options": [
        "A) Start Final Challenge Evaluation"
      ],
      "correct_option": "A",
      "feedback_correct": "Proceeding to the final pathology challenge.",
      "feedback_incorrect": "Proceeding to the final pathology challenge.",
      "term_card": {
        "term": "CLINICAL ETIOLOGICAL CLASSIFICATION",
        "meaning": "The systematic grouping of disease triggers into predisposing and definitive categories.",
        "example": "Applying pathological frameworks to diagnose field outbreaks in veterinary practice."
      },
      "recap": "Mastery of etiology allows quick, structured reasoning in clinical veterinary diagnostics."
    }
  ]
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
    st.write(f"**Current Session:** {st.session_state.current_session_num} / 8")
    st.write("---")
    
    if st.button("🚪 Logout / Switch Student"):
        st.session_state.student_logged_in = False
        st.session_state.completed_sessions = []
        st.session_state.current_session_num = 1
        st.session_state.challenge_submitted = False
        st.session_state.challenge_score = 0
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
            f"📌 **TERM: {term['term']}**\n\n"
            f"• **Meaning:** {term['meaning']}\n\n"
            f"• **Veterinary example:** {term['example']}"
        )

# -----------------------------------------------------------------------------
# 7. MAIN SESSION INTERACTIVE LOGIC
# -----------------------------------------------------------------------------
current_num = st.session_state.current_session_num

if current_num > 8:
    st.balloons()
    st.success("🎉 **MODULE COMPLETE! CONGRATULATIONS!**")
    st.markdown("🎉 Congratulations! You have completed the Etiology and Classification module. You have moved from asking 'Why did this animal become sick?' to classifying the possible causes like a beginning veterinary pathologist.")
    st.markdown(f"**Admission No:** `{st.session_state.student_id}`")
    st.markdown("*Department of Veterinary Pathology, CVAS, Pookode*")
    st.write("---")
    
    st.markdown("### 📋 ETIOLOGY OF DISEASE — COMPLETE CLASSIFICATION REFERENCE")
    matrix_md = """
| Main Group | Subtypes / Categories | Primary Veterinary Example |
| :--- | :--- | :--- |
| **1. PREDISPOSING CAUSES** | Heredity, Species, Breed, Age, Sex, Colour/Pigmentation | Breed susceptibility & unpigmented eyelids (Hereford cattle). |
| **2. DEFINITIVE CAUSES** | | |
| &nbsp;&nbsp;&nbsp;&nbsp;• **Physical** | Mechanical trauma, Heat, Cold, Radiation | Dog injured in road accident (Mechanical trauma). |
| &nbsp;&nbsp;&nbsp;&nbsp;• **Chemical & Toxins** | Acids, Alkalis, Heavy Metals, Phytotoxins, Zootoxins, Pesticides | Pesticide poisoning / heavy metal toxicity. |
| &nbsp;&nbsp;&nbsp;&nbsp;• **Biological / Viable** | Bacteria, Viruses, Fungi, Mycoplasma, Rickettsial, Protozoa, Helminths, Trematodes, Cestodes, Arthropods | Anthrax (bacteria), FMD (virus), Haemonchosis (helminth). |
| &nbsp;&nbsp;&nbsp;&nbsp;• **Nutritional** | Deficiency, Excess | Milk fever in cattle (Calcium deficiency). |
| &nbsp;&nbsp;&nbsp;&nbsp;• **Immunological** | Hypersensitivity, Anaphylaxis | Allergic reaction / anaphylactic shock from drug. |
| &nbsp;&nbsp;&nbsp;&nbsp;• **Miscellaneous** | Iatrogenic, Idiosyncrasy | Unintended condition from veterinary intervention. |
"""
    st.markdown(matrix_md)
    st.write("---")
    st.markdown("**Take-Home Messages:**")
    st.markdown("• ETIOLOGY asks: *WHY did the animal become sick?*")
    st.markdown("• PREDISPOSING causes make an animal more susceptible.")
    st.markdown("• DEFINITIVE causes are the actual agents or factors producing disease or injury.")
    st.write("---")
    
    if st.button("🔄 Restart Module", type="primary"):
        st.session_state.current_session_num = 1
        st.session_state.completed_sessions = []
        st.session_state.show_next_button = False
        st.session_state.challenge_submitted = False
        st.session_state.challenge_score = 0
        st.rerun()

else:
    sess = next((s for s in CURRICULUM_DATA["sessions"] if s["session_number"] == current_num), None)
    
    if sess:
        st.subheader(sess["title"])
        st.write(sess["intro"])
        
        if current_num == 8:
            st.info(sess["scenario"])
            st.markdown("### 🏆 Final Pathology Challenge Questions")
            
            challenge_qs = [
                {"q": "A sheep develops systemic illness after consuming toxic ornamental shrubs on pasture. Which category?", "opts": ["A) Physical trauma", "B) Chemical / phytotoxin", "C) Hereditary defect", "D) Age-related change"], "ans": "B"},
                {"q": "A cattle herd experiences an outbreak of fasciolosis due to liver fluke infestation. Which category?", "opts": ["A) Biological → Trematode", "B) Physical → Cold", "C) Nutritional → Excess", "D) Predisposing → Sex"], "ans": "A"},
                {"q": "An aged German Shepherd develops degenerative joint changes due to natural senescence. Which predisposing category applies?", "opts": ["A) Definitive physical", "B) Definitive chemical", "C) Predisposing → Age", "D) Definitive biological"], "ans": "C"},
                {"q": "A dairy cow develops milk fever associated with low blood calcium after calving. Which category?", "opts": ["A) Biological", "B) Nutritional", "C) Physical", "D) Chemical"], "ans": "B"},
                {"q": "A dog develops severe tissue necrosis at an accidental subcutaneous drug leakage site. Which category?", "opts": ["A) Iatrogenic / Miscellaneous", "B) Viral infection", "C) Mechanical trauma", "D) Genetic mutation"], "ans": "A"}
            ]
            
            with st.form("final_challenge_form"):
                user_ans = []
                for idx, item in enumerate(challenge_qs):
                    ans = st.radio(f"**Q{idx+1}:** {item['q']}", item['opts'], key=f"cq_{idx}")
                    user_ans.append(ans)
                
                c_submit = st.form_submit_button("Submit Challenge Answers", type="primary")
                if c_submit:
                    score = 0
                    for idx, item in enumerate(challenge_qs):
                        selected = user_ans[idx].split(")")[0].strip()
                        if selected == item['ans']:
                            score += 1
                    st.session_state.challenge_score = score
                    st.session_state.challenge_submitted = True
                    st.rerun()
            
            if st.session_state.challenge_submitted:
                st.success(f"🎯 **Challenge Score: {st.session_state.challenge_score} / 5**")
                if st.session_state.challenge_score == 5:
                    st.balloons()
                    st.markdown("🌟 **Flawless performance! You are fully ready for clinical veterinary pathology!**")
                
                if not any(c['title'] == sess['title'] for c in st.session_state.completed_sessions):
                    st.session_state.completed_sessions.append({
                        "title": sess["title"],
                        "scenario": sess["scenario"],
                        "feedback": f"Completed challenge with score {st.session_state.challenge_score}/5",
                        "term_card": sess["term_card"]
                    })
                
                if st.button("🎉 VIEW FINAL MATRIX & COMPLETE MODULE", type="primary"):
                    st.session_state.current_session_num = 9
                    st.rerun()
        else:
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
                    f"📌 **TERM: {term['term']}**\n\n"
                    f"• **Meaning:** {term['meaning']}\n\n"
                    f"• **Veterinary example:** {term['example']}"
                )
                st.write("---")
                st.write(f"**Recap:** {sess['recap']}")
                
                next_num = current_num + 1
                btn_label = f"▶ CONTINUE TO SESSION {next_num}" if next_num <= 8 else "🎉 VIEW FINAL MATRIX"
                
                if st.button(btn_label, type="primary", use_container_width=True):
                    st.session_state.show_next_button = False
                    st.session_state.last_feedback = ""
                    st.session_state.current_session_num = next_num
                    st.rerun()
