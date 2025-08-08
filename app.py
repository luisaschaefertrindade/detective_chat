# ui/app.py

import streamlit as st
import json
import random
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import difflib
import re

# Load Gemini API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def inject_css():
    st.markdown(
        """
        <style>
        /* Page background & font */
        @import url('https://fonts.googleapis.com/css2?family=Fredoka+One&display=swap');
        body, .css-18e3th9 {
            background: linear-gradient(135deg, #FFF8DC, #E0F7FA);
            font-family: 'Fredoka One', cursive;
            color: #1A237E;
        }

        /* Mystery title header */
        .mystery-title {
            font-size: 2.8rem;
            font-weight: 900;
            margin-bottom: 40px;
            text-align: center;
            color: #4A148C;
            text-shadow: 2px 2px 4px #B39DDB;
        }

        /* Each message bubble */
        .message {
            padding: 10px 15px;
            margin-bottom: 10px;
            border-radius: 20px;
            box-shadow: 2px 2px 6px #ccc;
            max-width: 70%;
            text-align: center;
            word-wrap: break-word;
            white-space: pre-wrap;
            font-size: 1.1rem;
        }

        /* Player message style */
        .player-msg {
            background: #CE93D8;
            color: white;
            text-align: left;
        }

        /* Bot message style */
        .bot-msg {
            background: #9575CD;
            color: white;
            text-align: left;
            margin-left: auto;
        }

        /* Other messages style (e.g. intro) */
        .other-msg {
            background: #FFD54F;
            color: #4A148C;
            margin-left: 100px;
            font-weight: bold;
            border-radius: 15px;
            box-shadow: 2px 2px 6px #C6A700;
        }

        /* Chat input and buttons container */
        .input-buttons-container {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 5px;
            margin-bottom: 25px;
        }

        /* Style buttons */
        .stButton > button {
            background-color: #FF6F61;
            border-radius: 25px;
            color: white;
            font-weight: bold;
            box-shadow: 0 4px 6px #E57373;
            padding: 10px 20px;
            font-size: 1rem;
            cursor: pointer;
            transition: background-color 0.3s ease;
            min-width: 140px;
        }
        .stButton > button:hover {
            background-color: #E64A19;
        }

        /* Fix Streamlit chat input margin */
        .css-1aumxhk {
            margin-bottom: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


inject_css()

# --- SETUP ---
st.set_page_config(page_title="Solving Mysteries!", page_icon="🕵️")

if "name" not in st.session_state:
    st.session_state.name = None
if "age" not in st.session_state:
    st.session_state.age = None
if "used_titles" not in st.session_state:
    st.session_state.used_titles = []
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "solution_revealed" not in st.session_state:
    st.session_state.solution_revealed = False

# --- Gemini Chat Setup ---
def get_chain():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        api_key=GEMINI_API_KEY
    )

    prompt = PromptTemplate(
        input_variables=["history", "input"],
        template="""
You are a mystery-solving assistant for children aged 6–12.
You are helping them solve a short, age-appropriate mystery.
You know the exact mystery and its correct solution.

Mystery: {mystery_text}
Solution: {solution_text}

## How you must work:
1. **Think through the mystery first** 
    - use the conversation history and question to decide if the information could directly or indirectly help identify the solution {solution_text}.
    - think logically: 
        - Does the input make sense in the context of the mystery {mystery_text} and its known solution {solution_text}? 
            - If not, it is **irrelevant**. If it does make sense, it could be a **yes** or **no** answer. 
            - A question should be answered with **yes** if it is relevant and correct towards a solution. 
            - A question should be answered with **no** if it is relevant but incorrect towards a solution.
        - Example 1:
            - Mystery: "Emma left her cupcake on the table, but when she came back, only the wrapper was there. What happened?"
            - Solution: "Her dog ate the cupcake while she was gone."
            - Possible questions:
                - "Does she have siblings" -> The detective is trying to assess if someone from the family did it; it's **irrelevant** since it wasn't a sibling who did it.
                - "Did someone eat it" -> The detective is getting closer, someone did eat it, even the solution being an animal; it's **yes**.
                - "Does the family have a pet" -> The detective is trying to assess if it was a pet, getting in the right track; it's **yes**.
                - "The dog ate her cupcake" -> The detective is right!
        - Example 2:
            - Mystery: "The picture in the hallway was upside down, but no one admitted touching it. Why?"
            - Solution: "The cat knocked it over and it was rehung the wrong way."
            - Possible questions:
                - "Was it in a home" -> The detective is trying to assess the environment. Since a cat did it and a cat lives in a home, it's **yes**.
                - "Does a pet live in the home" -> The detective is getting closer as a cat is a pet; it's **yes**.
                - "Was the picture hung upside down by mistake" -> The detective is trying to assess if someone did it on purpose; it's relevant since it shows a person wasn't the culprit; it's **no**.
                - "The family cat knocked the picture and someone hung it wrong" -> The detective is right!
2. You may ONLY respond with exactly one of these three words: "Yes", "No", or "Irrelevant".
3. Do NOT add any other words, punctuation, emojis, or explanations.
4. If the question is not answerable with Yes/No, reply: "Only Yes or No questions!"
5. A question is **relevant** if:
   - It directly points toward the cause, method, or reason behind the mystery, OR
   - It could lead to clues that help uncover the cause (even indirectly, like asking if there’s a pet when a pet could cause the event).
6. A question is **irrelevant** if it has no realistic connection to solving the mystery.
7. Never reveal hints or the solution unless the player explicitly asks for them through the game’s buttons.

Conversation so far:
{history}

Player’s question:
{input}

Your answer (exactly "Yes", "No", or "Irrelevant"):
""",
    partial_variables={
        "mystery_text": st.session_state.current_mystery["mystery"],
        "solution_text": st.session_state.current_mystery["solution"]
    }
    )

    memory = ConversationBufferMemory(ai_prefix="Bot")
    return ConversationChain(llm=llm, prompt=prompt, memory=memory)


def is_solution_guess(user_input, solution_variants):
    guess = user_input.strip().lower()

    stopwords = {"the", "is", "at", "a", "an", "and", "to", "of", "in", "on", "for", "with", "it"}

    def match_single_solution(guess, answer):
        answer = answer.strip().lower()

        similarity = difflib.SequenceMatcher(None, guess, answer).ratio()
        if similarity > 0.65:
            return True

        answer_clean = re.sub(r"[^\w\s]", "", answer)
        guess_clean = re.sub(r"[^\w\s]", "", guess)

        answer_keywords = {w for w in answer_clean.split() if w not in stopwords}
        guess_keywords = {w for w in guess_clean.split() if w not in stopwords}

        if not answer_keywords:
            return False

        overlap = answer_keywords & guess_keywords
        overlap_ratio = len(overlap) / len(answer_keywords)

        return overlap_ratio >= 0.6

    for variant in solution_variants:
        if match_single_solution(guess, variant):
            return True

    return False


def get_age_bucket(age):
    if age < 8:
        return "6-7"
    elif age < 10:
        return "8-9"
    else:
        return "10-12"


def start_new_game(age):
    age_bucket = get_age_bucket(age)
    with open("mystery_bank.json", "r", encoding="utf-8") as f:
        bank = json.load(f)

    all_mysteries = bank[age_bucket]
    unused = [m for m in all_mysteries if m["title"] not in st.session_state.used_titles]

    if not unused:
        return None

    mystery = random.choice(unused)
    st.session_state.used_titles.append(mystery["title"])
    st.session_state.current_mystery = mystery
    st.session_state.question_count = 0
    return mystery["mystery"]


# --- APP FLOW ---
# STEP 1: Name & Age Setup
if not st.session_state.name or not st.session_state.age:
    st.title("🕵️ Welcome to Solving Mysteries!")
    with st.form("setup_form"):
        name = st.text_input("Detective, what's your name?")
        age = st.number_input("How old are you?", min_value=6, max_value=12, step=1)
        submitted = st.form_submit_button("Start the investigation!")
        if submitted and name and age:
            st.session_state.name = name
            st.session_state.age = int(age)
            st.rerun()

# STEP 2: Game Screen
else:
    # 1. Header (big styled title)
    st.markdown(
        f'<h1 class="mystery-title">Solving Mysteries<br>🕵️ Detective: {st.session_state.name}</h1>',
        unsafe_allow_html=True
    )

    # Initialize messages and chain if needed
    if "messages" not in st.session_state:
        mystery = start_new_game(st.session_state.age)
        if mystery:
            # 2. Mystery description
            st.session_state.messages = [f"Your case is:\n\n**{mystery}**"]
        else:
            st.session_state.messages = []

    if "chain" not in st.session_state:
        st.session_state.chain = get_chain()
    

    # 3. Rendering messages
    for msg in st.session_state.messages:
        if msg.startswith("🕵️") and st.session_state.name in msg:
            # clean_msg = msg.split(": ", 1)[-1]
            st.markdown(f'<div class="message player-msg">{msg}</div>', unsafe_allow_html=True)
        elif msg.startswith("🤖"):
            # clean_msg = msg.replace("🤖 ", "", 1)
            st.markdown(f'<div class="message bot-msg">{msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="message other-msg">{msg}</div>', unsafe_allow_html=True)

    

    # 4. Buttons container - centered & spaced nicely above input box
    st.markdown('<div class="input-buttons-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("I'm stuck"):
            st.session_state.messages.append("💡 Tip: " + st.session_state.current_mystery["hint"])
            st.rerun()
    with col2:
        if st.button("I give up"):
            if st.session_state.solution_revealed:
                st.session_state.messages.append(f"✅ Solution: {st.session_state.current_mystery['solution']}")
            else:
                st.session_state.solution_revealed = True
                st.session_state.messages.append("Are you sure? Click again to see the solution.")
            st.rerun()
    with col3:
        if st.button("Play another mystery"):
            new_mystery = start_new_game(st.session_state.age)
            if new_mystery:
                st.session_state.messages = [f"Your case is:\n\n**{new_mystery}**"]
                st.session_state.solution_revealed = False
            else:
                st.session_state.messages = [f"🎉 Congratulations Detective {st.session_state.name}, you've solved all mysteries!"]
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 5. Chat input box at the bottom
    user_input = st.chat_input("Ask your question...")

    if user_input:
        if user_input.lower() not in ["hint", "i give up", "i'm stuck"]:
            st.session_state.question_count += 1

        # Check if player guessed the mystery solution
        if is_solution_guess(user_input, st.session_state.current_mystery['solution_variants']):
            st.session_state.messages.append(f"🕵️ {st.session_state.name}: {user_input}")
            st.session_state.messages.append("🎉 The mystery was solved! Great job, Detective!")
            st.session_state.solution_revealed = True
            st.session_state.messages.append("👉 Click 'Play another mystery' to start a new case.")
        else:
            st.session_state.messages.append(f"🕵️ {st.session_state.name}: {user_input}")

            mystery_context = st.session_state.current_mystery["mystery"]
            history_text = "\n".join(st.session_state.messages)

            response = st.session_state.chain.run(
                history=history_text,
                input=f"Mystery: {mystery_context}\nQuestion: {user_input}"
            )
            st.session_state.messages.append(f"🤖 {response.strip()}")

        st.rerun()

    # Show stats if solution revealed
    if st.session_state.solution_revealed:
        st.markdown(f"📊 You solved this mystery with **{st.session_state.question_count}** question(s).")