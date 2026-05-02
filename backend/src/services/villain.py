"""
Villain bot decision engine for poker training.

Each villain has an archetype (TAG, LAG, NIT, CALLING_STATION, MANIAC)
defined by a profile dict of tunable parameters. All decisions flow
through these numbers, so future drift/tilt just mutates the dict.

The hero never sees which archetype a villain is — they must infer it
from observed betting patterns.
"""

import numpy as np
from src.engine.equity import hand_type_from_cards, preflop_equity_vs_range
from src.engine.ranges import openRaise
from src.engine.variables import openRaise_25PC, openRaise_50PC, handsList

# ========== Archetype Profiles ==========

ARCHETYPE_PROFILES = {
    'TAG': {                            # Tight-Aggressive
        'preflop_range_pct': 0.85,      # Plays 85% of the GTO position range
        'preflop_3bet_threshold': 0.62,  # Equity to 3-bet vs raiser
        'preflop_flat_threshold': 0.38, # Min equity to flat-call a raise
        'open_raise_bb': 2.5,           # Open raise sizing (big blinds)
        'cbet_freq': 0.70,             # Continuation bet frequency
        'cbet_size_pct': 0.60,         # C-bet as fraction of pot
        'postflop_bet_equity': 0.55,   # Equity threshold to bet
        'postflop_call_equity': 0.35,  # Equity threshold to call
        'postflop_raise_equity': 0.70, # Equity threshold to raise
        'bluff_freq': 0.15,            # Bluff probability
        'noise': 0.08,                 # Gaussian sigma on thresholds
    },
    'LAG': {                            # Loose-Aggressive
        'preflop_range_pct': 1.30,
        'preflop_3bet_threshold': 0.55,
        'preflop_flat_threshold': 0.32,
        'open_raise_bb': 3.0,
        'cbet_freq': 0.80,
        'cbet_size_pct': 0.75,
        'postflop_bet_equity': 0.45,
        'postflop_call_equity': 0.30,
        'postflop_raise_equity': 0.60,
        'bluff_freq': 0.30,
        'noise': 0.12,
    },
    'NIT': {                            # Ultra-tight, passive without the goods
        'preflop_range_pct': 0.50,
        'preflop_3bet_threshold': 0.72,
        'preflop_flat_threshold': 0.45,
        'open_raise_bb': 2.5,
        'cbet_freq': 0.50,
        'cbet_size_pct': 0.50,
        'postflop_bet_equity': 0.65,
        'postflop_call_equity': 0.42,
        'postflop_raise_equity': 0.80,
        'bluff_freq': 0.05,
        'noise': 0.05,
    },
    'CALLING_STATION': {                # Loose-passive: calls everything
        'preflop_range_pct': 1.50,
        'preflop_3bet_threshold': 0.78,
        'preflop_flat_threshold': 0.20, # Calls with almost anything
        'open_raise_bb': 2.0,
        'cbet_freq': 0.30,
        'cbet_size_pct': 0.40,
        'postflop_bet_equity': 0.60,
        'postflop_call_equity': 0.20,
        'postflop_raise_equity': 0.85,
        'bluff_freq': 0.05,
        'noise': 0.10,
    },
    'MANIAC': {                         # Ultra-aggressive: bets and raises constantly
        'preflop_range_pct': 1.60,
        'preflop_3bet_threshold': 0.45,
        'preflop_flat_threshold': 0.25,
        'open_raise_bb': 4.0,
        'cbet_freq': 0.90,
        'cbet_size_pct': 1.0,
        'postflop_bet_equity': 0.35,
        'postflop_call_equity': 0.25,
        'postflop_raise_equity': 0.45,
        'bluff_freq': 0.45,
        'noise': 0.15,
    },
}

ARCHETYPE_NAMES = list(ARCHETYPE_PROFILES.keys())


class VillainBot:
    """Autonomous decision engine for a villain player."""

    def __init__(self, archetype='TAG', rng_seed=None):
        if archetype not in ARCHETYPE_PROFILES:
            raise ValueError(f"Unknown archetype: {archetype}. "
                             f"Choose from {ARCHETYPE_NAMES}")
        self.archetype = archetype
        self.profile = ARCHETYPE_PROFILES[archetype].copy()
        self.rng = np.random.default_rng(rng_seed)
        self.hand_history = []  # for future tilt/drift

    def decide(self, ctx):
        """Return (action, amount) given current game state.

        Parameters
        ----------
        ctx : dict
            Game state built by HandState._build_game_state().
            Keys: hole, board, street, position, pot, current_bet,
                  player_bets, big_blind, stack, table_size,
                  last_raiser_position, active_names.

        Returns
        -------
        (str, int) — action name and amount.
            action: 'fold', 'check', 'call', 'raise'
            amount: 0 for fold/check, relevant amount for call/raise
        """
        if ctx['street'] == 'preflop':
            return self._decide_preflop(ctx)
        return self._decide_postflop(ctx)

    # ------------------------------------------------------------------
    # Preflop: range-based decisions
    # ------------------------------------------------------------------

    def _decide_preflop(self, ctx):
        p = self.profile
        hand_type = hand_type_from_cards(int(ctx['hole'][0]),
                                          int(ctx['hole'][1]))
        position = ctx['position']
        table_size = ctx['table_size']
        current_bet = ctx['current_bet']
        bb = ctx['big_blind']

        # Get GTO range for this position
        base_range = self._get_position_range(table_size, position)

        # Scale by archetype
        range_pct = p['preflop_range_pct']
        if range_pct < 1.0:
            n_hands = max(1, int(len(base_range) * range_pct))
            effective_range = base_range[:n_hands]
        elif range_pct > 1.0:
            # Expand beyond position range using handsList order
            effective_range = list(base_range)
            target = int(len(base_range) * range_pct)
            base_set = set(base_range)
            for ht in handsList:
                if len(effective_range) >= target:
                    break
                if ht not in base_set:
                    effective_range.append(ht)
        else:
            effective_range = list(base_range)

        in_range = hand_type in effective_range
        noise = self.rng.normal(0, p['noise'])

        # Not in range
        if not in_range:
            if current_bet > bb:
                # Facing a raise with out-of-range hand:
                # Loose archetypes may still call based on equity
                raiser_pos = ctx.get('last_raiser_position')
                raiser_range = self._get_position_range(table_size, raiser_pos)
                eq = preflop_equity_vs_range(hand_type, raiser_range)
                flat_threshold = p['preflop_flat_threshold'] + noise
                if eq['equity'] > flat_threshold:
                    return ('call', current_bet)
            if self.rng.random() < p['bluff_freq']:
                if current_bet <= bb:
                    size = int(bb * p['open_raise_bb'])
                    return ('raise', size)
                else:
                    return ('raise', int(current_bet * 3))
            # BB can check for free
            if position == 'BB' and current_bet <= bb:
                return ('check', 0)
            return ('fold', 0)

        # In range
        if current_bet <= bb:
            # Unopened — open raise
            size = int(bb * p['open_raise_bb'])
            return ('raise', size)
        else:
            # Facing a raise — use equity to decide 3bet vs call vs fold
            raiser_pos = ctx.get('last_raiser_position')
            raiser_range = self._get_position_range(table_size, raiser_pos)
            eq = preflop_equity_vs_range(hand_type, raiser_range)
            equity = eq['equity']

            if equity > p['preflop_3bet_threshold'] + noise:
                return ('raise', int(current_bet * 3))
            elif equity > p['preflop_flat_threshold'] + noise:
                return ('call', current_bet)
            else:
                return ('fold', 0)

    # ------------------------------------------------------------------
    # Postflop: equity-based decisions
    # ------------------------------------------------------------------

    def _decide_postflop(self, ctx):
        p = self.profile
        current_bet = ctx['current_bet']
        pot = ctx['pot']
        bb = ctx['big_blind']
        noise = self.rng.normal(0, p['noise'])

        # Estimate equity vs hero's likely range
        equity = self._estimate_postflop_equity(ctx)

        if current_bet == 0:
            # No bet facing us — check or bet
            bet_threshold = p['postflop_bet_equity'] + noise
            if equity > bet_threshold or self.rng.random() < p['bluff_freq']:
                # C-bet or value bet
                if self.rng.random() < p['cbet_freq'] or equity > bet_threshold:
                    size = max(bb, int(pot * p['cbet_size_pct']
                                       * self.rng.uniform(0.85, 1.15)))
                    size = min(size, ctx['stack'])
                    return ('raise', size)
            return ('check', 0)
        else:
            # Facing a bet
            pot_odds = current_bet / (pot + current_bet) if (pot + current_bet) > 0 else 0

            if equity > p['postflop_raise_equity'] + noise:
                # Raise
                raise_size = int(current_bet * 2.5
                                 * self.rng.uniform(0.85, 1.15))
                raise_size = min(raise_size, ctx['stack'] + current_bet)
                return ('raise', raise_size)
            elif equity > p['postflop_call_equity'] + noise or equity > pot_odds:
                return ('call', current_bet)
            else:
                return ('fold', 0)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_position_range(self, table_size, position):
        """Get the GTO opening range for a position, with fallback."""
        if (table_size in openRaise
                and position in openRaise.get(table_size, {})):
            return openRaise[table_size][position]
        return openRaise_25PC

    def _estimate_postflop_equity(self, ctx):
        """Fast equity estimate for postflop bot decisions.

        Uses preflop lookup as a rough proxy to avoid slow per-hand
        equity computation. Real equity calculation would be more
        accurate but too slow for every bot decision.
        """
        hand_type = hand_type_from_cards(int(ctx['hole'][0]),
                                          int(ctx['hole'][1]))
        # Use a mid-range opponent estimate
        hero_range = self._get_position_range(ctx['table_size'], 'CO')
        result = preflop_equity_vs_range(hand_type, hero_range)
        base_equity = result['equity']

        # Adjust based on board texture (simple heuristic):
        # If we have a pair or better on the board, boost equity slightly
        if len(ctx['board']) >= 3:
            ranks = ctx['board'] // 4
            hole_ranks = ctx['hole'] // 4
            # Check if either hole card pairs the board
            board_hit = np.isin(hole_ranks, ranks).any()
            if board_hit:
                base_equity = min(1.0, base_equity + 0.10)
            # Check for overcards (both hole cards above all board cards)
            if len(ranks) > 0 and (hole_ranks > ranks.max()).all():
                base_equity = min(1.0, base_equity + 0.05)

        return base_equity

    def __repr__(self):
        return f"VillainBot({self.archetype})"
