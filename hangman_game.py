# app.py
import os
import re
import requests
import streamlit as st
import random
from wordfreq import zipf_frequency


# configure streamlit page settings
st.set_page_config(page_title="Hangman", layout="centered")

# api endpoint for fetching random words
api = "https://random-word-api.herokuapp.com/word"

# maximum number of allowed wrong attempts
max_tries = 6

# directory containing hangman stage images
image_dir = "images"  # folder with hangman images

# map remaining attempts to image filenames
image_map = {
    6: "hangman0.png",
    5: "hangman1.png",
    4: "hangman2.png",
    3: "hangman3.png",
    2: "hangman4.png",
    1: "hangman5.png",
    0: "hangman6.png",
}

def art_img(tries):
    # select image based on remaining attempts
    # fallback to initial image if key is missing
    file_name = image_map.get(tries, "hangman0.png")
    return os.path.join(image_dir, file_name)


@st.cache_data(ttl=600) # if this function is called again with the same inputs, don't run it again and reuse previous results( cache expires after 600 seconds (10 minutes))
def fetch_common_candidates(target_len: int, timeout: int = 5, min_zipf: float = 3.5):
    # fetch multiple words from api, filter common ones, and cache the result
    r = requests.get(
        f"{api}?number=100&length={max(3, int(target_len))}", # fetch 100 words of at least length 3
        timeout=timeout
    )
    # raise exception for http errors
    r.raise_for_status()
    # parse api response (expected to be a list)
    data = r.json()

    common_words = []
    for item in data if isinstance(data, list) else []:
        # remove non-alphabetic characters and convert to lowercase
        w = re.sub(r"[^A-Za-z]", "", str(item)).lower()
        # skip empty or length-mismatched words
        if not w or len(w) != int(target_len):
            continue
        # keep only sufficiently common english words
        if zipf_frequency(w, "en") >= min_zipf:
            common_words.append(w)

    return common_words

def fetch_random_word(target_len: int = 5, timeout: int = 5, min_zipf: float = 3.5):
    # get a random word from the filtered common word list
    common_words = fetch_common_candidates(target_len, timeout=timeout, min_zipf=min_zipf)
    return random.choice(common_words) if common_words else "streamlit"

# mask unguessed letters with underscores
def mask(word: str, tried: set[str]) -> str:
    # use a set to avoid duplicate guesses and improve lookup speed
    return " ".join(c if c in tried else "_" for c in word) # spaced for better readability (e.g. "_ a _ _ m a n" not "_a__m_a_n")

def new_game(min_len: int = 5) -> dict: # default word length is 5
    # try multiple times to find a word not used in this session
    for _ in range(30):
        word = fetch_random_word(min_len)
        if word not in st.session_state.used_words:
            st.session_state.used_words.add(word)
            break
    else:
        # fallback if everything repeats (api small / cache / filtering)
        word = fetch_random_word(min_len)

    return dict(
        word=word,
        attempts_left=max_tries,
        wrong_letters=[],
        tried=set(), # avoid duplicate guesses
        status="in_progress",
    )

# ---- session state ----
# store game state so it persists across streamlit reruns
if "state" not in st.session_state:
    st.session_state.state = None  # main game memory

# store the current single-letter guess
if "letter" not in st.session_state:
    st.session_state.letter = ""

# store the full-word solve attempt
if "solve" not in st.session_state:
    st.session_state.solve = ""

if "used_words" not in st.session_state:
    st.session_state.used_words = set()  # store words already used in this session

if "ui_warning" not in st.session_state:
    st.session_state.ui_warning = ""

# ---- callbacks ----
def on_guess_letter():
    # handle single-letter guesses
    state_dict = st.session_state.state # get current game state
    # ignore input if no active game
    if not state_dict or state_dict["status"] != "in_progress":
        st.session_state.letter = ""
        return

    # read and normalize user input
    guess = (st.session_state.letter or "").strip().lower()
    # clear input field after reading
    st.session_state.letter = ""

    # validate input: must be a single lowercase letter
    if not re.fullmatch(r"[a-z]", guess or ""):
        return

    # warn if letter was already tried
    if guess in state_dict["tried"]:
        st.session_state.ui_warning = f"'{guess}' was already tried."
        return

    # clear warning and record the guessed letter
    st.session_state.ui_warning = ""
    state_dict["tried"].add(guess)

    # update attempts if guess is wrong
    if guess not in state_dict["word"]:
        state_dict["wrong_letters"].append(guess)
        state_dict["attempts_left"] -= 1

    # check win condition
    if mask(state_dict["word"], state_dict["tried"]).replace(" ", "") == state_dict["word"]: # to convert masked word back to normal
        state_dict["status"] = "won"
    # check loss condition
    elif state_dict["attempts_left"] <= 0:
        state_dict["status"] = "lost"

def on_solve_word():
    # handle full-word solve attempts
    state_dict = st.session_state.state # get current game state
    # ignore input if no active game
    if not state_dict or state_dict["status"] != "in_progress":
        st.session_state.solve = ""
        return

    # read and normalize guess
    guess = (st.session_state.solve or "").strip().lower()
    # clear input field
    st.session_state.solve = ""

    if not guess:
        return

    # correct full-word guess
    if guess == state_dict["word"]:
        state_dict["tried"].update(state_dict["word"])
        state_dict["status"] = "won"
    # incorrect full-word guess
    else:
        state_dict["attempts_left"] -= 1
        if state_dict["attempts_left"] <= 0:
            state_dict["status"] = "lost"

# ---- UI ----
# app title and instructions
st.title("Hangman Game")
st.info("To start a new game, select word length and click 'Start a new game'")

# user-selected word length
len_w = st.number_input("Word length", min_value=3, max_value=12, value=5)

# start a new game when button is pressed
if st.button("Start a new game"):
    st.session_state.state = new_game(len_w)
    # force rerun so UI updates immediately
    st.rerun()

# retrieve current game state
game_state = st.session_state.get("state")
# stop presenting if no game exists
if game_state is None:
    st.stop()

# display hangman image based on remaining attempts
img_path = art_img(game_state["attempts_left"])
st.image(img_path, width=300, caption="Hangman stage")

# convert internal status to display text
status_map = {
    "in_progress": "in progress",
    "won": "won",
    "lost": "lost",
}

display_status = status_map[game_state["status"]]

# display game metrics
c1, c2, c3 = st.columns(3)
c1.metric("Attempts", game_state["attempts_left"])
c2.metric("Status", display_status)
c3.metric("Word length", len(game_state["word"]))

# show masked word and guess history
st.subheader(mask(game_state["word"], game_state["tried"]))
st.write(f"Wrong: `{', '.join(game_state['wrong_letters']) or '-'}`")
st.write(f"Tried: `{', '.join(sorted(game_state['tried'])) or '-'}`")

if st.session_state.ui_warning:
    st.warning(st.session_state.ui_warning)

# show inputs while game is active
if game_state["status"] == "in_progress":
    st.text_input("Guess a letter", key="letter", max_chars=1, on_change=on_guess_letter)
    st.button("Guess", on_click=on_guess_letter)
    st.text_input("Solve the word", key="solve", on_change=on_solve_word)
    st.button("Solve", on_click=on_solve_word)
else:
    # show result when game ends
    if game_state["status"] == "won":
        st.success("You won.")
    else:
        st.error("You lost.")

    # reveal correct word
    st.write(f"Answer: **{game_state['word']}**")

    # restart game button
    if st.button("Play again"):
        st.session_state.state = new_game(len_w)
        st.rerun()