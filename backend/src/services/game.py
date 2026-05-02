"""
Clean interactive poker game API.

Designed for use in Spyder / interactive Python. No pygame dependency.
Uses the vectorized NumPy evaluator and equity calculator.

Usage:
    game = PokerGame(['Hero', 'V1', 'V2', 'V3'], buy_in=1000)
    hand = game.new_hand()
    print(hand)
    hand.my_equity()
    hand.deal_flop()
    hand.my_equity()
    hand.deal_turn()
    hand.deal_river()
    hand.showdown()
"""

import numpy as np
from src.engine.cards import (
    FULL_DECK, card_str, cards_str, normalize_cards
)
from src.engine.evaluator import evaluate_hands, hand_category, CATEGORY_SCALE
from src.engine.equity import (
    equity_vs_hand, equity_vs_range,
    hand_type_from_cards, preflop_equity_vs_range, preflop_equity_lookup
)
from src.engine.positions import Positions
from src.engine.ranges import openRaise

# Category names for display
_HAND_NAMES = {
    1: "High Card", 2: "Pair", 3: "Two Pair", 4: "Three of a Kind",
    5: "Straight", 6: "Flush", 7: "Full House", 8: "Four of a Kind",
    9: "Straight Flush", 10: "Royal Flush"
}


class Player:
    """A player at the table."""

    def __init__(self, name, buy_in, is_hero=False):
        self.name = name
        self.chips = buy_in
        self.is_hero = is_hero
        self.position = None
        self._hole = None  # int8 array of 2 card IDs
        self.bot = None    # VillainBot instance or None for hero

    @property
    def hole_cards(self):
        if self._hole is None:
            return None
        return tuple(cards_str(self._hole))

    def __repr__(self):
        pos = self.position or '?'
        chips = f"${self.chips}"
        if self._hole is not None:
            hole = ' '.join(cards_str(self._hole))
            return f"{self.name} ({pos}) [{hole}] {chips}"
        return f"{self.name} ({pos}) {chips}"


class PokerGame:
    """Manages a multi-hand poker session."""

    def __init__(self, player_names, buy_in=1000, hero_index=0,
                 big_blind=10, villain_archetypes=None):
        """Create a new poker game.

        Parameters
        ----------
        player_names : list of str
            Names for each player. First player is hero by default.
        buy_in : int
            Starting chips for each player.
        hero_index : int
            Which player is the hero (you). Default 0 (first).
        big_blind : int
            Big blind amount. Small blind is half (rounded down).
        villain_archetypes : dict or None
            Optional {player_name: archetype_str} mapping.
            Unspecified villains get random archetypes.
        """
        if len(player_names) < 3 or len(player_names) > 9:
            raise ValueError("Need 3-9 players")

        self.players = []
        for i, name in enumerate(player_names):
            p = Player(name, buy_in, is_hero=(i == hero_index))
            self.players.append(p)

        self.hero = self.players[hero_index]
        self.big_blind = big_blind
        self.small_blind = big_blind // 2
        self._positions = list(Positions[len(self.players)])
        self._hand_count = 0
        self._assign_positions()

        # Assign villain bots
        from .villain import VillainBot, ARCHETYPE_NAMES
        rng = np.random.default_rng()
        if villain_archetypes is None:
            villain_archetypes = {}
        for player in self.players:
            if not player.is_hero:
                arch = villain_archetypes.get(player.name)
                if arch is None:
                    arch = rng.choice(ARCHETYPE_NAMES)
                player.bot = VillainBot(arch)

    def _assign_positions(self):
        for i, player in enumerate(self.players):
            player.position = self._positions[i]

    def new_hand(self):
        """Start a new hand. Rotates positions and deals hole cards."""
        # Remove busted players
        self.players = [p for p in self.players if p.chips > 0]
        if len(self.players) < 2:
            raise RuntimeError("Not enough players with chips")

        # Rotate positions
        if self._hand_count > 0:
            self._positions.insert(0, self._positions.pop())
        self._positions = list(Positions.get(len(self.players),
                                             Positions[min(Positions.keys())]))
        if self._hand_count > 0:
            # Apply rotation based on hand count
            for _ in range(self._hand_count % len(self.players)):
                self._positions.insert(0, self._positions.pop())
        self._assign_positions()
        self._hand_count += 1

        return HandState(self)

    def __repr__(self):
        lines = [f"PokerGame ({len(self.players)} players, hand #{self._hand_count})"]
        for p in self.players:
            hero_mark = " *" if p.is_hero else ""
            lines.append(f"  {p}{hero_mark}")
        return '\n'.join(lines)


class HandState:
    """Tracks a single hand in progress."""

    def __init__(self, game):
        self.game = game
        self.active_players = list(game.players)
        self.pot = 0
        self.big_blind = game.big_blind
        self.small_blind = game.small_blind

        # Betting state
        self.current_bet = 0
        self.player_bets = {p.name: 0 for p in self.active_players}
        self.action_log = []          # [(name, action, amount), ...]
        self._last_raiser = None      # name of last player who raised
        self._last_raiser_position = None

        # Shuffle deck and deal hole cards
        rng = np.random.default_rng()
        deck = rng.permutation(FULL_DECK)
        self._deck_idx = 0
        self._board = np.array([], dtype=np.int8)
        self._street = 'preflop'

        # Deal 2 cards to each player
        for player in self.active_players:
            player._hole = np.array(
                [deck[self._deck_idx], deck[self._deck_idx + 1]],
                dtype=np.int8
            )
            self._deck_idx += 2

        self._deck = deck

        # Post blinds
        self._post_blinds()

    @property
    def street(self):
        return self._street

    @property
    def board(self):
        """Current community cards as list of strings."""
        return cards_str(self._board) if len(self._board) > 0 else []

    @property
    def board_raw(self):
        """Current community cards as int8 array."""
        return self._board.copy()

    @property
    def hero(self):
        return self.game.hero

    def deal_flop(self):
        """Deal the flop (3 community cards)."""
        if self._street != 'preflop':
            raise RuntimeError(f"Can't deal flop from {self._street}")
        self._deck_idx += 1  # burn
        flop = self._deck[self._deck_idx:self._deck_idx + 3].astype(np.int8)
        self._deck_idx += 3
        self._board = flop
        self._street = 'flop'
        self._reset_street_bets()
        return self

    def deal_turn(self):
        """Deal the turn (4th community card)."""
        if self._street != 'flop':
            raise RuntimeError(f"Can't deal turn from {self._street}")
        self._deck_idx += 1  # burn
        turn = self._deck[self._deck_idx:self._deck_idx + 1].astype(np.int8)
        self._deck_idx += 1
        self._board = np.concatenate([self._board, turn])
        self._street = 'turn'
        self._reset_street_bets()
        return self

    def deal_river(self):
        """Deal the river (5th community card)."""
        if self._street != 'turn':
            raise RuntimeError(f"Can't deal river from {self._street}")
        self._deck_idx += 1  # burn
        river = self._deck[self._deck_idx:self._deck_idx + 1].astype(np.int8)
        self._deck_idx += 1
        self._board = np.concatenate([self._board, river])
        self._street = 'river'
        self._reset_street_bets()
        return self

    def deal_to_river(self):
        """Deal all remaining streets at once."""
        if self._street == 'preflop':
            self.deal_flop()
        if self._street == 'flop':
            self.deal_turn()
        if self._street == 'turn':
            self.deal_river()
        return self

    def fold(self, player_name):
        """Remove a player from the hand."""
        player = self._find_player(player_name)
        self.active_players.remove(player)
        self.action_log.append((player_name, 'fold', 0))
        # Auto-award pot if only one player remains
        if len(self.active_players) == 1:
            winner = self.active_players[0]
            winner.chips += self.pot
            self.pot = 0
        return self

    def check(self, player_name):
        """Player checks (no bet to call, or already matched)."""
        self.action_log.append((player_name, 'check', 0))
        return self

    def call(self, player_name):
        """Player calls the current bet."""
        player = self._find_player(player_name)
        already_in = self.player_bets.get(player_name, 0)
        to_call = min(self.current_bet - already_in, player.chips)
        if to_call <= 0:
            return self.check(player_name)
        player.chips -= to_call
        self.pot += to_call
        self.player_bets[player_name] = already_in + to_call
        self.action_log.append((player_name, 'call', to_call))
        if player.chips == 0:
            print(f"{player.name} is all-in")
        return self

    def raise_to(self, player_name, total_amount):
        """Player raises to total_amount for this street."""
        player = self._find_player(player_name)
        already_in = self.player_bets.get(player_name, 0)
        to_put_in = min(total_amount - already_in, player.chips)
        if to_put_in <= 0:
            return self.check(player_name)
        player.chips -= to_put_in
        self.pot += to_put_in
        self.player_bets[player_name] = already_in + to_put_in
        self.current_bet = self.player_bets[player_name]
        self._last_raiser = player_name
        self._last_raiser_position = player.position
        self.action_log.append((player_name, 'raise', self.current_bet))
        if player.chips == 0:
            print(f"{player.name} is all-in")
        return self

    def bet(self, player_name, amount):
        """Player bets an amount (opens betting or raises)."""
        player = self._find_player(player_name)
        already_in = self.player_bets.get(player_name, 0)
        actual = min(amount, player.chips)
        player.chips -= actual
        self.pot += actual
        self.player_bets[player_name] = already_in + actual
        new_level = self.player_bets[player_name]
        if new_level > self.current_bet:
            self.current_bet = new_level
            self._last_raiser = player_name
            self._last_raiser_position = player.position
        self.action_log.append((player_name, 'bet', actual))
        if player.chips == 0:
            print(f"{player.name} is all-in")
        return self

    # ------------------------------------------------------------------
    # Betting infrastructure
    # ------------------------------------------------------------------

    def _post_blinds(self):
        """Post small and big blinds at start of hand."""
        pos_map = {p.position: p for p in self.active_players}
        sb_player = pos_map.get('SB')
        bb_player = pos_map.get('BB')
        if sb_player:
            sb_amt = min(self.small_blind, sb_player.chips)
            sb_player.chips -= sb_amt
            self.pot += sb_amt
            self.player_bets[sb_player.name] = sb_amt
            self.action_log.append((sb_player.name, 'sb', sb_amt))
        if bb_player:
            bb_amt = min(self.big_blind, bb_player.chips)
            bb_player.chips -= bb_amt
            self.pot += bb_amt
            self.player_bets[bb_player.name] = bb_amt
            self.current_bet = bb_amt
            self.action_log.append((bb_player.name, 'bb', bb_amt))

    def _reset_street_bets(self):
        """Reset per-street betting state when a new street is dealt."""
        self.current_bet = 0
        self.player_bets = {p.name: 0 for p in self.active_players}
        self._last_raiser = None
        self._last_raiser_position = None

    def _betting_order(self):
        """Return active players in betting order for current street."""
        all_positions = list(Positions[len(self.game.players)])

        if self._street == 'preflop':
            # Preflop: UTG acts first (skip BTN, SB, BB to end)
            while all_positions and all_positions[0] in ('BTN', 'SB', 'BB'):
                all_positions.append(all_positions.pop(0))
        else:
            # Postflop: SB first, BTN last
            while all_positions and all_positions[0] != 'SB':
                all_positions.append(all_positions.pop(0))

        active_pos = {p.position: p for p in self.active_players}
        return [active_pos[pos] for pos in all_positions if pos in active_pos]

    def _build_game_state(self, player):
        """Build context dict for a villain bot's decision."""
        return {
            'name': player.name,
            'hole': player._hole.copy(),
            'board': self._board.copy(),
            'street': self._street,
            'position': player.position,
            'pot': self.pot,
            'current_bet': self.current_bet,
            'player_bets': dict(self.player_bets),
            'big_blind': self.big_blind,
            'stack': player.chips,
            'table_size': len(self.game.players),
            'last_raiser_position': self._last_raiser_position,
            'active_names': [p.name for p in self.active_players],
        }

    def play_villains(self):
        """Run villain bot actions up to the hero's turn.

        Iterates through players in betting order. Each villain bot
        decides and acts automatically. Stops when it reaches the hero.
        Returns list of (name, action, amount) for actions taken.
        """
        actions = []
        self._villains_acted = set()
        for player in self._betting_order():
            if player.name not in [p.name for p in self.active_players]:
                continue
            if player.is_hero:
                break
            if player.bot is None:
                continue
            self._villains_acted.add(player.name)
            action, amount = player.bot.decide(self._build_game_state(player))
            self._execute_bot_action(player, action, amount)
            actions.append((player.name, action, amount))
            print(f"  {player.position:6s} {player.name:12s} {action}"
                  f"{f' {amount}' if amount else ''}")
        return actions

    def play_villains_after_hero(self):
        """Run villain bot actions for players not yet acted this round.

        Processes all bot players who weren't handled by play_villains().
        Returns list of actions taken.
        """
        actions = []
        acted = getattr(self, '_villains_acted', set())
        for player in self._betting_order():
            if player.is_hero:
                continue
            if player.name in acted:
                continue
            if player.name not in [p.name for p in self.active_players]:
                continue
            if player.bot is None:
                continue
            action, amount = player.bot.decide(self._build_game_state(player))
            self._execute_bot_action(player, action, amount)
            actions.append((player.name, action, amount))
            print(f"  {player.position:6s} {player.name:12s} {action}"
                  f"{f' {amount}' if amount else ''}")
        return actions

    def _execute_bot_action(self, player, action, amount):
        """Execute a bot's decided action."""
        if action == 'fold':
            self.fold(player.name)
        elif action == 'check':
            self.check(player.name)
        elif action == 'call':
            self.call(player.name)
        elif action == 'raise':
            self.raise_to(player.name, amount)
        elif action == 'bet':
            self.bet(player.name, amount)

    def my_equity(self, vs_hand=None, vs_range=None):
        """Calculate hero's equity at the current street.

        Parameters
        ----------
        vs_hand : cards, optional
            Specific villain hand to compare against.
        vs_range : list of str, optional
            Villain range as hand type names. If None, uses position-based
            default range for first villain.

        Returns
        -------
        dict with equity, win, tie, lose
        """
        hero_hole = self.hero._hole
        board = self._board if len(self._board) > 0 else None

        if vs_hand is not None:
            return equity_vs_hand(hero_hole, vs_hand, board=board)

        if vs_range is None:
            vs_range = self._default_villain_range()

        # Preflop: use instant lookup table (falls back to MC if table missing)
        if self._street == 'preflop' and vs_hand is None:
            try:
                hero_type = hand_type_from_cards(hero_hole[0], hero_hole[1])
                return preflop_equity_vs_range(hero_type, vs_range)
            except (FileNotFoundError, KeyError):
                # Fallback to Monte Carlo if lookup table not available
                return equity_vs_range(hero_hole, vs_range, board=board,
                                       n_samples=2000)

        return equity_vs_range(hero_hole, vs_range, board=board)

    def showdown(self):
        """Score all remaining players and determine winner(s).

        Returns
        -------
        dict with 'winners' (list of Player), 'results' (list of dicts per player)
        """
        if len(self._board) < 5:
            self.deal_to_river()

        if len(self.active_players) == 1:
            winner = self.active_players[0]
            winner.chips += self.pot
            self.pot = 0
            return {
                'winners': [winner],
                'results': [{'player': winner.name, 'hand': 'Last standing',
                             'score': None}]
            }

        # Build (N, 7) hands array
        n = len(self.active_players)
        hands = np.zeros((n, 7), dtype=np.int8)
        for i, player in enumerate(self.active_players):
            hands[i, :2] = player._hole
            hands[i, 2:] = self._board

        scores = evaluate_hands(hands)
        categories = hand_category(scores)
        max_score = scores.max()
        winner_mask = scores == max_score

        # Build results
        results = []
        winners = []
        for i, player in enumerate(self.active_players):
            cat = int(categories[i])
            is_winner = bool(winner_mask[i])
            results.append({
                'player': player.name,
                'hole': ' '.join(cards_str(player._hole)),
                'hand': _HAND_NAMES.get(cat, '?'),
                'score': int(scores[i]),
                'winner': is_winner,
            })
            if is_winner:
                winners.append(player)

        # Distribute pot (leftover chip goes to first winner)
        share = self.pot // len(winners)
        leftover = self.pot % len(winners)
        for i, w in enumerate(winners):
            w.chips += share + (1 if i < leftover else 0)
        self.pot = 0

        return {'winners': winners, 'results': results}

    def _find_player(self, name):
        for p in self.active_players:
            if p.name == name:
                return p
        raise ValueError(f"Player '{name}' not found in active players")

    def _default_villain_range(self):
        """Get a position-appropriate opening range for the first non-hero villain."""
        table_size = len(self.game.players)
        if table_size not in openRaise:
            # Fallback: top 25%
            from poker_variables import openRaise_25PC
            return openRaise_25PC

        table_ranges = openRaise[table_size]
        # Use the first non-hero active player's position
        for player in self.active_players:
            if not player.is_hero and player.position in table_ranges:
                return table_ranges[player.position]

        # Fallback
        from poker_variables import openRaise_25PC
        return openRaise_25PC

    def __repr__(self):
        lines = []
        lines.append(f"--- {self._street.upper()} ---")

        if len(self._board) > 0:
            lines.append(f"Board: {' '.join(cards_str(self._board))}")
        else:
            lines.append("Board: (none)")

        lines.append(f"Pot: ${self.pot}  |  Bet to call: ${self.current_bet}")
        lines.append("")

        for player in self.active_players:
            pos = player.position or '?'
            hero_mark = " <-- Hero" if player.is_hero else ""
            if player.is_hero or self._street == 'river':
                hole = ' '.join(cards_str(player._hole))
                lines.append(f"  {pos:6s} {player.name:12s} [{hole}]  "
                             f"${player.chips}{hero_mark}")
            else:
                lines.append(f"  {pos:6s} {player.name:12s} [** **]  "
                             f"${player.chips}{hero_mark}")

        # Show recent actions for this street
        street_actions = [(n, a, amt) for n, a, amt in self.action_log
                          if a not in ('sb', 'bb') or self._street == 'preflop']
        if street_actions:
            lines.append("")
            lines.append("Actions:")
            for name, action, amount in street_actions[-8:]:
                if amount:
                    lines.append(f"  {name} {action} {amount}")
                else:
                    lines.append(f"  {name} {action}")

        return '\n'.join(lines)
