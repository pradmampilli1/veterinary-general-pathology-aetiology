# Replace the initial prompt string in app.py with this tighter version:
if not st.session_state.chat_history and not st.session_state.completed_bystander_sessions:
    init_prompt = (
        f"Begin Session 1 of 7 now. In your very first response, perform BOTH of these steps in one single turn:\n"
        f"1. Greet the student: 'Welcome, {st.session_state.student_name}! Department of Veterinary Pathology, CVAS, Pookode welcomes you to Session 1.'\n"
        f"2. Immediately present a short scenario about two calves at CVAS Pookode where one becomes sick and one stays healthy, and ask ONE simple multiple-choice question (MCQ) to make the student think about why.\n"
        f"Do NOT stop after the greeting alone. Do NOT introduce technical terms like 'Etiology' yet."
    )
    st.session_state.chat_history.append({"role": "user", "text": init_prompt})
