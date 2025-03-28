import pygame
import random
import sys
from pygame.locals import *

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initializes sound
screen = pygame.display.set_mode((1024, 768))
pygame.display.set_caption("Hangman Game")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 28)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (150, 150, 150)
YELLOW = (255, 255, 0)

# Game states
MAIN_MENU = 0
AI_MODE = 1
SINGLE_PLAYER = 2
MULTIPLAYER = 3

#sound files
try:
    correct_sound = pygame.mixer.Sound("correct.wav")
    wrong_sound = pygame.mixer.Sound("wrong.wav")
    win_sound = pygame.mixer.Sound("win.wav")
    lose_sound = pygame.mixer.Sound("lose.wav")
except:
    # If sound files are not found, create dummy sound objects
    correct_sound = wrong_sound = win_sound = lose_sound = type('DummySound', (), {'play': lambda: None})()


def load_words(filename):
    categories = {}
    current_category = None
    current_difficulty = None
    
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('[') and line.endswith(']'):
                try:
                    if ':' in line[1:-1]:
                        category, difficulty = line[1:-1].split(':')
                        current_category = category
                        current_difficulty = difficulty
                        if current_category not in categories:
                            categories[current_category] = {'EASY': [], 'MEDIUM': [], 'HARD': []}
                    else:
                        current_category = line[1:-1]
                        current_difficulty = None
                        if current_category not in categories:
                            categories[current_category] = []
                except ValueError:
                    print(f"Warning: Skipping invalid category line: {line}")
                    continue
            elif current_category is not None:
                if current_difficulty is not None:
                    categories[current_category][current_difficulty].append(line.upper())
                else:
                    categories[current_category].append(line.upper())
    
    return categories


def load_words_with_hints(filename):
    categories = {}
    current_category = None
    
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('[') and line.endswith(']'):
                current_category = line[1:-1]
                categories[current_category] = {}
            elif ':' in line:
                word, hint = line.split(':', 1)
                categories[current_category][word.upper()] = hint.strip()
    
    return categories


class HangmanGame:
    def __init__(self, word, category=None, difficulty=None, hint=None):
        self.word = word.upper()
        self.category = category
        self.difficulty = difficulty
        self.hint = hint
        self.guessed_letters = set()
        self.correct_letters = set()
        self.wrong_guesses = 0
        self.max_attempts = 7  # Fixed at 7 attempts for traditional hangman
        self.score = 0
        self.hints_used = 0
        self.start_time = pygame.time.get_ticks()
        self.game_time = 0

    def get_difficulty_bonus(self):
        if self.difficulty == 'EASY':
            return 5
        elif self.difficulty == 'MEDIUM':
            return 10
        else:  # HARD or EXPERT
            return 15

    def get_time_played(self):
        if self.game_time:
            return self.game_time
        return (pygame.time.get_ticks() - self.start_time) // 1000

    def guess_letter(self, letter):
        letter = letter.upper()
        if letter in self.guessed_letters:
            return 'already_guessed'
        self.guessed_letters.add(letter)
        if letter in self.word:
            self.correct_letters.add(letter)
            self.score += self.get_difficulty_bonus()
            correct_sound.play()
            return 'correct'
        else:
            self.wrong_guesses += 1
            self.score -= 2
            wrong_sound.play()
            return 'incorrect'

    def get_display_word(self):
        return ' '.join([char if char in self.correct_letters else '_' for char in self.word])

    def is_word_guessed(self):
        return all(char in self.correct_letters for char in self.word)

    def use_hint(self):
        if self.hints_used < 2 and self.score >= 20:
            self.hints_used += 1
            self.score -= 20
            
            # Special handling for RANDOM category
            if self.category == 'RANDOM':
                # Display disclaimer for random category
                disclaimer = "WARNING: For RANDOM category, hints may be incorrect!"
                
                # Random chance (0 or 1) to give correct or random hint
                if random.randint(0, 1) == 0:
                    # Give correct hint (one random unguessed letter)
                    unguessed = [c for c in self.word if c not in self.guessed_letters]
                    if unguessed:
                        return disclaimer + "\nHint: Letter '" + random.choice(unguessed) + "' is in the word"
                else:
                    # Give random letter that may or may not be in the word
                    random_letter = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                    return disclaimer + "\nHint: Letter '" + random_letter + "' might be in the word"
                
            # Normal hint handling for other categories
            if self.hint:
                return self.hint
            return f"This is a {self.category.lower()} with {len(self.word)} letters"
        return None


class AIGame(HangmanGame):
    def __init__(self, word_list, word=None, is_user_word=False):
        if word:
            super().__init__(word)
        else:
            super().__init__(random.choice(word_list))
        self.word_list = word_list
        self.possible_words = word_list.copy()
        self.max_attempts = 7
        self.is_user_word = is_user_word
        # English letter frequencies (most common to least common)
        self.letter_frequencies = ['E', 'A', 'R', 'I', 'O', 'T', 'N', 'S', 'L', 'C', 
                                 'U', 'D', 'P', 'M', 'H', 'G', 'B', 'F', 'Y', 'W', 
                                 'K', 'V', 'X', 'Z', 'J', 'Q']
        # For min-max algorithm
        self.partition_cache = {}

    def update_possible_words(self):
        if self.is_user_word:
            return  # Don't update possible words for user-entered words
            
        pattern = self.get_display_word().replace(' ', '')
        self.possible_words = [w for w in self.possible_words if len(w) == len(self.word)]
        self.possible_words = [w for w in self.possible_words if all((c == '_' or w[i] == c)
                                                                     for i, c in enumerate(pattern))]
        wrong_letters = self.guessed_letters - self.correct_letters
        self.possible_words = [w for w in self.possible_words if not any(c in wrong_letters for c in w)]

    def get_word_pattern(self, word, guessed_letters):
        """Get the pattern of a word based on guessed letters"""
        return ''.join([c if c in guessed_letters else '_' for c in word])

    def partition_words(self, words, letter):
        """Partition words into groups based on where the letter appears"""
        partitions = {}
        for word in words:
            pattern = tuple(i for i, c in enumerate(word) if c == letter)
            if pattern not in partitions:
                partitions[pattern] = []
            partitions[pattern].append(word)
        return partitions

    def min_max_guess(self):
        """Choose the letter that minimizes the maximum partition size"""
        if len(self.possible_words) == 1:
            # If only one word left, guess its letters in order
            remaining_letters = [c for c in self.possible_words[0] if c not in self.guessed_letters]
            if remaining_letters:
                return remaining_letters[0]
            return None

        unguessed_letters = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ') - self.guessed_letters
        best_letter = None
        min_max_partition_size = float('inf')

        for letter in unguessed_letters:
            partitions = self.partition_words(self.possible_words, letter)
            max_partition_size = max(len(words) for words in partitions.values()) if partitions else 0
            
            if max_partition_size < min_max_partition_size:
                min_max_partition_size = max_partition_size
                best_letter = letter
            elif max_partition_size == min_max_partition_size:
                # Tie-breaker: prefer vowels first if we haven't found many yet
                vowels = {'A', 'E', 'I', 'O', 'U'}
                current_vowels = len(self.correct_letters & vowels)
                if (letter in vowels and best_letter not in vowels and current_vowels < 2) or \
                   (letter in vowels and best_letter in vowels and self.letter_frequencies.index(letter) < self.letter_frequencies.index(best_letter)):
                    best_letter = letter

        return best_letter

    def ai_guess(self):
        if self.is_user_word:
            # Use min-max algorithm for user-entered words
            return self.min_max_guess()
        else:
            # Use dictionary-based frequency analysis for AI-selected words
            letter_freq = {}
            for word in self.possible_words:
                for c in word:
                    if c not in self.guessed_letters:
                        letter_freq[c] = letter_freq.get(c, 0) + 1
            if not letter_freq:
                return None
            return max(letter_freq, key=letter_freq.get)


def draw_hangman(screen, wrong_guesses):
    # For the gallows
    pygame.draw.line(screen, BLACK, (100, 500), (300, 500), 5)
    pygame.draw.line(screen, BLACK, (200, 500), (200, 100), 5)
    pygame.draw.line(screen, BLACK, (200, 100), (350, 100), 5)
    pygame.draw.line(screen, BLACK, (350, 100), (350, 150), 5)

    # Draws body parts for wrong guesses
    parts = [
        lambda: pygame.draw.circle(screen, BLACK, (350, 175), 25, 3),  # Head
        lambda: pygame.draw.line(screen, BLACK, (350, 200), (350, 300), 3),  # Body
        lambda: pygame.draw.line(screen, BLACK, (350, 220), (300, 250), 3),  # Left arm
        lambda: pygame.draw.line(screen, BLACK, (350, 220), (400, 250), 3),  # Right arm
        lambda: pygame.draw.line(screen, BLACK, (350, 300), (300, 350), 3),  # Left leg
        lambda: pygame.draw.line(screen, BLACK, (350, 300), (400, 350), 3),  # Right leg
    ]

    for i in range(wrong_guesses):
        if i < len(parts):
            parts[i]()


def draw_text(surface, text, color, rect, font=font, aa=False):
    text_surf = font.render(text, aa, color)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)


def draw_background(surface):
    background_color1 = (230, 240, 255)
    background_color2 = (255, 255, 240)
    
    # Draw gradient background
    for y in range(surface.get_height()):
        progress = y / surface.get_height()
        color = tuple(int(background_color1[i] * (1 - progress) + background_color2[i] * progress) 
                    for i in range(3))
        pygame.draw.line(surface, color, (0, y), (surface.get_width(), y))


def get_input_from_gui(prompt):
    input_text = ''
    input_active = True
    input_rect = pygame.Rect(300, 300, 400, 50)

    while input_active:
        draw_background(screen)
        draw_text(screen, prompt, BLACK, pygame.Rect(300, 200, 400, 50))
        pygame.draw.rect(screen, BLACK, input_rect, 2)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    input_active = False
                elif event.key == K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

        txt_surface = font.render(input_text, True, BLACK)
        screen.blit(txt_surface, (input_rect.x + 5, input_rect.y + 5))
        pygame.display.flip()
        clock.tick(30)

    return input_text.strip()


def main_menu():
    screen_width = 1024
    screen_height = 768
    button_width = 300
    button_height = 60
    button_spacing = 20
    
    # Center horizontally
    button_x = (screen_width - button_width) // 2
    
    # Position buttons vertically with proper spacing
    title_y = 100
    first_button_y = 250
    
    buttons = [
        pygame.Rect(button_x, first_button_y + i * (button_height + button_spacing), button_width, button_height)
        for i in range(4)
    ]

    while True:
        draw_background(screen)  # Use gradient background

        # Draw title with shadow effect
        title_shadow_offset = 2
        title_rect = pygame.Rect(0, title_y, screen_width, 60)
        shadow_rect = title_rect.copy()
        shadow_rect.x += title_shadow_offset
        shadow_rect.y += title_shadow_offset
        
        # Draw shadow first
        title_font = pygame.font.Font(None, 72)  # Larger font for title
        draw_text(screen, "Hangman Game", (100, 100, 100), shadow_rect, title_font)
        # Draw main text
        draw_text(screen, "Hangman Game", (0, 0, 100), title_rect, title_font)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for i, button in enumerate(buttons):
                    if button.collidepoint(mouse_pos):
                        if i == 0:
                            ai_mode()
                        elif i == 1:
                            single_player()
                        elif i == 2:
                            multiplayer()
                        elif i == 3:
                            pygame.quit()
                            sys.exit()

        # Draw buttons with hover effect and modern style
        for i, button in enumerate(buttons):
            is_hovered = button.collidepoint(pygame.mouse.get_pos())
            
            # Button colors
            if i == 3:  # Quit button
                base_color = (200, 100, 100)  # Reddish
                hover_color = (220, 120, 120)  # Lighter red
                text_color = (255, 255, 255)  # White text
            else:
                base_color = (100, 150, 255) if not is_hovered else (120, 170, 255)  # Blue/Lighter blue
                text_color = (255, 255, 255)  # White text
            
            # Draw button background
            pygame.draw.rect(screen, base_color, button, border_radius=10)
            
            # Draw button border
            border_color = (70, 120, 225) if not is_hovered else (90, 140, 245)
            pygame.draw.rect(screen, border_color, button, 2, border_radius=10)
            
            # Button labels with consistent styling
            labels = ["AI Mode", "Single Player", "Multiplayer", "Quit"]
            draw_text(screen, labels[i], text_color, button, font)

        pygame.display.flip()
        clock.tick(30)


def ai_mode():
    # First show the selection screen
    selection_active = True
    while selection_active:
        draw_background(screen)
        
        # Draw title
        title_rect = pygame.Rect(0, 100, 1024, 60)
        draw_text(screen, "Select AI Mode", BLACK, title_rect, pygame.font.Font(None, 72))
        
        # Draw options with bigger buttons
        option1_rect = pygame.Rect(212, 300, 600, 80)  # Increased width and height
        option2_rect = pygame.Rect(212, 400, 600, 80)  # Increased width and height
        
        # Draw buttons with hover effect
        for rect, text, is_hovered in [
            (option1_rect, "1. Enter your own word for AI to guess", option1_rect.collidepoint(pygame.mouse.get_pos())),
            (option2_rect, "2. AI selects and guesses a random word", option2_rect.collidepoint(pygame.mouse.get_pos()))
        ]:
            color = (120, 170, 255) if is_hovered else (100, 150, 255)
            pygame.draw.rect(screen, color, rect, border_radius=15)  # Increased border radius
            pygame.draw.rect(screen, (70, 120, 225), rect, 3, border_radius=15)  # Thicker border
            draw_text(screen, text, WHITE, rect, pygame.font.Font(None, 40))  # Larger font
        
        # Draw back button
        back_btn = pygame.Rect(50, 50, 80, 30)
        pygame.draw.rect(screen, BLACK, back_btn, 2)
        draw_text(screen, "Back", BLACK, back_btn, small_font)
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                if option1_rect.collidepoint(event.pos):
                    selection_active = False
                    play_ai_mode(True)  # True for user-entered word
                elif option2_rect.collidepoint(event.pos):
                    selection_active = False
                    play_ai_mode(False)  # False for AI-selected word
                elif back_btn.collidepoint(event.pos):
                    return
        
        pygame.display.flip()
        clock.tick(30)


def play_ai_mode(user_entered_word):
    categories = load_words("words.txt")
    # Combine all words from all categories and difficulties
    all_words = []
    for category_data in categories.values():
        if isinstance(category_data, dict):
            for difficulty_words in category_data.values():
                all_words.extend(difficulty_words)
        else:
            all_words.extend(category_data)
    
    # Get the word based on the mode
    if user_entered_word:
        # Show instructions first
        instruction_screen = True
        while instruction_screen:
            draw_background(screen)
            title_rect = pygame.Rect(0, 100, 1024, 60)
            draw_text(screen, "Word Entry Instructions", BLACK, title_rect, pygame.font.Font(None, 72))
            
            instructions = [
                "Rules for entering a word:",
                "1. Use only letters (A-Z)",
                "2. No spaces or special characters",
                "3. No numbers",
                "4. Minimum length: 3 letters",
                "5. Maximum length: 15 letters",
                "",
                "Click Continue to enter your word"
            ]
            
            for i, text in enumerate(instructions):
                draw_text(screen, text, BLACK, pygame.Rect(200, 200 + i*40, 600, 30), small_font)
            
            continue_btn = pygame.Rect(412, 600, 200, 50)
            pygame.draw.rect(screen, (100, 150, 255), continue_btn, border_radius=10)
            pygame.draw.rect(screen, (70, 120, 225), continue_btn, 2, border_radius=10)
            draw_text(screen, "Continue", WHITE, continue_btn, font)
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN and continue_btn.collidepoint(event.pos):
                    instruction_screen = False
            
            pygame.display.flip()
            clock.tick(30)
        
        # Get the word from user
        word = get_input_from_gui("Enter a word for AI to guess:").upper()
        if not word or not word.isalpha() or len(word) < 3 or len(word) > 15:
            message = "Invalid word! Word must be 3-15 letters long and contain only letters."
            show_message_screen(message)
            return
        game = AIGame(all_words, word, is_user_word=True)  # Use is_user_word=True for user words
    else:
        word = random.choice(all_words)
        game = AIGame(all_words, word, is_user_word=False)  # Use is_user_word=False for AI words
    
    message = ''
    game_active = True
    ai_guesses = 0  # Track total AI guesses

    while game_active:
        draw_background(screen)
        draw_hangman(screen, game.wrong_guesses)

        # Display game information
        draw_text(screen, f"Score: {game.score}", BLACK, pygame.Rect(500, 100, 200, 50))
        draw_text(screen, game.get_display_word(), BLACK, pygame.Rect(500, 200, 300, 50))
        draw_text(screen, f"Guessed: {', '.join(sorted(game.guessed_letters))}",
                  BLACK, pygame.Rect(500, 300, 300, 50))
        draw_text(screen, f"Attempts Left: {game.max_attempts - game.wrong_guesses}",
                  BLACK, pygame.Rect(500, 350, 200, 30))

        game.update_possible_words()
        ai_guess = game.ai_guess()
        if ai_guess and game.wrong_guesses < game.max_attempts:
            result = game.guess_letter(ai_guess)
            ai_guesses += 1
            pygame.time.wait(1000)  # Delay after AI guess
            message = f"AI guessed {ai_guess} - {'Correct' if result == 'correct' else 'Wrong'}!"
            
            # Update display immediately after guess
            draw_text(screen, game.get_display_word(), BLACK, pygame.Rect(500, 200, 300, 50))
            pygame.display.flip()
            
            # Check game state after updating display
            if game.is_word_guessed():
                message = f"AI won! Word guessed in {ai_guesses} attempts!"
                game_active = False
            elif game.wrong_guesses >= game.max_attempts:
                message = f"AI lost! Word was {game.word}"
                game_active = False
        else:
            if game.wrong_guesses >= game.max_attempts:
                message = f"AI lost! Word was {game.word}"
            else:
                message = "AI couldn't guess the word!"
            game_active = False

        draw_text(screen, message, RED, pygame.Rect(500, 400, 300, 50), small_font)

        back_btn = pygame.Rect(700, 550, 80, 30)
        pygame.draw.rect(screen, BLACK, back_btn, 2)
        draw_text(screen, "Back", BLACK, back_btn, small_font)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN and back_btn.collidepoint(event.pos):
                return

        pygame.display.flip()
        clock.tick(2)

    # Keep showing the final state until user clicks back
    while True:
        draw_background(screen)
        draw_hangman(screen, game.wrong_guesses)
        draw_text(screen, game.get_display_word(), BLACK, pygame.Rect(500, 200, 300, 50))
        draw_text(screen, message, RED, pygame.Rect(500, 400, 300, 50), small_font)
        draw_text(screen, f"Guessed: {', '.join(sorted(game.guessed_letters))}", 
                 BLACK, pygame.Rect(500, 300, 300, 50))
        draw_text(screen, f"Total AI Guesses: {ai_guesses}", 
                 BLACK, pygame.Rect(500, 350, 200, 30))
        
        pygame.draw.rect(screen, BLACK, back_btn, 2)
        draw_text(screen, "Back", BLACK, back_btn, small_font)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN and back_btn.collidepoint(event.pos):
                return
        pygame.display.flip()
        clock.tick(30)


def show_message_screen(message):
    message_active = True
    while message_active:
        draw_background(screen)
        draw_text(screen, message, RED, pygame.Rect(200, 300, 600, 50), font)
        
        back_btn = pygame.Rect(700, 550, 80, 30)
        pygame.draw.rect(screen, BLACK, back_btn, 2)
        draw_text(screen, "Back", BLACK, back_btn, small_font)
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN and back_btn.collidepoint(event.pos):
                return
        
        pygame.display.flip()
        clock.tick(30)


def single_player():
    categories = load_words("words.txt")
    hints_data = load_words_with_hints("words_with_hints.txt")
    category_list = list(categories.keys())
    current_category = category_list[0]
    current_difficulty = 'MEDIUM'
    
    def get_random_word():
        nonlocal current_category, current_difficulty
        if current_difficulty == 'EXPERT':
            # For expert mode, randomly select a word from any HARD difficulty
            possible_words = []
            for cat in categories:
                if cat != 'EXPERT' and cat != 'RANDOM':  # Exclude EXPERT and RANDOM categories
                    possible_words.extend(categories[cat]['HARD'])
            word = random.choice(possible_words)
            # Don't provide category info for expert mode
            return word, None
        elif current_category == 'EXPERT':
            word = random.choice(categories['EXPERT'])
            return word, None
        else:
            word_list = categories[current_category][current_difficulty]
            word = random.choice(word_list)
            hint = hints_data.get(current_category, {}).get(word, None)
            return word, hint

    word, hint = get_random_word()
    game = HangmanGame(word, current_category, current_difficulty, hint)
    input_text = ''
    message = ''
    game_active = True
    show_word = False

    def start_new_game():
        nonlocal word, hint, game, input_text, message, game_active, show_word
        word, hint = get_random_word()
        game = HangmanGame(word, current_category, current_difficulty, hint)
        input_text = ''
        message = ''
        game_active = True
        show_word = False

    while True:
        draw_background(screen)  # Use gradient background
        # Move hangman drawing to the left
        draw_hangman(screen, game.wrong_guesses)

        # Game info section - moved right and adjusted spacing
        info_x = 600
        draw_text(screen, f"Score: {game.score}", BLACK, pygame.Rect(info_x, 30, 200, 30))
        if current_difficulty != 'EXPERT':
            draw_text(screen, f"Category: {game.category}", BLUE, pygame.Rect(info_x, 70, 200, 30))
        draw_text(screen, f"Difficulty: {game.difficulty}", 
                 GREEN if game.difficulty == 'EASY' else 
                 YELLOW if game.difficulty == 'MEDIUM' else 
                 RED if game.difficulty == 'HARD' else 
                 BLUE, pygame.Rect(info_x, 110, 200, 30))
        draw_text(screen, f"Time: {game.get_time_played()}s", BLACK, pygame.Rect(info_x, 150, 200, 30))
        draw_text(screen, f"Attempts Left: {game.max_attempts - game.wrong_guesses}", 
                 GREEN if game.wrong_guesses < game.max_attempts - 2 else 
                 YELLOW if game.wrong_guesses < game.max_attempts - 1 else RED, 
                 pygame.Rect(info_x, 190, 200, 30))

        # Category selection - moved down and spread out
        cat_text = "Category: "
        cat_surface = small_font.render(cat_text, True, BLACK)
        screen.blit(cat_surface, (50, 650))
        x_pos = 50 + cat_surface.get_width()
        
        # Calculate button width based on longest category name
        cat_btn_width = max(len(cat) * 10 + 20 for cat in category_list)
        cat_spacing = 20  # Space between category buttons
        
        for i, cat in enumerate(category_list):
            color = BLUE if cat == current_category else BLACK
            cat_btn = pygame.Rect(x_pos, 645, cat_btn_width, 30)
            pygame.draw.rect(screen, color, cat_btn, 2)
            draw_text(screen, cat, color, cat_btn, small_font)
            x_pos += cat_btn_width + cat_spacing

        # Difficulty selection - moved down and spread out
        diff_text = "Difficulty: "
        diff_surface = small_font.render(diff_text, True, BLACK)
        screen.blit(diff_surface, (50, 600))
        x_pos = 50 + diff_surface.get_width()
        
        difficulties = ['EASY', 'MEDIUM', 'HARD', 'EXPERT']
        diff_btn_width = 100  # Fixed width for difficulty buttons
        diff_spacing = 20  # Space between difficulty buttons
        
        for diff in difficulties:
            color = (GREEN if diff == 'EASY' else 
                    YELLOW if diff == 'MEDIUM' else 
                    RED if diff == 'HARD' else 
                    BLUE)
            if diff == current_difficulty:
                color = BLUE
            diff_btn = pygame.Rect(x_pos, 595, diff_btn_width, 30)
            pygame.draw.rect(screen, color, diff_btn, 2)
            draw_text(screen, diff, color, diff_btn, small_font)
            x_pos += diff_btn_width + diff_spacing

        # Word display
        word_rect = pygame.Rect(info_x, 250, 400, 50)
        pygame.draw.rect(screen, BLACK, word_rect, 2)
        draw_text(screen, game.get_display_word(), BLACK, word_rect)

        # Guessed letters with color coding
        guessed_text = "Guessed: "
        guessed_surface = small_font.render(guessed_text, True, BLACK)
        screen.blit(guessed_surface, (info_x, 300))
        x_pos = info_x + guessed_surface.get_width()
        for letter in sorted(game.guessed_letters):
            color = GREEN if letter in game.correct_letters else RED
            letter_surface = small_font.render(letter, True, color)
            screen.blit(letter_surface, (x_pos, 300))
            x_pos += letter_surface.get_width() + 5

        # Message display
        message_rect = pygame.Rect(info_x, 350, 400, 50)
        draw_text(screen, message, RED, message_rect)

        # Game control buttons
        if current_difficulty != 'EXPERT':
            hint_btn = pygame.Rect(info_x, 400, 80, 30)
            btn_color = BLACK if game.score >= 20 and game_active else GRAY
            pygame.draw.rect(screen, btn_color, hint_btn, 2)
            draw_text(screen, "Hint", btn_color, hint_btn, small_font)

        new_game_btn = pygame.Rect(info_x + 100, 400, 120, 30)
        pygame.draw.rect(screen, BLUE, new_game_btn, 2)
        draw_text(screen, "New Game", BLUE, new_game_btn, small_font)

        if game_active:
            input_rect = pygame.Rect(info_x, 450, 200, 32)
            pygame.draw.rect(screen, BLACK, input_rect, 2)
            txt_surface = font.render(input_text, True, BLACK)
            screen.blit(txt_surface, (input_rect.x + 5, input_rect.y + 5))

        back_btn = pygame.Rect(900, 700, 80, 30)
        pygame.draw.rect(screen, BLACK, back_btn, 2)
        draw_text(screen, "Back", BLACK, back_btn, small_font)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and game_active:
                if event.key == K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == K_RETURN:
                    if len(input_text) == 1:
                        result = game.guess_letter(input_text)
                        if result == 'correct':
                            message = "Correct guess!"
                        elif result == 'incorrect':
                            message = "Wrong guess! Try again."
                        else:
                            message = f"Letter '{input_text}' was already guessed!"
                        input_text = ''
                    else:
                        message = "Please enter a single letter!"
                elif event.unicode.isalpha():
                    input_text += event.unicode.upper()
            if event.type == MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                
                # Category buttons
                x_pos = 50 + small_font.render("Category: ", True, BLACK).get_width()
                for i, cat in enumerate(category_list):
                    cat_btn = pygame.Rect(x_pos, 645, cat_btn_width, 30)
                    if cat_btn.collidepoint(mouse_pos):
                        current_category = cat
                        start_new_game()
                    x_pos += cat_btn_width + cat_spacing

                # Difficulty buttons
                x_pos = 50 + small_font.render("Difficulty: ", True, BLACK).get_width()
                for diff in difficulties:
                    diff_btn = pygame.Rect(x_pos, 595, diff_btn_width, 30)
                    if diff_btn.collidepoint(mouse_pos):
                        current_difficulty = diff
                        start_new_game()
                    x_pos += diff_btn_width + diff_spacing

                if current_difficulty != 'EXPERT':
                    if hint_btn.collidepoint(event.pos) and game.score >= 20 and game_active:
                        hint = game.use_hint()
                        if hint:
                            message = hint
                        else:
                            message = "No hints available or not enough points (need 20 points)"
                
                if new_game_btn.collidepoint(event.pos):
                    start_new_game()
                elif back_btn.collidepoint(event.pos):
                    return

        if game.is_word_guessed() and game_active:
            game.game_time = game.get_time_played()
            bonus = game.get_difficulty_bonus() * 10
            game.score += bonus
            message = f"Congratulations! You won in {game.game_time}s! The word was '{game.word}' (+{bonus} difficulty bonus)"
            win_sound.play()
            game_active = False
        elif game.wrong_guesses >= game.max_attempts and game_active:
            game.game_time = game.get_time_played()
            message = f"Game Over! The word was '{game.word}'"
            lose_sound.play()
            game_active = False

        pygame.display.flip()
        clock.tick(30)


def multiplayer():
    player1 = get_input_from_gui("Enter Player 1 name:")
    player2 = get_input_from_gui("Enter Player 2 name:")
    rounds = int(get_input_from_gui("Enter number of rounds:"))
    scores = {player1: 0, player2: 0}
    message = ''
    
    # Load all words with categories and difficulties
    categories = load_words("words.txt")
    hints_data = load_words_with_hints("words_with_hints.txt")
    
    for current_round in range(rounds):
        # Select random category and difficulty for player 1
        valid_categories = [cat for cat in categories.keys() if cat != 'EXPERT']
        p1_category = random.choice(valid_categories)
        p1_difficulty = random.choice(['EASY', 'MEDIUM', 'HARD'])
        
        # Get word for player 1
        p1_word = random.choice(categories[p1_category][p1_difficulty])
        p1_hint = hints_data.get(p1_category, {}).get(p1_word, None)
        
        # For player 2, use same difficulty but any category
        p2_category = random.choice(valid_categories)
        p2_word = random.choice(categories[p2_category][p1_difficulty])  # Use p1's difficulty
        p2_hint = hints_data.get(p2_category, {}).get(p2_word, None)
        
        for current_player, word, hint, category in [(player1, p1_word, p1_hint, p1_category),
                                                   (player2, p2_word, p2_hint, p2_category)]:
            game = HangmanGame(word, category, p1_difficulty, hint)  # Both use p1's difficulty
            input_text = ''
            game_active = True
            round_score = 0  # Track score for this round

            while game_active:
                draw_background(screen)  # Use gradient background
                draw_hangman(screen, game.wrong_guesses)

                # Display game information
                draw_text(screen, f"Round {current_round + 1}/{rounds}", BLACK, pygame.Rect(500, 50, 200, 50))
                draw_text(screen, f"{player1}: {scores[player1]}", BLACK, pygame.Rect(500, 100, 200, 50))
                draw_text(screen, f"{player2}: {scores[player2]}", BLACK, pygame.Rect(500, 150, 200, 50))
                draw_text(screen, f"Current Player: {current_player}", BLACK, pygame.Rect(500, 200, 200, 50))
                draw_text(screen, f"Difficulty: {p1_difficulty}", BLACK, pygame.Rect(500, 230, 200, 50))
                draw_text(screen, f"Category: {category}", BLACK, pygame.Rect(500, 260, 200, 50))
                draw_text(screen, f"Round Score: {game.score}", BLACK, pygame.Rect(500, 290, 200, 50))
                draw_text(screen, game.get_display_word(), BLACK, pygame.Rect(500, 320, 300, 50))
                draw_text(screen, f"Guessed: {', '.join(sorted(game.guessed_letters))}",
                          BLACK, pygame.Rect(500, 350, 300, 50))
                draw_text(screen, message, RED, pygame.Rect(500, 380, 300, 50), small_font)

                # Rest of the game loop remains the same...
                input_rect = pygame.Rect(500, 420, 200, 32)
                pygame.draw.rect(screen, BLACK, input_rect, 2)
                txt_surface = font.render(input_text, True, BLACK)
                screen.blit(txt_surface, (input_rect.x + 5, input_rect.y + 5))

                hint_btn = pygame.Rect(500, 470, 80, 30)
                btn_color = BLACK if game.score >= 20 else GRAY
                pygame.draw.rect(screen, btn_color, hint_btn, 2)
                draw_text(screen, "Hint", btn_color, hint_btn, small_font)

                back_btn = pygame.Rect(700, 550, 80, 30)
                pygame.draw.rect(screen, BLACK, back_btn, 2)
                draw_text(screen, "Back", BLACK, back_btn, small_font)

                for event in pygame.event.get():
                    if event.type == QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == KEYDOWN:
                        if event.key == K_BACKSPACE:
                            input_text = input_text[:-1]
                        elif event.key == K_RETURN:
                            if len(input_text) == 1:
                                result = game.guess_letter(input_text)
                                if result == 'correct':
                                    message = "Correct!"
                                elif result == 'incorrect':
                                    message = "Wrong!"
                                else:
                                    message = "Already guessed!"
                                input_text = ''
                            else:
                                message = "Enter single letter!"
                        elif event.unicode.isalpha():
                            input_text += event.unicode.upper()
                    if event.type == MOUSEBUTTONDOWN:
                        if hint_btn.collidepoint(event.pos):
                            if game.score >= 20:
                                hint = game.use_hint()
                                if hint:
                                    message = hint
                                else:
                                    message = "No hints left!"
                            else:
                                message = "Need 20 points for hint!"
                        if back_btn.collidepoint(event.pos):
                            return

                if game.is_word_guessed():
                    message = f"Correct! The word was: {game.word}"
                    scores[current_player] += game.score  # Add round score to total
                    pygame.time.wait(2000)
                    game_active = False
                elif game.wrong_guesses >= game.max_attempts:
                    message = f"Game Over! The word was: {game.word}"
                    pygame.time.wait(2000)
                    game_active = False

                pygame.display.flip()
                clock.tick(30)

    # Winner display with back button
    screen.fill(WHITE)
    draw_text(screen, f"Final Scores:", BLACK, pygame.Rect(400, 200, 400, 50))
    draw_text(screen, f"{player1}: {scores[player1]}", BLACK, pygame.Rect(400, 250, 400, 50))
    draw_text(screen, f"{player2}: {scores[player2]}", BLACK, pygame.Rect(400, 300, 400, 50))
    winner = max(scores, key=scores.get)
    draw_text(screen, f"Winner: {winner}!", GREEN, pygame.Rect(400, 350, 400, 50))

    back_btn = pygame.Rect(350, 450, 100, 50)
    pygame.draw.rect(screen, BLUE, back_btn)
    draw_text(screen, "Main Menu", WHITE, back_btn)

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN and back_btn.collidepoint(pygame.mouse.get_pos()):
                return
            if event.type == QUIT:
                pygame.quit()
                sys.exit()


if __name__ == "__main__":
    main_menu()