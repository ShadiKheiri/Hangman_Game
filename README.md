# Hangman Game (Streamlit)

An interactive Hangman game built with Python and Streamlit that uses an external API to fetch random words, filtered to common English vocabulary, and features visual hangman stages with real-time game state updates.

## Live Demo

Play the game here: [Hangman Game Demo](https://hangman-guess-word-game.streamlit.app/)

## Features

- Guess letters one by one or solve the full word
- Visual hangman images that update with remaining attempts
- Prevents duplicate guesses with clear warnings
- Adjustable word length
- Uses an external API to fetch random words and filters them to keep common English vocabulary
- Clean UI with live metrics and game status

## How the Game Works

- A random common English word is fetched from an external API at the start of each game
- The word is filtered using frequency-based heuristics to ensure it is commonly used in English
- You have a limited number of attempts
- Correct guesses reveal letters
- Incorrect guesses reduce remaining attempts
- You win by guessing all letters or solving the word
- You lose when attempts reach zero
