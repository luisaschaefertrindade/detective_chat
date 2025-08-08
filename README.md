# Solving Mysteries!

An interactive Streamlit app where children aged 6-12 can solve fun mysteries by asking questions and getting hints!

## Features

- Age-appropriate mysteries with hints
- Interactive question-answer gameplay
- Fun UI with detective-themed messages and emojis
- AI-powered hinting and solution verification

## How to run it
https://solvingmysteries.streamlit.app/

## Usage
Start a new mystery based on your age.
Ask yes/no questions to solve the case.
Use hints if stuck.
Have fun being a detective!

# Project Techniques
This project combines **Streamlit UI design**, **AI-powered reasoning**, and **interactive game logic** to create a fun mystery-solving experience for kids aged 6–12. 
Key techniques include:

## Custom UI Styling
- Inline CSS injection to override default Streamlit styles, giving a playful, colorful interface.
- Custom message bubbles for player (🕵️), bot (🤖), and system messages, with different colors and shadows for a chat-like experience.
- Google Fonts integration for a kid-friendly typeface (Fredoka One).
- Gradient backgrounds and thematic colors for an immersive feel.

## AI-Powered Gameplay
LangChain ConversationChain with ChatGoogleGenerativeAI (Gemini) for real-time reasoning.
Custom PromptTemplate that:
- Injects the current mystery and solution into the model’s context.
- Restricts answers to "Yes", "No", or "Irrelevant", keeping gameplay concise and age-appropriate.
- Partial variables in the prompt to dynamically set mystery content from JSON.
ConversationBufferMemory to maintain context between questions.

## Mystery Logic & Answer Checking
Dynamic difficulty: Mysteries are grouped into age buckets (6–7, 8–9, 10–12).

Randomized mystery selection without repetition using used_titles tracking.
Flexible answer detection with:
- String similarity matching (difflib).
- Keyword overlap ratio for partial matches.
- Case and punctuation-insensitive comparisons.

## JSON Mystery Database
Mysteries, solutions, hints, and acceptable answer variants are stored in a mystery_bank.json file.
Easy to expand by simply adding new entries per age group.

## Streamlit State Management
Uses st.session_state to persist:
- Player name and age
- Active mystery data
- Question count and used titles
- Whether the solution is revealed
- Supports replay with "Play another mystery" button while keeping session history isolated per round.

## Player Interaction Features
- "I'm stuck" button to reveal a hint.
- "I give up" button with a confirmation step before showing the solution.
- Question counter to track performance.
