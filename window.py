"""Pygame window and main event loop for Blackjack.

This module handles the display, user input, and window management.
Game logic is delegated to game.py (separation of concerns).

Key Components:
- DialogButton: Reusable clickable button with hover state
- OutOfMoneyDialog: Modal dialog when balance <= 0
- GameModeScreen: Mode selection screen (Practice/Classic/Custom)
- BlackjackWindow: Main game window, event handler, and render loop

Window States:
- "mode_select": Showing game mode selection buttons
- "game": Active gameplay

Event Flow:
1. User presses key/clicks mouse → handle_events()
2. Events route to appropriate handler (dialog, mode screen, or game input)
3. Game state updates in update()
4. Screen redraws in render()
5. Loop repeats at 60 FPS

Potential Break Points:
- game_state strings must match game.py (betting/playing/result/etc)
- pygame initialization must happen before creating window
- Event handling order matters (dialogs checked first)
- ESC key returns to mode selection (clears all state)

Dependencies:
- pygame: For display and input
- game.BlackjackGame: For game logic
"""

import os
import cards
import pygame
import sys
from game import BlackjackGame



class DialogButton:
    """Simple button for dialogs and menus.
    
    Features:
    - Clickable rectangular button
    - Hover state detection (color changes on mouse over)
    - Custom callback function execution on click
    - Renders with different color when hovered
    
    Used by:
    - GameModeScreen (3 mode selection buttons)
    - OutOfMoneyDialog ("Get More Money" button)
    
    BREAK POINT: If callback is None, clicking will crash.
    """

    def __init__(self, x: int, y: int, width: int, height: int, text: str, callback):
        """Initialize button.

        Args:
            x, y: Top-left position in pixels
            width, height: Button dimensions in pixels
            text: Button label string
            callback: Function to call when clicked (must be callable)
        
        BREAK POINT: callback must be a function, not None
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.hovered = False

    def handle_event(self, event):
        """Handle mouse motion and click events.
        
        Updates hover state on mouse motion.
        Calls callback on mouse button down if button is hovered.
        
        Args:
            event: Pygame event object
        """
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered:
                self.callback()

    def on_click(self):
        """Trigger the button's callback (programmatic click).
        
        Used when clicking is simulated (e.g., by GameModeScreen.handle_click).
        """
        self.callback()

    def render(self, screen, font, color_button, color_hover, color_text):
        """Render button to screen.
        
        Args:
            screen: Pygame surface to draw to
            font: Font object for text rendering
            color_button: RGB tuple for normal button color
            color_hover: RGB tuple for hovered button color
            color_text: RGB tuple for text color
        
        Renders:
        1. Rectangle background (color changes on hover)
        2. Border outline
        3. Centered text
        """
        # Choose color based on hover state
        color = color_hover if self.hovered else color_button
        # Draw filled rectangle for button background
        pygame.draw.rect(screen, color, self.rect)
        # Draw border around button (2 pixel width)
        pygame.draw.rect(screen, color_text, self.rect, 2)
        # Render text and center it on button
        text_surf = font.render(self.text, True, color_text)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)


class OutOfMoneyDialog:
    """Dialog shown when player runs out of money."""

    def __init__(self, screen, game, width: int = 500, height: int = 250):
        """Initialize dialog.

        Args:
            screen: Pygame screen.
            game: BlackjackGame instance.
            width, height: Dialog size.
        """
        self.screen = screen
        self.game = game
        self.width = width
        self.height = height
        self.x = (screen.get_width() - width) // 2
        self.y = (screen.get_height() - height) // 2

        # Colors
        self.color_bg = (40, 40, 40)
        self.color_text = (255, 255, 255)
        self.color_button = (50, 100, 200)
        self.color_button_hover = (100, 150, 255)

        # Fonts
        self.font_title = pygame.font.Font(None, 40)
        self.font_message = pygame.font.Font(None, 28)
        self.font_button = pygame.font.Font(None, 24)

        # Button
        button_width = 200
        button_height = 50
        button_x = self.x + (self.width - button_width) // 2
        button_y = self.y + self.height - 80
        self.button = DialogButton(button_x, button_y, button_width, button_height,
                                    "Get More Money", self.on_button_click)

    def on_button_click(self):
        """Handle button click."""
        self.game.reset_balance_on_broke()

    def handle_event(self, event):
        """Handle events."""
        self.button.handle_event(event)

    def render(self):
        """Render dialog."""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Dialog background
        pygame.draw.rect(self.screen, self.color_bg,
                         (self.x, self.y, self.width, self.height))
        pygame.draw.rect(self.screen, self.color_text,
                         (self.x, self.y, self.width, self.height), 3)

        # Title
        title_text = self.font_title.render("You Ran Out of Money!", True, (255, 100, 100))
        title_rect = title_text.get_rect(center=(self.x + self.width // 2, self.y + 40))
        self.screen.blit(title_text, title_rect)

        # Message
        msg_text = self.font_message.render("Click the button below for more chips.", True, self.color_text)
        msg_rect = msg_text.get_rect(center=(self.x + self.width // 2, self.y + 100))
        self.screen.blit(msg_text, msg_rect)

        # Button
        self.button.render(self.screen, self.font_button, self.color_button,
                          self.color_button_hover, self.color_text)


class GameModeScreen:
    """Screen for selecting game mode."""

    def __init__(self, screen):
        """Initialize game mode selection screen.

        Args:
            screen: Pygame screen.
        """
        self.screen = screen
        self.selected_mode = None

        # Colors
        self.color_bg = (0, 100, 0)
        self.color_text = (255, 255, 255)
        self.color_button = (50, 50, 150)
        self.color_button_hover = (100, 100, 200)

        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)

        # Buttons
        button_width = 250
        button_height = 60
        center_x = screen.get_width() // 2

        y_offset = 150
        self.btn_practice = DialogButton(
            center_x - button_width // 2, y_offset, button_width, button_height,
            "Practice Mode (No Wagers)", lambda: self._select("practice")
        )
        y_offset += 120
        self.btn_classic = DialogButton(
            center_x - button_width // 2, y_offset, button_width, button_height,
            "Classic Mode ($2000 -> $25000)", lambda: self._select("classic")
        )
        y_offset += 120
        self.btn_custom = DialogButton(
            center_x - button_width // 2, y_offset, button_width, button_height,
            "Custom Mode (Set Goals)", lambda: self._select("custom")
        )

        self.buttons = [self.btn_practice, self.btn_classic, self.btn_custom]

    def _select(self, mode: str):
        """Set selected mode."""
        self.selected_mode = mode

    def handle_event(self, event):
        """Handle events."""
        for btn in self.buttons:
            btn.handle_event(event)

    def handle_click(self, pos):
        """Handle mouse click and return selected mode if clicked."""
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                btn.on_click()
                return self.selected_mode
        return None

    def render(self):
        """Render game mode selection screen."""
        self.screen.fill(self.color_bg)

        # Title
        title_text = self.font_large.render("Blackjack", True, self.color_text)
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 50))
        self.screen.blit(title_text, title_rect)

        # Subtitle
        subtitle_text = self.font_medium.render("Select Game Mode", True, self.color_text)
        subtitle_rect = subtitle_text.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(subtitle_text, subtitle_rect)

        # Render buttons
        for btn in self.buttons:
            btn.render(self.screen, self.font_medium, self.color_button,
                      self.color_button_hover, self.color_text)

        pygame.display.flip()


class BlackjackWindow:
    """Pygame window for Blackjack game."""

    def __init__(self, width: int = 800, height: int = 600, title: str = "Blackjack",
                 mode: str = "classic", starting_balance: int = 2000, target_balance: int = 25000):
        """Initialize the window.

        Args:
            width: Window width in pixels.
            height: Window height in pixels.
            title: Window title.
            mode: Game mode ("practice", "classic", or "custom").
            starting_balance: Player's starting balance.
            target_balance: Goal balance to win.
        """
        pygame.init()
        self.width = width
        self.height = height
        self.title = title
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = 60

        # Fonts for text rendering
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)

        # Colors
        self.color_bg = (0, 100, 0)  # Green felt
        self.color_text = (255, 255, 255)  # White text
        self.color_button = (50, 50, 150)  # Blue buttons
        self.color_button_hover = (100, 100, 200)
        self.color_text_dark = (0, 0, 0)

        # Game instance
        self.game = BlackjackGame(starting_balance=starting_balance, target_balance=target_balance, mode=mode)

        # Input state
        self.current_input = ""
        self.input_active = False
        
        # Dialog state
        self.out_of_money_dialog = None
        
        # Screen state: "mode_select" -> "game"
        self.screen_state = "mode_select"
        self.game_mode_screen = GameModeScreen(self.screen)

        # Card images: load PNGs for card faces and a back image
        self.card_size = (72, 96)
        self.card_images = {}
        self.card_back_image = None
        try:
            assets_path = os.path.join(os.path.dirname(__file__), 'pygame_cards-0.1', 'cards', 'PNG')
            for fname in os.listdir(assets_path):
                if not fname.lower().endswith('.png'):
                    continue
                key = fname[:-4]  # strip .png
                img = pygame.image.load(os.path.join(assets_path, fname)).convert_alpha()
                img = pygame.transform.scale(img, self.card_size)
                # Store backs as a special key
                if 'back' in fname.lower():
                    self.card_back_image = img
                else:
                    self.card_images[key] = img
        except Exception as e:
            # If loading images fails, keep dict empty and fall back to text rendering
            print(f"Failed to load card images: {e}")

    def handle_events(self):
        """Handle pygame events (quit, keyboard input, etc.)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # If on mode selection screen
            if self.screen_state == "mode_select":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    selected_mode = self.game_mode_screen.handle_click(event.pos)
                    if selected_mode:
                        # Initialize game with selected mode
                        starting_balance = 2000 if selected_mode == "classic" else 0 if selected_mode == "practice" else 0
                        target_balance = 25000 if selected_mode == "classic" else 0 if selected_mode == "practice" else 0
                        
                        self.game = BlackjackGame(starting_balance=starting_balance, 
                                               target_balance=target_balance, 
                                               mode=selected_mode)
                        self.screen_state = "game"
                        self.current_input = ""
                        self.input_active = False
                continue

            # If out-of-money dialog is open, handle its events
            if self.out_of_money_dialog is not None:
                self.out_of_money_dialog.handle_event(event)
                continue

            elif event.type == pygame.KEYDOWN:
                # Game controls
                if event.key == pygame.K_h:
                    # Hit
                    if self.game.game_state == "playing":
                        action, msg = self.game.player_hit()
                        print(f"[HIT] {msg}")

                elif event.key == pygame.K_s:
                    # Stand
                    if self.game.game_state == "playing":
                        action, msg = self.game.player_stand()
                        print(f"[STAND] {msg}")

                elif event.key == pygame.K_n:
                    # New hand
                    if self.game.game_state == "result" or self.game.game_state == "betting":
                        self.game.reset_for_new_hand()
                        print("[NEW HAND] Ready for new game.")

                elif event.key == pygame.K_RETURN:
                    # Confirm bet (if currently inputting)
                    if self.input_active:
                        self._process_bet_input()

                elif event.key == pygame.K_BACKSPACE:
                    # Delete character from input
                    if self.input_active:
                        self.current_input = self.current_input[:-1]

                elif event.unicode.isdigit():
                    # Add digit to bet input
                    if self.input_active and len(self.current_input) < 5:
                        self.current_input += event.unicode

                elif event.key == pygame.K_ESCAPE:
                    # Return to mode selection screen
                    self.screen_state = "mode_select"
                    self.input_active = False
                    self.current_input = ""
                    self.out_of_money_dialog = None
                    self.game_mode_screen = GameModeScreen(self.screen)
                    print("[ESC] Returning to mode selection...")

    def _process_bet_input(self):
        """Process the current bet input."""
        # In practice mode, skip betting
        if self.game.mode == "practice":
            success, msg = self.game.place_bet()
            print(f"[PRACTICE] {msg}")
            if success:
                self.game.deal_initial_hands()
                self.input_active = False
                self.current_input = ""
            return

        if not self.current_input:
            print("[BET] No amount entered.")
            return

        try:
            bet_amount = int(self.current_input)
            success, msg = self.game.place_bet(bet_amount)
            print(f"[BET] {msg}")

            if success:
                self.game.deal_initial_hands()
                self.input_active = False
                self.current_input = ""
            else:
                self.current_input = ""

        except ValueError:
            print("[BET] Invalid input.")
            self.current_input = ""

    def update(self):
        """Update game state (called each frame)."""
        # Skip updates if on mode select screen
        if self.screen_state == "mode_select":
            return
        
        # Check if out-of-money dialog should be shown
        if self.game.game_state == "out_of_money" and self.out_of_money_dialog is None:
            self.out_of_money_dialog = OutOfMoneyDialog(self.screen, self.game)

        # Close dialog if game state changed
        if self.out_of_money_dialog is not None and self.game.game_state != "out_of_money":
            self.out_of_money_dialog = None

        # Check if we need to start betting
        if self.game.game_state == "betting" and not self.input_active:
            print(f"\n--- New Hand ---")
            print(f"Balance: {self.game.balance}")
            print("Enter bet amount (press 'H' for Hit, 'S' for Stand, 'N' for New Hand, ESC to cancel):")
            self.input_active = True

    def render(self):
        """Render the game state to the screen."""
        # If on mode select screen, render that instead
        if self.screen_state == "mode_select":
            self.game_mode_screen.render()
            return

        self.screen.fill(self.color_bg)

        # Display balance and bet info
        balance_text = self.font_medium.render(f"Balance: ${self.game.balance}", True, self.color_text)
        bet_text = self.font_medium.render(f"Bet: ${self.game.current_bet}", True, self.color_text)
        self.screen.blit(balance_text, (20, 20))
        self.screen.blit(bet_text, (20, 60))

        # Display hands as images and text
        player_hand_text = self.font_small.render(self.game.get_player_hand_str(), True, self.color_text)
        if self.game.game_state == "playing":
            dealer_hand_text = self.font_small.render(
                self.game.get_dealer_hand_str(hide_hole_card=True), True, self.color_text
            )
        else:
            dealer_hand_text = self.font_small.render(
                self.game.get_dealer_hand_str(hide_hole_card=False), True, self.color_text
            )
        self.screen.blit(player_hand_text, (20, self.height - 100))
        self.screen.blit(dealer_hand_text, (20, 100))

        # Draw card images for dealer and player
        card_w, card_h = self.card_size
        # Dealer: top center
        dealer_cards = self.game.dealer_hand
        if dealer_cards:
            start_x = (self.width - (len(dealer_cards) * (card_w + 10))) // 2
            y = 100
            for idx, card in enumerate(dealer_cards):
                x = start_x + idx * (card_w + 10)
                # hide hole card while playing
                if self.game.game_state == 'playing' and idx == 1:
                    if self.card_back_image:
                        self.screen.blit(self.card_back_image, (x, y))
                    else:
                        pygame.draw.rect(self.screen, (200, 200, 200), (x, y, card_w, card_h))
                else:
                    key = getattr(card, 'image_key', None) and card.image_key()
                    surf = None
                    if key is not None:
                        surf = self.card_images.get(key)
                    if surf:
                        self.screen.blit(surf, (x, y))
                    else:
                        # fallback: render card text
                        t = self.font_small.render(str(card), True, self.color_text)
                        self.screen.blit(t, (x + 5, y + card_h//2 - 8))

        # Player: bottom center
        player_cards = self.game.player_hand
        if player_cards:
            start_x = (self.width - (len(player_cards) * (card_w + 10))) // 2
            y = self.height - card_h - 40
            for idx, card in enumerate(player_cards):
                x = start_x + idx * (card_w + 10)
                key = getattr(card, 'image_key', None) and card.image_key()
                surf = None
                if key is not None:
                    surf = self.card_images.get(key)
                if surf:
                    self.screen.blit(surf, (x, y))
                else:
                    t = self.font_small.render(str(card), True, self.color_text)
                    self.screen.blit(t, (x + 5, y + card_h//2 - 8))

        # Display game state message
        if self.game.result_message:
            msg_text = self.font_medium.render(self.game.result_message, True, (255, 215, 0))
            self.screen.blit(msg_text, (20, self.height // 2 - 30))

        # Display input prompt
        if self.input_active:
            prompt_text = self.font_small.render(f"Bet: ${self.current_input}_", True, self.color_text)
            self.screen.blit(prompt_text, (20, self.height // 2 + 50))

        # Display controls
        controls_y = self.height - 40
        controls_text = self.font_small.render("H: Hit | S: Stand | N: New Hand | ESC: Cancel", True, self.color_text)
        self.screen.blit(controls_text, (20, controls_y))

        # Display out-of-money dialog if active
        if self.out_of_money_dialog is not None:
            self.out_of_money_dialog.render()

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        print("=== Blackjack ===")
        print("Controls: H (Hit), S (Stand), N (New Hand), ESC (Cancel)")
        print()

        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.fps)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    window = BlackjackWindow(width=800, height=600, title="Blackjack")
    window.run()

