# Hangman Game with AI
A modern, feature-rich implementation of the classic Hangman game built with Pygame, featuring an AI opponent and multiple game modes.

## Features

### Game Modes
1. **AI Mode**
   - Play against an intelligent AI opponent
   - Two AI gameplay options:
     - Enter your own word for the AI to guess
     - Watch the AI select and guess random words
   - AI uses advanced algorithms:
     - Min-Max strategy for user-entered words
     - Frequency analysis for dictionary words

2. **Single Player Mode**
   - Multiple difficulty levels (Easy, Medium, Hard, Expert)
   - Category-based word selection
   - Hint system with scoring
   - Time-based bonus points
   - Visual feedback with hangman drawing

3. **Multiplayer Mode**
   - Two-player competitive gameplay
   - Turn-based word guessing
   - Score tracking
   - Category and difficulty selection

### Technical Features
- Modern UI with gradient backgrounds
- Sound effects for game events
- Responsive controls
- Dynamic difficulty scaling
- Hint system with point costs
- Category-based word organization
- Time tracking and scoring system

## Requirements
- Python 3.x
- Pygame library
- Sound files (optional)

## Installation
1. Clone the repository
2. Install required packages:
   ```bash
   pip install pygame
   ```
3. Run the game:
   ```bash
   python hangmanGame.py
   ```

## File Structure
- `hangmanGame.py`: Main game file
- `words.txt`: Word database with categories
- `words_with_hints.txt`: Word hints database
- Sound files (optional):
  - correct.wav
  - wrong.wav
  - win.wav
  - lose.wav

## Game Rules
- Players have 7 attempts to guess the word
- Correct guesses reveal letters and award points
- Wrong guesses reduce score and progress the hangman
- Hints are available at a cost of 20 points
- Time bonuses are awarded for quick wins
- Difficulty affects scoring multipliers

## AI Algorithm
The game features two AI strategies:
1. **Min-Max Algorithm** (for user-entered words):
   - Optimizes letter selection to minimize maximum possible outcomes
   - Adapts strategy based on revealed letters
   - Prioritizes vowels and common consonants

2. **Frequency Analysis** (for dictionary words):
   - Uses word database to calculate letter frequencies
   - Updates possible words based on guesses
   - Optimizes for word pattern matching
