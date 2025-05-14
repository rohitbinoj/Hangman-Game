# Hangman Game with AI and Enhanced UI

A Python-based implementation of the classic Hangman game built with Pygame, featuring multiple game modes, an intelligent AI opponent, dynamic difficulty levels, and a modern user interface.

## Features

### Game Modes

1. **Single Player Mode**
   - Four distinct difficulty levels with color-coding:
     - Easy - Shorter words (3-6 letters), common letters
     - Medium - Average length (5-8 letters), balanced difficulty
     - Hard - Longer words (7+ letters), rare letters
     - Expert - Hidden category, no hints, challenging words
   - Multiple word categories to choose from
   - Hint system (costs 25 points per hint, max 2 hints)
   - Visual and audio feedback
   - Real-time scoring system

2. **AI Mode**
   - Two interaction options:
     - Challenge AI with your own words
     - Watch AI solve randomly selected words
   - Dual AI algorithms:
     - Min-Max algorithm for user-entered words
     - Frequency analysis for dictionary words
   - Real-time visualization of AI thinking process
   - Word length restrictions: 3-15 letters

3. **Multiplayer Mode**
   - Two-player turn-based gameplay
   - Customizable number of rounds
   - Individual scoring per player
   - Shared difficulty levels
   - Different categories per player
   - Competitive scoring system

### Scoring System

- **Base Points**
  - Varies by letter frequency (rare letters worth more)
  - Difficulty multipliers:
    - Easy: 8x
    - Medium: 12x
    - Hard: 18x
    - Expert: 25x

- **Bonus Points**
  - Time bonus: Up to 10 points per 10 seconds saved
  - Attempt bonus: 10 points per unused attempt
  - Word length bonus: 2 points per letter
  - No-hint bonus: 50 points
  - Perfect game bonus: 100 points (no wrong guesses)

### Technical Features
- Modern UI with:
  - Gradient/image backgrounds
  - Color-coded difficulty indicators
  - Interactive buttons with hover effects
  - Real-time visual feedback
- Sound Effects System:
  - Correct/wrong guess feedback
  - Win/lose sound effects
- Extensive Word Management:
  - Category-based organization
  - Difficulty-specific word pools
  - Hint database integration

## Requirements
- Python 3.x
- Pygame library
- Required files:
  - words.txt (word database)
  - words_with_hints.txt (hint database)
  - Sound files (correct.wav, wrong.wav, win.wav, lose.wav)
  - image.png (background image)

## Installation
1. Clone the repository
2. Install Pygame:
   ```bash
   pip install pygame
   ```
3. Launch the game:
   ```bash
   python hangmanduplicate.py
   ```

## File Structure
- `hangmanGame.py`: Main game implementation
- `words.txt`: Word database with categories and difficulty levels
- `words_with_hints.txt`: Hint database for words
- `image.png`: Background image
- Sound files:
  - `correct.wav`: Correct guess sound
  - `wrong.wav`: Wrong guess sound
  - `win.wav`: Victory sound
  - `lose.wav`: Game over sound

## Game Rules

- 7 attempts per word
- Incorrect guesses add parts to the hangman
- Hints show:
  - A hidden letter for normal categories
  - Special hints for RANDOM category (may be random)
- Game ends when:
  - Word is correctly guessed (win)
  - Hangman is completed (lose)

## AI Implementation

The game features two specialized AI algorithms:

1. **Min-Max Algorithm** (User-word Mode)
   - Optimizes guessing by minimizing maximum possible word groups
   - Prioritizes vowels early in the game
   - Uses pattern recognition for efficient guessing
   - Employs letter frequency for tiebreaking

2. **Frequency Analysis** (Dictionary Mode)
   - Dynamically updates letter frequencies based on possible words
   - Filters word list using revealed pattern
   - Adapts strategy based on remaining word pool
   - Optimizes for efficiency in word discovery

## Controls

- Type letters to make guesses
- Enter/Return to submit guesses
- Mouse clicks for:
  - Category selection
  - Difficulty selection
  - Hint button (when available)
  - Menu navigation
- Back button to return to previous menu
