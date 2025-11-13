"""Blackjack game state machine and logic."""

from typing import Tuple, List
from cards import Deck
from hand_logic import calculate_hand_value, compare_hands


class BlackjackGame:
    """Main game state machine."""

    def __init__(self, starting_balance: int = 2000, target_balance: int = 25000, mode: str = "classic"):
        """Initialize the game."""
        self.starting_balance = starting_balance
        self.target_balance = target_balance
        self.mode = mode  # practice, classic, or custom
        self.balance = starting_balance
        self.current_bet = 0

        # Initialize fresh deck and shuffle
        self.deck = Deck()
        self.deck.shuffle()

        # Player and dealer hands
        self.player_hand: List = []
        self.dealer_hand: List = []

        # Game state: one of betting, dealing, playing, result, won, lost, out_of_money
        # DON'T modify these strings without updating all references in window.py
        self.game_state = "betting"
        self.result_message = ""

    def reset_for_new_hand(self):
        """Reset hands and state for a new round."""
        self.player_hand.clear()
        self.dealer_hand.clear()
        self.game_state = "betting"
        self.result_message = ""
        self.current_bet = 0

        # Reshuffle if deck is getting low (less than 10 cards)
        # This prevents card shortage during play
        if self.deck.remaining() < 10:
            self.deck = Deck()
            self.deck.shuffle()

    def place_bet(self, amount: int = 0) -> Tuple[bool, str]:
        """Place a bet for the current hand.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # In practice mode, no bet needed - just deal cards
        if self.mode == "practice":
            self.current_bet = 0
            self.game_state = "dealing"
            return True, "Practice mode: Dealing cards..."

        # Check if player has balance to bet (CRITICAL: prevents overbetting)
        if self.balance <= 0:
            return False, "Game over. Reset balance to play again."
        
        # Validate bet amount
        if amount <= 0:
            return False, "Bet must be greater than 0."
        if amount > self.balance:
            return False, f"Insufficient balance. You have {self.balance}."

        # Bet is valid - set it and move to dealing state
        self.current_bet = amount
        self.game_state = "dealing"
        return True, f"Bet placed: {amount}. Dealing cards..."

    def deal_initial_hands(self):
        """Deal two cards each to player and dealer.
        
        Also checks for natural blackjack (21 on first two cards).
        
        Natural Blackjack Rules:
        - Player 21 + Dealer not 21: Player wins (3:2 payout)
        - Dealer 21 + Player not 21: Dealer wins (player loses bet)
        - Both 21: Push (tie, no money exchanges)
        - Neither 21: Continue to "playing" state for hits/stands
        
        Payout Calculation:
        - Natural blackjack pays 3:2 (bet * 1.5)
        - Example: $100 bet × 1.5 = $150 win, $250 total returned
        
        State Transitions:
        - If natural blackjack detected: → "result" (game over)
        - Otherwise: → "playing" (player can hit/stand)
        
        BREAK POINTS:
        - If 21 check uses != instead of ==, logic fails
        - If 3:2 payout calculation changes, house goes broke
        - If state transitions change, dealer won't get their turn
        """
        # Deal 2 cards to each
        self.player_hand = [self.deck.deal(), self.deck.deal()]
        self.dealer_hand = [self.deck.deal(), self.deck.deal()]
        
        # Calculate initial totals
        player_total, _ = calculate_hand_value(self.player_hand)
        dealer_total, _ = calculate_hand_value(self.dealer_hand)
        
        # Check for natural blackjack (21 on first two cards)
        if player_total == 21 and dealer_total != 21:
            # Player has blackjack, dealer doesn't
            self.game_state = "result"
            self.result_message = "Natural Blackjack! Player wins!"
            # 3:2 payout for natural blackjack
            self.balance += int(self.current_bet * 1.5)
            
        elif dealer_total == 21 and player_total != 21:
            # Dealer has blackjack, player doesn't
            self.game_state = "result"
            self.result_message = "Dealer has Blackjack! Dealer wins."
            self.balance -= self.current_bet
            
        elif player_total == 21 and dealer_total == 21:
            # Both have blackjack
            self.game_state = "result"
            self.result_message = "Both have Blackjack! Push."
            # Balance unchanged on push
            
        else:
            # No natural blackjack - proceed to normal play
            self.game_state = "playing"

    def player_hit(self) -> Tuple[str, str]:
        """Player takes another card.
        
        Can only hit during "playing" state.
        Checks for bust after drawing.
        
        Returns:
            Tuple of (action_result: str, message: str)
            - action_result: "hit" (success), "bust", or "invalid" (wrong state)
            - message: Descriptive text for display
        
        State Transitions:
        - Valid hit, not busted: stays in "playing"
        - Valid hit, busted (> 21): → "result" (game over, player loses)
        - Invalid state: stays current (error shown to player)
        
        Bust Logic:
        - Player total > 21: Immediate loss, dealer doesn't need to play
        - Balance reduced by current_bet
        
        BREAK POINTS:
        - If > 21 check changes to >=, hard totals fail
        - If state != "playing" check is removed, player hits in wrong state
        - If balance -= current_bet is removed, player doesn't lose money
        """
        # Only allow hitting during active play
        if self.game_state != "playing":
            return "invalid", "Cannot hit now."

        # Draw a card
        self.player_hand.append(self.deck.deal())
        player_total, _ = calculate_hand_value(self.player_hand)

        # Check if player busted
        if player_total > 21:
            self.game_state = "result"
            self.result_message = f"Player busts with {player_total}. Dealer wins."
            self.balance -= self.current_bet
            return "bust", self.result_message

        # Hit succeeded, still under 21
        return "hit", f"Hit! New total: {player_total}"

    def player_stand(self) -> Tuple[str, str]:
        """Player stands; dealer plays out their hand.
        
        Dealer follows blackjack rules:
        - Hit on 16 or less
        - Stand on 17 or higher (hard or soft)
        - Note: This game uses "soft 17 stand" (dealer stands on soft 17)
        
        After dealer finishes:
        - Compare hands using compare_hands()
        - Update balance based on outcome
        - Check for win condition (balance >= target_balance)
        - Check for loss condition (balance <= 0)
        
        Returns:
            Tuple of (action_result: str, message: str)
            - action_result: "stand"
            - message: Descriptive outcome text
        
        State Transitions:
        - Valid stand: Dealer plays, compare hands
        - Player wins: → "result", balance += bet
        - Player loses: → "result", balance -= bet (already done in hit())
        - Push (tie): → "result", balance unchanged
        - If balance >= target_balance: → "won" (game won!)
        - If balance <= 0: → "out_of_money" (game over, prompt for reset)
        
        BREAK POINTS:
        - If dealer >= 17 changes to > 17, soft 17s won't stand
        - If win condition balance calculation is wrong, game doesn't track money
        - If out_of_money check is removed, player can continue with -$ balance
        - If compare_hands() result string changes, balance updates fail
        """
        # Can only stand during active play
        if self.game_state != "playing":
            return "invalid", "Cannot stand now."

        # Dealer plays: hits on 16 or less, stands on 17+
        while True:
            dealer_total, _ = calculate_hand_value(self.dealer_hand)
            if dealer_total >= 17:
                break
            self.dealer_hand.append(self.deck.deal())

        # Compare final hands
        player_total, _ = calculate_hand_value(self.player_hand)
        dealer_total, _ = calculate_hand_value(self.dealer_hand)
        result, message = compare_hands(player_total, dealer_total)

        # Update balance based on result
        if result == "win":
            self.balance += self.current_bet
        elif result == "lose":
            self.balance -= self.current_bet
        # "push" and "bust" don't change balance (already handled in hit())

        self.game_state = "result"
        self.result_message = message

        # Check for overall game win/loss conditions
        if self.balance >= self.target_balance:
            # Player reached goal!
            self.game_state = "won"
        elif self.balance <= 0:
            # Player out of money
            self.game_state = "out_of_money"
            if self.game_state == "out_of_money":
                self.result_message += " You are out of money!"

        return "stand", message

    def get_player_hand_str(self) -> str:
        """Return player's hand as a formatted string for display.
        
        Format: "Player: [cards] = [total] (soft/hard)"
        Example: "Player: A♥, 6♦ = 17 (soft)"
        
        Returns:
            Formatted string with all cards and total value
        """
        cards_str = ", ".join(str(card) for card in self.player_hand)
        total, has_ace = calculate_hand_value(self.player_hand)
        soft_str = " (soft)" if has_ace else ""
        return f"Player: {cards_str} = {total}{soft_str}"

    def get_dealer_hand_str(self, hide_hole_card: bool = False) -> str:
        """Return dealer's hand as a formatted string for display.
        
        Args:
            hide_hole_card: If True, hide the dealer's second card during play
                - During player's turn ("playing" state): Show only first card
                - After stand/end ("result" state): Show all cards
        
        Returns:
            Formatted string with cards and total (or [hidden] for hole card)
        
        Example:
            - Playing state: "Dealer: K♠, [hidden]"
            - Result state: "Dealer: K♠, 7♥ = 17"
        """
        if hide_hole_card and len(self.dealer_hand) >= 2:
            # Only show first card (hole card is hidden)
            cards_str = f"{self.dealer_hand[0]}, [hidden]"
            return f"Dealer: {cards_str}"
        else:
            # Show all cards with total
            cards_str = ", ".join(str(card) for card in self.dealer_hand)
            total, has_ace = calculate_hand_value(self.dealer_hand)
            soft_str = " (soft)" if has_ace else ""
            return f"Dealer: {cards_str} = {total}{soft_str}"

    def reset_balance_on_broke(self):
        """Reset player balance and hands when broke (balance <= 0).
        
        Called when player clicks "Get More Money" in out-of-money dialog.
        
        Actions:
        1. Clear both hands
        2. Reset current bet to 0
        3. Clear any result message
        4. Reset balance to starting amount
        5. Move back to "betting" state
        6. Optionally reshuffle if deck is low
        
        This allows player to play again without restarting the game.
        
        BREAK POINT: If this doesn't properly clear state, stale data
        (old cards/bets) can appear on next hand.
        """
        # Reset hands and prepare for new betting phase
        self.player_hand.clear()
        self.dealer_hand.clear()
        self.current_bet = 0
        self.result_message = ""
        
        # Reset balance to starting amount
        self.balance = self.starting_balance
        self.game_state = "betting"
        
        # Reshuffle if deck is getting low
        if self.deck.remaining() < 10:
            self.deck = Deck()

