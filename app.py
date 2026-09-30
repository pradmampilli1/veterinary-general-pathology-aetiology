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
      "intro": "Welcome to **General Veterinary Pathology**! Let's step straight onto the farm and investigate a real case.",
      "scenario": "Two dairy calves face identical management. Following a cold rain, Calf B develops a high fever, while Calf A remains healthy.",
      "question": "Both calves faced the same environment, yet only one fell sick. What is the most important question a veterinary pathologist must answer first?",
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
        "example": "Determining why Calf B developed a fever after environmental exposure."
      },
      "recap": "Etiology asks WHY an animal became sick."
    },
    {
      "session_number": 2,
      "title": "Session 2 of 8 — Predisposing Causes",
      "intro": "Sometimes two animals face a similar situation, but one is more likely to become diseased. Why?",
      "scenario": "Two cattle are exposed to strong sunlight. A white-faced Hereford develops a sun-related lesion around the eye, while a heavily pigmented animal does not.",
      "question": "Which factor could make one animal more susceptible?",
      "options": [
        "A) Breed and pigmentation",
        "B) A bacterial culture",
        "C) A surgical operation",
        "D) A vitamin injection"
      ],
      "correct_option": "A",
      "feedback_correct": "Certain characteristics can make an animal more susceptible to disease. These are called predisposing causes.",
      "feedback_incorrect": "Look at the difference between the animals. Their breed and pigmentation can influence susceptibility.",
      "term_card": {
        "term": "PREDISPOSING CAUSE",
        "meaning": "A factor that makes an animal more likely or susceptible to disease.",
        "example": "Breed, age, sex, heredity, species, or pigmentation may increase susceptibility."
      },
      "recap": "Predisposing causes make an animal more susceptible to disease."
    },
    {
      "session_number": 3,
      "title": "Session 3 of 8 — Definitive Causes: Physical",
      "intro": "Now let's look at factors that can directly produce disease or injury.",
      "scenario": "A dog is hit by a vehicle and develops a fractured limb.",
      "question": "What type of cause directly produced the dog's injury?",
      "options": [
        "A) Nutritional cause",
        "B) Physical cause",
        "C) Biological cause",
        "D) Hereditary cause"
      ],
      "correct_option": "B",
      "feedback_correct": "A mechanical force from the accident directly produced the injury.",
      "feedback_incorrect": "Think about what physically acted on the dog. It was a mechanical force.",
      "term_card": {
        "term": "PHYSICAL CAUSE",
        "meaning": "A harmful physical force, energy, temperature or radiation that can produce disease or injury.",
        "example": "Mechanical trauma in a dog after a road accident."
      },
      "recap": "Physical causes include mechanical trauma, heat, cold and radiation."
    },
    {
      "session_number": 4,
      "title": "Session 4 of 8 — Chemical Causes and Toxins",
      "intro": "Animals may also become diseased after exposure to harmful chemicals or toxic substances.",
      "scenario": "Several sheep become ill after grazing in an area contaminated with an agricultural pesticide.",
      "question": "How should this cause be classified?",
      "options": [
        "A) Hereditary cause",
        "B) Physical cause",
        "C) Chemical / toxic cause",
        "D) Age-related cause"
      ],
      "correct_option": "C",
      "feedback_correct": "A pesticide is a chemical substance that can produce toxicity.",
      "feedback_incorrect": "Look at the clue: the sheep were exposed to a pesticide. That points to a chemical or toxic cause.",
      "term_card": {
        "term": "CHEMICAL CAUSE",
        "meaning": "A harmful chemical substance capable of producing disease or injury.",
        "example": "Pesticide toxicity in sheep."
      },
      "recap": "Chemical causes and toxins can directly produce disease."
    },
    {
      "session_number": 5,
      "title": "Session 5 of 8 — Biological Causes: Microbial Agents",
      "intro": "Now ask: WHO caused the disease? Many diseases are caused by biological agents.",
      "scenario": "A group of cattle develops fever and characteristic disease after exposure to an infectious agent.",
      "question": "Which of the following is a biological cause of disease?",
      "options": [
        "A) Bacterium",
        "B) Heat",
        "C) Calcium deficiency",
        "D) Mechanical trauma"
      ],
      "correct_option": "A",
      "feedback_correct": "Bacteria are biological agents capable of causing infectious disease.",
      "feedback_incorrect": "Think about which option is an organism rather than a physical or nutritional factor.",
      "term_card": {
        "term": "BIOLOGICAL / VIABLE CAUSE",
        "meaning": "A disease-causing organism or infectious biological agent.",
        "example": "Bacteria causing anthrax in cattle."
      },
      "recap": "Microbial biological causes include bacteria, viruses, fungi, mycoplasma and rickettsial organisms."
    },
    {
      "session_number": 6,
      "title": "Session 6 of 8 — Biological Causes: Parasites",
      "intro": "Some biological causes are parasites. Let's see how they fit into the classification.",
      "scenario": "A group of goats becomes weak and pale because of a heavy Haemonchus infection.",
      "question": "Haemonchus belongs to which broad group?",
      "options": [
        "A) Chemical cause",
        "B) Physical cause",
        "C) Biological cause",
        "D) Predisposing cause"
      ],
      "correct_option": "C",
      "feedback_correct": "Haemonchus is a parasitic organism, so it is a biological cause.",
      "feedback_incorrect": "Haemonchus is a parasite. Parasites belong under biological causes.",
      "term_card": {
        "term": "HELMINTH",
        "meaning": "A parasitic worm.",
        "example": "Haemonchus in sheep and goats."
      },
      "recap": "Parasitic causes are biological causes and include protozoa, helminths and arthropods."
    },
    {
      "session_number": 7,
      "title": "Session 7 of 8 — Nutritional, Immunological and Miscellaneous Causes",
      "intro": "A few important causes remain. Let's identify them from veterinary situations.",
      "scenario": "A high-producing dairy cow becomes weak and unable to stand shortly after calving. Blood calcium concentration is very low.",
      "question": "Which type of cause should you consider?",
      "options": [
        "A) Biological cause",
        "B) Physical cause",
        "C) Nutritional cause",
        "D) Hereditary cause"
      ],
      "correct_option": "C",
      "feedback_correct": "Low calcium is a nutritional imbalance associated with milk fever around calving.",
      "feedback_incorrect": "Look at the clue: the cow has very low calcium. Calcium is a nutrient.",
      "term_card": {
        "term": "NUTRITIONAL CAUSE",
        "meaning": "Disease caused by deficiency, excess or imbalance of a nutrient.",
        "example": "Milk fever associated with low calcium in a dairy cow."
      },
      "recap": "The remaining definitive causes include nutritional, immunological and miscellaneous causes."
    },
    {
      "session_number": 8,
      "title": "Session 8 of 8 — You Are the Pathologist!",
      "intro": "This is your final challenge. You now have to classify the cause from short veterinary situations.",
      "scenario": "A dog develops injury after being hit by a vehicle.",
      "question": "How should the cause be classified?",
      "options": [
        "A) Definitive → Physical → Mechanical trauma",
        "B) Predisposing → Breed",
        "C) Definitive → Nutritional → Deficiency",
        "D) Definitive → Biological → Virus"
      ],
      "correct_option": "A",
      "feedback_correct": "You correctly connected the veterinary situation with the complete classification.",
      "feedback_incorrect": "Think about what directly acted on the dog. It was a physical mechanical force.",
      "term_card": {
        "term": "DEFINITIVE CAUSE",
        "meaning": "The actual agent or factor that directly produces disease or injury.",
        "example": "Mechanical trauma from a road accident."
      },
      "recap": "Think: Predisposing factors increase susceptibility; definitive causes actually produce disease or injury."
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
            st.markdown("**SESSION COMPLETE**")
            
            next_num = current_num + 1
            btn_label = f"▶ TAP TO CONTINUE TO SESSION {next_num} OF 8" if next_num <= 8 else "🎉 VIEW FINAL MATRIX"
            
            if st.button(btn_label, type="primary", use_container_width=True):
                st.session_state.show_next_button = False
                st.session_state.last_feedback = ""
                st.session_state.current_session_num = next_num
                st.rerun()
        
        # Special rendering for Session 8 challenge questions if desired
        if current_num == 8 and st.session_state.show_next_button:
            st.write("---")
            st.markdown("### 🏆 Final Pathology Challenge Questions")
            
            challenge_qs = [
                {"q": "A sheep develops disease after eating a poisonous plant. Which category?", "opts": ["A) Physical", "B) Chemical / toxic", "C) Hereditary", "D) Age-related"], "ans": "B"},
                {"q": "A cow develops fasciolosis due to Fasciola infection. Which category?", "opts": ["A) Biological → Trematode", "B) Physical → Heat", "C) Nutritional → Deficiency", "D) Predisposing → Breed"], "ans": "A"},
                {"q": "A particular breed of dog is more susceptible to a disease. Which category?", "opts": ["A) Definitive → Physical", "B) Definitive → Chemical", "C) Predisposing → Breed", "D) Definitive → Biological"], "ans": "C"},
                {"q": "A cow develops milk fever associated with low blood calcium after calving. Which category?", "opts": ["A) Biological", "B) Nutritional", "C) Physical", "D) Chemical"], "ans": "B"},
                {"q": "An animal develops an unintended condition following veterinary intervention. Which category?", "opts": ["A) Iatrogenic", "B) Viral", "C) Physical", "D) Hereditary"], "ans": "A"}
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
                
                if st.button("🎉 VIEW FINAL MATRIX & COMPLETE MODULE", type="primary"):
                    st.session_state.current_session_num = 9
                    st.rerun()
