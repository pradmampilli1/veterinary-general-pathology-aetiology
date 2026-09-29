def render_custom_markdown(text):
    """Cleans marker strings and forces every MCQ option onto its own line."""
    clean_text = text.replace("[SESSION_COMPLETE]", "").strip()
    
    # Force B) and C) onto separate lines whenever they appear preceded by text or a space
    clean_text = re.sub(r'\s+([B-C]\))', r'\n\n\1', clean_text)
    
    st.markdown(clean_text)
