import pygame
import random
import sys
import tkinter as tk
from tkinter import messagebox, Toplevel
from pygame.locals import *

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initializes sound
screen = pygame.display.set_mode((1280, 920))  
pygame.display.set_caption("Hangman Game")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 28)
title_font = pygame.font.Font(None, 48)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (150, 150, 150)
YELLOW = (255, 255, 0)
LIGHT_BLUE = (173, 216, 230)

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
        self.max_attempts = 7
        self.score = 0
        self.hints_used = 0
        self.start_time = pygame.time.get_ticks()
        self.game_time = 0
        self.current_streak = 0
        self.max_streak = 0
        self.consecutive_wrong = 0

    def get_difficulty_bonus(self):
        return {
            'EASY': 8,
            'MEDIUM': 12,
            'HARD': 18,
            'EXPERT': 25
        }.get(self.difficulty, 8)  # Default to EASY if difficulty not set

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
            self.current_streak += 1
            self.max_streak = max(self.max_streak, self.current_streak)
            self.consecutive_wrong = 0
            # Base points + streak bonus
            self.score += self.get_difficulty_bonus() + (self.current_streak * 5)
            correct_sound.play()
            return 'correct'
        else:
            self.wrong_guesses += 1
            self.current_streak = 0
            self.consecutive_wrong += 1
            # Penalty for wrong guesses
            self.score -= (5 + (self.consecutive_wrong * 2))
            wrong_sound.play()
            return 'incorrect'

    def calculate_final_score(self):
        # Base score from gameplay
        final_score = self.score
        
        # Time bonus (faster = more points)
        time_bonus = max(0, 100 - self.get_time_played()) // 10
        final_score += time_bonus
        
        # Remaining attempts bonus
        attempts_bonus = (self.max_attempts - self.wrong_guesses) * 10
        final_score += attempts_bonus
        
        # Word length bonus
        length_bonus = len(self.word) * 2
        final_score += length_bonus
        
        # Special bonuses
        if self.hints_used == 0:
            final_score += 50  # No-hint bonus
            
        if self.wrong_guesses == 0:
            final_score += 100  # Perfect game bonus
            
        return final_score

    def get_display_word(self):
        return ' '.join([char if char in self.correct_letters else '_' for char in self.word])

    def is_word_guessed(self):
        return all(char in self.correct_letters for char in self.word)

    def use_hint(self):
        if self.hints_used < 2 and self.score >= 25:  
            self.hints_used += 1
            self.score -= 25  
            
            # Special handling for RANDOM category
            if self.category == 'RANDOM':
                disclaimer = "WARNING: For RANDOM category, hints may be incorrect!"
                
                if random.randint(0, 1) == 0:
                    unguessed = [c for c in self.word if c not in self.guessed_letters]
                    if unguessed:
                        return disclaimer + "\nHint: Letter '" + random.choice(unguessed) + "' is in the word"
                else:
                    random_letter = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                    return disclaimer + "\nHint: Letter '" + random_letter + "' might be in the word"
                
            # Normal hint handling for other categories
            if self.hint:
                return self.hint
            return f"This is a {self.category.lower()} with {len(self.word)} letters"
        return None

    def show_continue_screen(self, screen):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    # Continue button area (centered)
                    continue_btn = pygame.Rect(490, 400, 300, 50)
                    exit_btn = pygame.Rect(490, 470, 300, 50)
                    if continue_btn.collidepoint(mouse_pos):
                        return True  # User wants to continue
                    if exit_btn.collidepoint(mouse_pos):
                        return False  # User wants to exit

            screen.fill(WHITE)
            # Draw continue message
            continue_text = title_font.render("Continue to iterate?", True, BLACK)
            screen.blit(continue_text, (440, 300))

            # Draw continue button
            pygame.draw.rect(screen, GREEN, (490, 400, 300, 50))
            continue_btn_text = font.render("Continue", True, BLACK)
            screen.blit(continue_btn_text, (580, 410))

            # Draw exit button
            pygame.draw.rect(screen, RED, (490, 470, 300, 50))
            exit_btn_text = font.render("Exit", True, BLACK)
            screen.blit(exit_btn_text, (600, 480))

            pygame.display.flip()
            clock.tick(60)

    def reset_game(self):
        self.guessed_letters.clear()
        self.correct_letters.clear()
        self.wrong_guesses = 0
        self.score = 0
        self.hints_used = 0
        self.start_time = pygame.time.get_ticks()
        self.game_time = 0
        self.current_streak = 0
        self.consecutive_wrong = 0

    def check_game_end(self, screen):
        if self.is_word_guessed() or self.wrong_guesses >= self.max_attempts:
            if self.is_word_guessed():
                win_sound.play()
            else:
                lose_sound.play()
            
            # Calculate final score
            final_score = self.calculate_final_score()
            
            # Show game over screen with continue option
            if self.show_continue_screen(screen):
                self.reset_game()
                return True  # Continue playing
            return False  # Exit game
        return True  # Game still in progress

    def run_game(self):
        running = True
        current_hint = None
        difficulty = "Medium"  # Default difficulty
        
        while running:
            # Game loop logic
            if game_active:
                # Difficulty selector
                easy_button = pygame.Rect(50, 50, 100, 30)
                medium_button = pygame.Rect(160, 50, 100, 30)
                hard_button = pygame.Rect(270, 50, 100, 30)
                
                # Draw difficulty buttons
                for btn, text, pos in [(easy_button, "Easy", (70, 55)), 
                                     (medium_button, "Medium", (170, 55)), 
                                     (hard_button, "Hard", (290, 55))]:
                    color = (100, 200, 100) if difficulty == text else (150, 150, 150)
                    pygame.draw.rect(screen, color, btn)
                    diff_text = small_font.render(text, True, BLACK)
                    screen.blit(diff_text, pos)
                
                # Display current hint if available
                if current_hint:
                    hint_text = small_font.render(f"Hint: {current_hint}", True, (200, 200, 100))
                    screen.blit(hint_text, (400, 100))
                
                # Handle difficulty selection
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = event.pos
                        if easy_button.collidepoint(mouse_pos):
                            difficulty = "Easy"
                        elif medium_button.collidepoint(mouse_pos):
                            difficulty = "Medium"
                        elif hard_button.collidepoint(mouse_pos):
                            difficulty = "Hard"
                            
                # Adjust game parameters based on difficulty
                max_mistakes = {"Easy": 8, "Medium": 6, "Hard": 4}[difficulty]
                if mistakes >= max_mistakes:
                    game_active = False
                    lose_sound.play()
            else:
                # Display "Continue to iterate?" prompt
                continue_text = font.render("Continue to iterate?", True, BLACK)
                yes_button = pygame.Rect(300, 350, 80, 40)
                no_button = pygame.Rect(400, 350, 80, 40)
                
                # Draw buttons
                pygame.draw.rect(screen, (100, 200, 100), yes_button)
                pygame.draw.rect(screen, (200, 100, 100), no_button)
                
                # Draw button text
                yes_text = small_font.render("Yes", True, BLACK)
                no_text = small_font.render("No", True, BLACK)
                screen.blit(continue_text, (250, 300))
                screen.blit(yes_text, (320, 360))
                screen.blit(no_text, (425, 360))
                
                # Handle button clicks
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = event.pos
                        if yes_button.collidepoint(mouse_pos):
                            # Reset game state
                            self.word = random.choice(self.words)
                            self.guessed_letters.clear()
                            mistakes = 0
                            game_active = True
                            current_hint = None
                        elif no_button.collidepoint(mouse_pos):
                            running = False


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
    try:
        # Try to load and draw the background image
        background_image = pygame.image.load("image.png")
        # Scale the image to fit the screen
        background_image = pygame.transform.scale(background_image, (surface.get_width(), surface.get_height()))
        surface.blit(background_image, (0, 0))
    except:
        # Fallback to gradient background if image loading fails
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
    input_rect = pygame.Rect(400, 300, 400, 50)

    while input_active:
        draw_background(screen)
        draw_text(screen, prompt, BLACK, pygame.Rect(400, 200, 400, 50))
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


def about_game():
    current_page = 0
    pages = [
        {
            "title": "Game Rules",
            "content": [
                "Welcome to Hangman!",
                "",
                "Basic Rules:",
                "- Try to guess a hidden word one letter at a time",
                "- You have 7 attempts before the hangman is complete",
                "- Each wrong guess adds a part to the hangman",
                "- Game ends when you guess the word or run out of attempts",
                "",
                "Controls:",
                "- Type a letter and press Enter to make a guess",
                "- Use the Hint button if you need help (costs points)",
                "- Watch your remaining attempts and score"
            ]
        },
        {
            "title": "Scoring System",
            "content": [
                "How Points are Earned:",
                "",
                "Base Points:",
                "- Each correct guess earns points based on letter frequency",
                "- Rare letters (J, Q, X, Z) earn more points",
                "- Common letters (E, A, T, I) earn fewer points",
                "",
                "Bonus Points:",
                "- Time bonus: +50 points if completed under 30 seconds",
                "- Perfect game bonus: +100 points (no wrong guesses)",
                "- No-hint bonus: +50 points (no hints used)",
                "- Word length bonus: +2 points per letter"
            ]
        },
        {
            "title": "Game Modes",
            "content": [
                "Available Game Modes:",
                "",
                "Single Player:",
                "- Play against the computer",
                "- Choose from different categories",
                "- Multiple difficulty levels",
                "",
                "Multiplayer:",
                "- Play with a friend",
                "- Take turns guessing words",
                "- Compete for high scores",
                "",
                "AI Mode:",
                "- Watch AI solve puzzles",
                "- Challenge AI with your own words"
            ]
        },
        {
            "title": "Difficulty Levels",
            "content": [
                "Choose Your Challenge:",
                "Easy Mode:",
                "- Shorter words (3-6 letters)",
                "- More common letters",
                "- More hints available",

                "Medium Mode:",
                "- Average length words (5-8 letters)",
                "- Balanced letter frequency",

                "Hard Mode:",
                "- Longer words (7+ letters)",
                "- More rare letters",

                "Expert Mode:",
                "- No hints available",
                "- Limited categories",
                "- Hidden word information"
            ]
        }
    ]
    
    while True:
        draw_background(screen)
        
        # Title with page indicator
        title_y = 50
        title_font = pygame.font.Font(None, 72)
        page_info = f"{pages[current_page]['title']} ({current_page + 1}/{len(pages)})"
        draw_text(screen, page_info, BLACK, pygame.Rect(0, title_y, 1280, 60), title_font)
        
        # Content
        content_font = pygame.font.Font(None, 36)
        content_spacing = 40
        start_y = 140
        
        # Draw current page content
        for i, line in enumerate(pages[current_page]["content"]):
            color = BLUE if line.endswith(":") else BLACK
            draw_text(screen, line, color, 
                     pygame.Rect(200, start_y + i * content_spacing, 880, 40),
                     content_font)
        
        # Navigation buttons
        button_y = 750
        button_width = 150
        button_height = 50
        button_spacing = 20
        
        # Previous button
        prev_btn = pygame.Rect(440, button_y, button_width, button_height)
        prev_enabled = current_page > 0
        prev_color = (100, 150, 255) if prev_enabled else GRAY
        is_prev_hovered = prev_btn.collidepoint(pygame.mouse.get_pos()) and prev_enabled
        
        pygame.draw.rect(screen, prev_color if not is_prev_hovered else (120, 170, 255),
                        prev_btn, border_radius=10)
        pygame.draw.rect(screen, (70, 120, 225) if prev_enabled else GRAY,
                        prev_btn, 2, border_radius=10)
        draw_text(screen, "Previous", WHITE, prev_btn, content_font)
        
        # Next button
        next_btn = pygame.Rect(440 + button_width + button_spacing, button_y, button_width, button_height)
        next_enabled = current_page < len(pages) - 1
        next_color = (100, 150, 255) if next_enabled else GRAY
        is_next_hovered = next_btn.collidepoint(pygame.mouse.get_pos()) and next_enabled
        
        pygame.draw.rect(screen, next_color if not is_next_hovered else (120, 170, 255),
                        next_btn, border_radius=10)
        pygame.draw.rect(screen, (70, 120, 225) if next_enabled else GRAY,
                        next_btn, 2, border_radius=10)
        draw_text(screen, "Next", WHITE, next_btn, content_font)
        
        # Back to Menu button
        back_btn = pygame.Rect(440 + (button_width + button_spacing) * 2, button_y, button_width, button_height)
        is_back_hovered = back_btn.collidepoint(pygame.mouse.get_pos())
        
        pygame.draw.rect(screen, (100, 150, 255) if not is_back_hovered else (120, 170, 255),
                        back_btn, border_radius=10)
        pygame.draw.rect(screen, (70, 120, 225), back_btn, 2, border_radius=10)
        draw_text(screen, "Back", WHITE, back_btn, content_font)
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                if prev_btn.collidepoint(event.pos) and prev_enabled:
                    current_page -= 1
                elif next_btn.collidepoint(event.pos) and next_enabled:
                    current_page += 1
                elif back_btn.collidepoint(event.pos):
                    return
        
        pygame.display.flip()
        clock.tick(30)


def main_menu():
    screen_width = 1280
    screen_height = 920
    button_width = 300
    button_height = 60
    button_spacing = 20
    
    button_x = (screen_width - button_width) // 2
    
    title_y = 200
    first_button_y = 300  
    
    buttons = [
        pygame.Rect(button_x, first_button_y + i * (button_height + button_spacing), button_width, button_height)
        for i in range(5)  
    ]

    while True:
        draw_background(screen)

        title_shadow_offset = 2
        title_rect = pygame.Rect(0, title_y, screen_width, 60)
        shadow_rect = title_rect.copy()
        shadow_rect.x += title_shadow_offset
        shadow_rect.y += title_shadow_offset
        
        title_font = pygame.font.Font(None, 96)
        draw_text(screen, "Hangman Game", (100, 100, 100), shadow_rect, title_font)

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
                            about_game()
                        elif i == 4:
                            pygame.quit()
                            sys.exit()

        for i, button in enumerate(buttons):
            is_hovered = button.collidepoint(pygame.mouse.get_pos())
            
            # Button colors
            if i == 4:  
                base_color = (200, 100, 100)  
                hover_color = (220, 120, 120)  
                text_color = (255, 255, 255) 
            else:
                base_color = (100, 150, 255) if not is_hovered else (120, 170, 255)  
                text_color = (255, 255, 255)  
            
            pygame.draw.rect(screen, base_color, button, border_radius=10)
            
            border_color = (70, 120, 225) if not is_hovered else (90, 140, 245)
            pygame.draw.rect(screen, border_color, button, 2, border_radius=10)
            
            labels = ["AI Mode", "Single Player", "Multiplayer", "About Game", "Quit"]
            draw_text(screen, labels[i], text_color, button, font)

        pygame.display.flip()
        clock.tick(30)


def ai_mode():
    selection_active = True
    while selection_active:
        draw_background(screen)
        
        # Draw title
        title_rect = pygame.Rect(0, 200, 1280, 60) 
        draw_text(screen, "Select AI Mode", BLACK, title_rect, pygame.font.Font(None, 72))
        
        button_width = 600
        button_x = (1280 - button_width) // 2  # Center horizontally
        
        option1_rect = pygame.Rect(button_x, 350, button_width, 80) 
        option2_rect = pygame.Rect(button_x, 450, button_width, 80) 
        
        for rect, text, is_hovered in [
            (option1_rect, "1. Enter your own word for AI to guess", option1_rect.collidepoint(pygame.mouse.get_pos())),
            (option2_rect, "2. AI selects and guesses a random word", option2_rect.collidepoint(pygame.mouse.get_pos()))
        ]:
            color = (120, 170, 255) if is_hovered else (100, 150, 255)
            pygame.draw.rect(screen, color, rect, border_radius=15)
            pygame.draw.rect(screen, (70, 120, 225), rect, 3, border_radius=15)
            draw_text(screen, text, WHITE, rect, pygame.font.Font(None, 40))
        
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
                    play_ai_mode(True)
                elif option2_rect.collidepoint(event.pos):
                    selection_active = False
                    play_ai_mode(False)
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
        instruction_screen = True
        while instruction_screen:
            draw_background(screen)
            title_rect = pygame.Rect(150, 100, 1024, 60)
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
                draw_text(screen, text, BLACK, pygame.Rect(350, 200 + i*40, 600, 30), small_font)
            
            continue_btn = pygame.Rect(550, 600, 200, 50)
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
        center_x = 640  
        info_y = 50
        info_spacing = 45  

        # Show the word that AI needs to guess 
        if not user_entered_word:
            draw_text(screen, f"Word to guess: {game.word}", BLUE, 
                     pygame.Rect(0, info_y, 1280, 50), pygame.font.Font(None, 42))
            info_y += info_spacing + 10

        # Game information
        info_y += 20
        # Word display 
        word_rect = pygame.Rect(center_x - 200, info_y, 400, 60)
        pygame.draw.rect(screen, BLACK, word_rect, 2)
        draw_text(screen, game.get_display_word(), BLACK, word_rect, pygame.font.Font(None, 48))
        
        # Guessed letters section 
        info_y += info_spacing + 30
        guessed_text = "Guessed Letters: "
        guessed_surface = pygame.font.Font(None, 36).render(guessed_text, True, BLACK)
        screen.blit(guessed_surface, (center_x - 200, info_y))
        
        letter_x = center_x - 200 + guessed_surface.get_width()
        letter_spacing = 25 
        for letter in sorted(game.guessed_letters):
            color = GREEN if letter in game.correct_letters else RED
            letter_surface = pygame.font.Font(None, 36).render(letter, True, color)
            screen.blit(letter_surface, (letter_x, info_y))
            letter_x += letter_spacing

        # AI thinking and message display
        info_y += info_spacing + 20
        if message:
            draw_text(screen, message, RED if "wrong" in message.lower() else GREEN, 
                     pygame.Rect(0, info_y, 1280, 50), pygame.font.Font(None, 36))

        # Statistics display
        info_y += info_spacing
        draw_text(screen, f"AI Guesses: {ai_guesses}", BLACK, 
                 pygame.Rect(0, info_y, 1280, 40), pygame.font.Font(None, 36))
        
        info_y += info_spacing - 10
        draw_text(screen, f"Wrong Guesses: {game.wrong_guesses}", 
                 RED if game.wrong_guesses > 0 else BLACK,
                 pygame.Rect(0, info_y, 1280, 40), pygame.font.Font(None, 36))

        back_btn = pygame.Rect(center_x - 40, info_y + info_spacing + 20, 80, 40)
        pygame.draw.rect(screen, (100, 150, 255), back_btn, border_radius=10)
        pygame.draw.rect(screen, (70, 120, 225), back_btn, 2, border_radius=10)
        draw_text(screen, "Back", WHITE, back_btn, pygame.font.Font(None, 36))

        game.update_possible_words()
        ai_guess = game.ai_guess()
        if ai_guess and game.wrong_guesses < game.max_attempts:
            result = game.guess_letter(ai_guess)
            ai_guesses += 1
            pygame.time.wait(1000)  # Delay for better visualization
            message = f"AI guessed '{ai_guess}' - {'Correct!' if result == 'correct' else 'Wrong!'}"
            
            if game.is_word_guessed():
                message = f"AI won! Word guessed in {ai_guesses} attempts!"
                game_active = False
            elif game.wrong_guesses >= game.max_attempts:
                message = f"AI lost! The word was '{game.word}'"
                game_active = False
        else:
            if game.wrong_guesses >= game.max_attempts:
                message = f"AI lost! The word was '{game.word}'"
            else:
                message = "AI couldn't find a letter to guess!"
            game_active = False

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN and back_btn.collidepoint(event.pos):
                return

        pygame.display.flip()
        clock.tick(2)  # Slowed down for better visualization

    # Game over screen
    while True:
        draw_background(screen)
        draw_hangman(screen, game.wrong_guesses)

        info_y = 150
        info_spacing = 45

        # Game result title
        draw_text(screen, "Game Over!", BLUE, 
                 pygame.Rect(0, info_y, 1280, 60), pygame.font.Font(None, 48))
        
        info_y += info_spacing + 20
        # Final word display
        word_rect = pygame.Rect(center_x - 200, info_y, 400, 60)
        pygame.draw.rect(screen, BLACK, word_rect, 2)
        draw_text(screen, game.word, BLACK, word_rect, pygame.font.Font(None, 48))

        # Game statistics 
        info_y += info_spacing + 30
        stats = [
            (f"Total Guesses: {ai_guesses}", BLACK),
            (f"Correct Guesses: {len(game.correct_letters)}", GREEN),
            (f"Wrong Guesses: {game.wrong_guesses}", RED),
            (message, BLUE)
        ]

        for stat, color in stats:
            draw_text(screen, stat, color, 
                     pygame.Rect(0, info_y, 1280, 40), pygame.font.Font(None, 36))
            info_y += info_spacing

        back_btn = pygame.Rect(center_x - 40, info_y + 20, 80, 40)
        pygame.draw.rect(screen, (100, 150, 255), back_btn, border_radius=10)
        pygame.draw.rect(screen, (70, 120, 225), back_btn, 2, border_radius=10)
        draw_text(screen, "Back", WHITE, back_btn, pygame.font.Font(None, 36))

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
        draw_background(screen) 
        # Move hangman drawing to the left
        draw_hangman(screen, game.wrong_guesses)

        # Game info section
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
        
        cat_btn_width = max(len(cat) * 10 + 20 for cat in category_list)
        cat_spacing = 20 
        
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
        diff_btn_width = 100  
        diff_spacing = 20  
        
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
            btn_color = BLACK if game.score >= 25 and game_active else GRAY
            pygame.draw.rect(screen, btn_color, hint_btn, 2)
            draw_text(screen, "Hint", btn_color, hint_btn, small_font)

        new_game_btn = pygame.Rect(info_x + 100, 400, 120, 30)
        pygame.draw.rect(screen, BLUE, new_game_btn, 2)
        draw_text(screen, "New Game", BLUE, new_game_btn, small_font)

        if game_active:
            # Draw input box
            input_box = pygame.Rect(info_x, 450, 200, 32)
            enter_button = pygame.Rect(info_x + 220, 450, 80, 32)
            
            # Draw input elements
            pygame.draw.rect(screen, WHITE, input_box, 2)
            pygame.draw.rect(screen, (100, 150, 255), enter_button)
            pygame.draw.rect(screen, (70, 120, 225), enter_button, 2)
            
            # Draw text
            txt_surface = font.render(input_text, True, BLACK)
            enter_text = font.render("Enter", True, BLACK)
            note_text = small_font.render("Type letter + Enter/click button", True, GRAY)
            
            # Position text
            screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
            screen.blit(enter_text, (enter_button.x + 10, enter_button.y + 5))
            screen.blit(note_text, (info_x, 490))

        back_btn = pygame.Rect(900, 700, 80, 30)
        pygame.draw.rect(screen, BLACK, back_btn, 2)
        draw_text(screen, "Back", BLACK, back_btn, small_font)

        # Handle events in single player mode
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Get mouse position
                mouse_pos = pygame.mouse.get_pos()
                # Check if enter button is clicked
                if enter_button.collidepoint(mouse_pos):
                    if len(input_text) == 1 and input_text.isalpha():
                        guess = input_text.upper()
                        if guess not in game.guessed_letters:
                            result = game.guess_letter(guess)
                            if result == 'correct':
                                message = "Correct guess!"
                            elif result == 'incorrect':
                                message = "Wrong guess! Try again."
                            else:
                                message = f"Letter '{input_text}' was already guessed!"
                        input_text = ''  # Clear input box after guess
            if event.type == pygame.KEYDOWN:
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
                mouse_pos = pygame.mouse.get_pos()
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
                    if hint_btn.collidepoint(event.pos) and game.score >= 25 and game_active:
                        hint = game.use_hint()
                        if hint:
                            message = hint
                        else:
                            message = "No hints available or not enough points (need 25 points)"
                
                if new_game_btn.collidepoint(event.pos):
                    start_new_game()
                elif back_btn.collidepoint(event.pos):
                    return

        if game.is_word_guessed() and game_active:
            game.game_time = game.get_time_played()
            final_score = game.calculate_final_score()
            
            # Display score breakdown
            score_lines = [
                f"Base Score: {game.score}",
                f"Time Bonus (faster = more points): +{max(0, 100 - game.game_time) // 10}",
                f"Remaining Attempts Bonus: +{(game.max_attempts - game.wrong_guesses) * 10}",
                f"Word Length Bonus: +{len(game.word) * 2}",
            ]
            
            if game.hints_used == 0:
                score_lines.append("No-Hint Bonus: +50")
            if game.wrong_guesses == 0:
                score_lines.append("Perfect Game Bonus: +100")
                
            score_lines.append(f"Final Score: {final_score}")
            
            # Create a semi-transparent overlay
            overlay = pygame.Surface((1280, 920))
            overlay.fill((255, 255, 255))
            overlay.set_alpha(230)
            screen.blit(overlay, (0, 0))
            
            # Draw score breakdown
            title = "Score Breakdown"
            title_y = 250
            line_height = 40
            
            # Draw title
            draw_text(screen, title, BLUE, pygame.Rect(0, title_y, 1280, 50), title_font)
            
            # Draw each score line
            for i, line in enumerate(score_lines):
                draw_text(screen, line, BLACK, 
                         pygame.Rect(0, title_y + 80 + i * line_height, 1280, 40), 
                         font)
            
            # Add continue button
            continue_btn = pygame.Rect(540, 650, 200, 50)
            pygame.draw.rect(screen, (100, 150, 255), continue_btn, border_radius=10)
            pygame.draw.rect(screen, (70, 120, 225), continue_btn, 2, border_radius=10)
            draw_text(screen, "Continue", WHITE, continue_btn, font)
            
            win_sound.play()
            game_active = False
            
            # Wait for continue button click
            waiting_for_click = True
            while waiting_for_click:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == MOUSEBUTTONDOWN:
                        if continue_btn.collidepoint(event.pos):
                            waiting_for_click = False
                            start_new_game()
                pygame.display.flip()
                clock.tick(30)
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
    round_details = {player1: [], player2: []}  # Store detailed score for each round
    message = ''
    
    # Load all words with categories and difficulties
    categories = load_words("words.txt")
    hints_data = load_words_with_hints("words_with_hints.txt")
    
    for current_round in range(rounds):
        # Select random category and difficulty for player 1
        valid_categories = [cat for cat in categories.keys() if cat not in ['EXPERT', 'RANDOM']]
        p1_category = random.choice(valid_categories)
        p1_difficulty = random.choice(['EASY', 'MEDIUM', 'HARD'])
        
        # Get word for player 1
        p1_word = random.choice(categories[p1_category][p1_difficulty])
        p1_hint = hints_data.get(p1_category, {}).get(p1_word, None)
        
        # For player 2, use same difficulty but different category
        p2_category = random.choice([cat for cat in valid_categories if cat != p1_category])
        p2_word = random.choice(categories[p2_category][p1_difficulty])
        p2_hint = hints_data.get(p2_category, {}).get(p2_word, None)
        
        for current_player, word, hint, category in [(player1, p1_word, p1_hint, p1_category),
                                                   (player2, p2_word, p2_hint, p2_category)]:
            game = HangmanGame(word, category, p1_difficulty, hint)
            input_text = ''
            game_active = True

            while game_active:
                draw_background(screen)
                draw_hangman(screen, game.wrong_guesses)

                # Display game information 
                center_x = 640  
                center_y = 460
                info_y = 80
                info_spacing = 45 

                # Player scores 
                score_y = info_y
                draw_text(screen, f"{player1}: {scores[player1]}", BLACK, 
                         pygame.Rect(center_x - 300, score_y, 200, 50))
                draw_text(screen, f"{player2}: {scores[player2]}", BLACK, 
                         pygame.Rect(center_x + 100, score_y, 200, 50))
                
                # Current player and round info
                info_y += info_spacing + 20
                draw_text(screen, f"Current Player: {current_player}", BLUE, 
                         pygame.Rect(0, info_y, 1280, 50))
                
                info_y += info_spacing
                draw_text(screen, f"Round: {current_round + 1}/{rounds}", BLACK, 
                         pygame.Rect(0, info_y, 1280, 50))
                
                info_y += info_spacing
                draw_text(screen, f"Category: {category}", BLACK, 
                         pygame.Rect(0, info_y, 1280, 50))
                
                info_y += info_spacing
                difficulty_color = (GREEN if p1_difficulty == 'EASY' else 
                                 YELLOW if p1_difficulty == 'MEDIUM' else 
                                 RED)
                draw_text(screen, f"Difficulty: {p1_difficulty}", difficulty_color, 
                         pygame.Rect(0, info_y, 1280, 50))

                info_y += info_spacing + 20
                word_rect = pygame.Rect(center_x - 200, info_y, 400, 60)
                pygame.draw.rect(screen, BLACK, word_rect, 2)
                draw_text(screen, game.get_display_word(), BLACK, word_rect, pygame.font.Font(None, 48))

                info_y += info_spacing + 30
                guessed_text = "Guessed Letters: "
                guessed_surface = font.render(guessed_text, True, BLACK)
                screen.blit(guessed_surface, (center_x - 200, info_y))
                
                letter_x = center_x - 200 + guessed_surface.get_width()
                letter_spacing = 25 
                for letter in sorted(game.guessed_letters):
                    color = GREEN if letter in game.correct_letters else RED
                    letter_surface = font.render(letter, True, color)
                    screen.blit(letter_surface, (letter_x, info_y))
                    letter_x += letter_spacing

                info_y += info_spacing
                draw_text(screen, message, RED, pygame.Rect(0, info_y, 1280, 50))

                if game_active:
                    input_box = pygame.Rect(center_x - 150, center_y + 50, 140, 40) 
                    pygame.draw.rect(screen, BLACK, input_box, 2)
                    text_surface = font.render(input_text, True, BLACK)
                    screen.blit(text_surface, (input_box.x + 5, input_box.y + 5))

                    enter_btn = pygame.Rect(input_box.x + input_box.width + 10, input_box.y, 100, 40)
                    pygame.draw.rect(screen, BLACK, enter_btn, 2)
                    draw_text(screen, "Enter", BLACK, enter_btn, small_font)

                    instruction_text = "Type a letter and press Enter or click Enter button"
                    instruction_surface = small_font.render(instruction_text, True, BLACK)
                    screen.blit(instruction_surface, (input_box.x, input_box.y + 50))

                    hint_btn = pygame.Rect(center_x - 110, input_box.y + 100, 100, 40)  
                    back_btn = pygame.Rect(center_x + 10, input_box.y + 100, 100, 40)  
                    pygame.draw.rect(screen, BLACK, hint_btn, 2)
                    pygame.draw.rect(screen, BLACK, back_btn, 2)
                    draw_text(screen, "Hint", BLACK, hint_btn, small_font)
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
                            if game.score >= 25:
                                hint = game.use_hint()
                                if hint:
                                    message = hint
                                else:
                                    message = "No hints left!"
                            else:
                                message = "Need 25 points for hint!"
                        if back_btn.collidepoint(event.pos):
                            return
                        if enter_btn.collidepoint(event.pos):
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

                if game.is_word_guessed() or game.wrong_guesses >= game.max_attempts:
                    game.game_time = game.get_time_played()
                    final_score = game.calculate_final_score()
                    
                    # Store round details
                    round_info = {
                        'word': game.word,
                        'base_score': game.score,
                        'time_bonus': max(0, 100 - game.game_time) // 10,
                        'attempts_bonus': (game.max_attempts - game.wrong_guesses) * 10,
                        'word_length_bonus': len(game.word) * 2,
                        'no_hint_bonus': 50 if game.hints_used == 0 else 0,
                        'perfect_bonus': 100 if game.wrong_guesses == 0 else 0,
                        'final_score': final_score
                    }
                    round_details[current_player].append(round_info)
                    scores[current_player] += final_score
                    
                    # Show round end screen
                    overlay = pygame.Surface((1280, 920))
                    overlay.fill((255, 255, 255))
                    overlay.set_alpha(230)
                    screen.blit(overlay, (0, 0))
                    
                    # Show word and result
                    result_text = "Correct!" if game.is_word_guessed() else "Game Over!"
                    draw_text(screen, f"{result_text} The word was: {game.word}", BLACK, pygame.Rect(0, 250, 1280, 50), font)
                    
                    # Show score breakdown
                    score_lines = [
                        f"Base Score: {game.score}",
                        f"Time Bonus: +{round_info['time_bonus']}",
                        f"Remaining Attempts Bonus: +{round_info['attempts_bonus']}",
                        f"Word Length Bonus: +{round_info['word_length_bonus']}"
                    ]
                    
                    if round_info['no_hint_bonus'] > 0:
                        score_lines.append("No-Hint Bonus: +50")
                    if round_info['perfect_bonus'] > 0:
                        score_lines.append("Perfect Game Bonus: +100")
                    
                    score_lines.append(f"Round Total: {final_score}")
                    
                    for i, line in enumerate(score_lines):
                        draw_text(screen, line, BLACK, pygame.Rect(0, 350 + i * 40, 1280, 40), font)
                    
                    # Continue button
                    continue_btn = pygame.Rect(540, 650, 200, 50)
                    pygame.draw.rect(screen, (100, 150, 255), continue_btn, border_radius=10)
                    pygame.draw.rect(screen, (70, 120, 225), continue_btn, 2, border_radius=10)
                    draw_text(screen, "Continue", WHITE, continue_btn, font)
                    
                    if game.is_word_guessed():
                        win_sound.play()
                    else:
                        lose_sound.play()
                        
                    game_active = False
                    waiting_for_click = True
                    
                    while waiting_for_click:
                        for event in pygame.event.get():
                            if event.type == QUIT:
                                pygame.quit()
                                sys.exit()
                            if event.type == MOUSEBUTTONDOWN:
                                if continue_btn.collidepoint(event.pos):
                                    waiting_for_click = False
                        pygame.display.flip()
                        clock.tick(30)

                pygame.display.flip()
                clock.tick(30)

    # Final score screen
    screen.fill(WHITE)
    draw_text(screen, "Final Score Breakdown", BLUE, pygame.Rect(0, 50, 1280, 50), title_font)
    
    # Calculate totals for each player
    player_totals = {}
    for player in [player1, player2]:
        totals = {
            'base_score': 0,
            'time_bonus': 0,
            'attempts_bonus': 0,
            'word_length_bonus': 0,
            'no_hint_bonus': 0,
            'perfect_bonus': 0,
            'final_score': 0,
            'words': []  # Keep track of words for display
        }
        
        for round_info in round_details[player]:
            totals['base_score'] += round_info['base_score']
            totals['time_bonus'] += round_info['time_bonus']
            totals['attempts_bonus'] += round_info['attempts_bonus']
            totals['word_length_bonus'] += round_info['word_length_bonus']
            totals['no_hint_bonus'] += round_info['no_hint_bonus']
            totals['perfect_bonus'] += round_info['perfect_bonus']
            totals['final_score'] += round_info['final_score']
            totals['words'].append(round_info['word'])
            
        player_totals[player] = totals

    # Display side by side comparison
    left_x = 150
    right_x = 680
    y_pos = 150
    column_width = 450

    # Display player names
    draw_text(screen, player1, BLUE, pygame.Rect(left_x, y_pos, column_width, 40), font)
    draw_text(screen, player2, BLUE, pygame.Rect(right_x, y_pos, column_width, 40), font)
    y_pos += 50

    # Display words used
    for player, x_pos in [(player1, left_x), (player2, right_x)]:
        words_text = "Words: " + ", ".join(player_totals[player]['words'])
        draw_text(screen, words_text, BLACK, pygame.Rect(x_pos, y_pos, column_width, 30), small_font)
    y_pos += 50

    # Display score components
    score_components = [
        ('Base Score', 'base_score'),
        ('Time Bonuses', 'time_bonus'),
        ('Attempts Bonuses', 'attempts_bonus'),
        ('Word Length Bonuses', 'word_length_bonus'),
        ('No-Hint Bonuses', 'no_hint_bonus'),
        ('Perfect Game Bonuses', 'perfect_bonus')
    ]

    for label, key in score_components:
        for player, x_pos in [(player1, left_x), (player2, right_x)]:
            if player_totals[player][key] > 0:
                text = f"{label}: +{player_totals[player][key]}"
                draw_text(screen, text, BLACK, pygame.Rect(x_pos, y_pos, column_width, 30), small_font)
        y_pos += 35

    # Display final totals with bigger font and emphasis
    y_pos += 20
    for player, x_pos in [(player1, left_x), (player2, right_x)]:
        total_text = f"Final Total: {player_totals[player]['final_score']}"
        draw_text(screen, total_text, BLUE, pygame.Rect(x_pos, y_pos, column_width, 40), font)

    y_pos += 80
    winner = max(scores, key=scores.get)
    draw_text(screen, f"Winner: {winner}!", GREEN, pygame.Rect(0, y_pos, 1280, 50), title_font)
    
    menu_btn = pygame.Rect(540, 800, 200, 50)  
    pygame.draw.rect(screen, BLUE, menu_btn, border_radius=10)
    draw_text(screen, "Main Menu", WHITE, menu_btn, font)
    
    pygame.display.flip()
    
    while True:
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN and menu_btn.collidepoint(pygame.mouse.get_pos()):
                return
            if event.type == QUIT:
                pygame.quit()
                sys.exit()


if __name__ == "__main__":
    main_menu()
