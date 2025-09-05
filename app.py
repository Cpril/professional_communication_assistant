import os
import streamlit as st
import re
import difflib
import google.generativeai as genai

# -----------------------------
# Setup Gemini client
# -----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("⚠️ Gemini API key not found. Please set GEMINI_API_KEY as an environment variable.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# -----------------------------
# Streamlit page setup
# -----------------------------
st.set_page_config(page_title="Professional Communication Assistant", layout="wide")
st.title("💬 Professional Communication Assistant")

# -----------------------------
# Style selection
# -----------------------------
styles = ["Professional", "Friendly", "Light-hearted", "Concise", "Empathetic"]
style_choice = st.selectbox("Choose polishing style:", styles)

# -----------------------------
# Layout: two columns
# -----------------------------
col1, col2 = st.columns(2)
height = 400

with col1:
    user_input = st.text_area("✍️ Your Draft", height=height)

# -----------------------------
# Highlight function
# -----------------------------
def highlight_sentences(polished_sentences, categories):
    """Apply color highlights to polished sentences based on categories dict"""
    highlights = {
        "grammar": "background-color:#ffcccc;",    # red
        "spelling": "background-color:#cce5ff;",   # blue
        "tone": "background-color:#fff3cd;",       # yellow
        "formatting": "background-color:#d5f5e3;", # green
        "other": "background-color:#e8d4f8;",      # purple
    }

    output = []
    for sent in polished_sentences:
        category = categories.get(sent.strip())
        if category:
            style = highlights.get(category, "")
            sent = f"<span style='{style}'>{sent}</span>"
        output.append(sent)
    return " ".join(output)

# -----------------------------
# Sentence splitting helper
# -----------------------------
def split_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text.strip())

# -----------------------------
# Gemini wrapper
# -----------------------------
def gemini_generate(prompt, max_output_tokens=600):
    response = model.generate_content(
        prompt,
        generation_config={"max_output_tokens": max_output_tokens}
    )
    return response.text.strip()

# -----------------------------
# Polishing workflow
# -----------------------------
if st.button("Polish"):
    if user_input.strip() == "":
        st.warning("Please enter some text first.")
    else:
        with st.spinner("Polishing your text..."):

            # Step 1: Polished version
            prompt = f"""

Instructions:
1. Rewrite the draft in the style the user selected ({style_choice}).
2. Only change or polish sentences from the original draft that have grammar, spelling, tone, formatting, or other issues.
3. Wrap the entire original sentence that was changed with:
   <grammar>...</grammar>, <spelling>...</spelling>, <tone>...</tone>, <formatting>...</formatting>, or <other>...</other> as appropriate.
4. Do NOT add new sentences, repeat sentences, extra commentary, or explanations.
Draft:
{user_input}
"""
            polished_text = gemini_generate(prompt, max_output_tokens=600)

            # Step 2: Diff sentences
            orig_sentences = split_sentences(user_input)
            polished_sentences = split_sentences(polished_text)

            matcher = difflib.SequenceMatcher(None, orig_sentences, polished_sentences)
            changed_sentences = []
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag != "equal":
                    changed_sentences.extend(polished_sentences[j1:j2])

            # Step 3: Classify each changed sentence
            categories = {}
            for sent in changed_sentences:
                classify_prompt = f"""
Classify the type of fix made to this sentence compared to the original draft.

Sentence: "{sent}"

Categories: grammar, spelling, tone, formatting, other
Return only one category name.
"""
                category = gemini_generate(classify_prompt, max_output_tokens=5).lower()
                if category not in ["grammar", "spelling", "tone", "formatting", "other"]:
                    category = "other"
                categories[sent.strip()] = category

            # Step 4: Highlight polished sentences
            polished_html = highlight_sentences(polished_sentences, categories)

        # -----------------------------
        # Right panel: polished version
        # -----------------------------
        with col2:
            box_html = f"""
            <div style="
                padding:15px;
                border-radius:5px;
                min-height:{height}px;
                white-space: pre-wrap;
                font-family: 'Courier New', monospace;
                color:black;
            ">
                {polished_html}
            </div>
            """
            st.markdown(box_html, unsafe_allow_html=True)

        # -----------------------------
        # Legend
        # -----------------------------
        st.markdown("---")
        st.markdown(
            "### 🔑 Highlight Legend\n"
            "- <span style='background-color:#ffcccc;'>Red</span>: Grammar fixes  \n"
            "- <span style='background-color:#cce5ff;'>Blue</span>: Spelling fixes  \n"
            "- <span style='background-color:#fff3cd;'>Yellow</span>: Tone/style adjustments  \n"
            "- <span style='background-color:#d5f5e3;'>Green</span>: Formatting fixes  \n"
            "- <span style='background-color:#e8d4f8;'>Purple</span>: Other fixes",
            unsafe_allow_html=True
        )
