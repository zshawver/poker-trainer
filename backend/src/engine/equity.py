"""
Poker equity calculator powered by the vectorized NumPy evaluator.

Supports:
- Hand-vs-hand equity (exhaustive or Monte Carlo)
- Hand-vs-range equity
- Preflop lookup from precomputed 169x169 table (instant)
- Street-aware: auto-selects exhaustive vs sampling based on board size
"""

import os
import json
import numpy as np
from numpy_cards import (
    normalize_cards, remaining_deck, enumerate_boards,
    deal_random_boards, make_hands, card_str, cards_str,
    _RANK_CHARS
)
from numpy_eval import evaluate_hands
from poker_variables import rangeHands


# ========== Preflop lookup table ==========

_preflop_table = None  # cached after first load


def hand_type_from_cards(card1, card2):
    """Classify two concrete card IDs into a hand type string.

    Parameters
    ----------
    card1, card2 : int
        Card IDs (0-51).

    Returns
    -------
    str like 'AA', 'AKs', 'AKo', '72o'
    """
    r1 = int(card1) // 4  # 0-12
    s1 = int(card1) % 4
    r2 = int(card2) // 4
    s2 = int(card2) % 4

    # Ensure higher rank first
    if r1 < r2:
        r1, r2 = r2, r1
        s1, s2 = s2, s1

    rank_high = _RANK_CHARS[r1]
    rank_low = _RANK_CHARS[r2]

    if r1 == r2:
        return f"{rank_high}{rank_low}"
    elif s1 == s2:
        return f"{rank_high}{rank_low}s"
    else:
        return f"{rank_high}{rank_low}o"


def load_preflop_table(path=None):
    """Load precomputed preflop equity table. Cached after first call.

    Returns
    -------
    dict with 'hand_types', 'n_samples', 'matrix'
    """
    global _preflop_table
    if _preflop_table is not None:
        return _preflop_table

    if path is None:
        try:
            _dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            _dir = os.getcwd()
        path = os.path.join(_dir, 'preflop_equity.json')

    with open(path, 'r') as f:
        _preflop_table = json.load(f)
    return _preflop_table


def preflop_equity_lookup(hero_type, villain_type):
    """Instant preflop equity lookup for one hand type vs another.

    Returns
    -------
    dict with equity, win, tie, lose
    """
    table = load_preflop_table()
    entry = table['matrix'][hero_type][villain_type]
    w, t, l = entry
    return {
        'equity': w + 0.5 * t,
        'win': w,
        'tie': t,
        'lose': l,
    }


def preflop_equity_vs_range(hero_type, range_names):
    """Instant preflop equity vs a range using lookup table.

    Parameters
    ----------
    hero_type : str
        Hand type string like 'AKs', 'QQ'.
    range_names : list of str
        Villain's range as hand type strings.

    Returns
    -------
    dict with equity, win, tie, lose, by_hand
    """
    table = load_preflop_table()
    matrix = table['matrix']

    if hero_type not in matrix:
        return {'equity': 0.0, 'win': 0.0, 'tie': 0.0, 'lose': 0.0,
                'by_hand': {}}

    # Weight each villain hand type by number of combos
    # Pairs: 6, suited: 4, offsuit: 12
    total_weight = 0.0
    total_win = 0.0
    total_tie = 0.0
    by_hand = {}

    for vt in range_names:
        if vt not in matrix.get(hero_type, {}):
            continue
        # Determine combo count for weighting
        if vt not in rangeHands:
            continue
        n_combos = len(rangeHands[vt])
        entry = matrix[hero_type][vt]
        w, t, l = entry

        total_win += w * n_combos
        total_tie += t * n_combos
        total_weight += n_combos
        by_hand[vt] = w + 0.5 * t

    if total_weight == 0:
        return {'equity': 0.0, 'win': 0.0, 'tie': 0.0, 'lose': 0.0,
                'by_hand': {}}

    avg_win = total_win / total_weight
    avg_tie = total_tie / total_weight
    avg_lose = 1.0 - avg_win - avg_tie

    return {
        'equity': avg_win + 0.5 * avg_tie,
        'win': avg_win,
        'tie': avg_tie,
        'lose': avg_lose,
        'by_hand': by_hand,
    }


def equity_vs_hand(hero, villain, board=None, n_samples=None):
    """Calculate equity of hero vs a single villain hand.

    Parameters
    ----------
    hero : cards (any format — strings, tuples, int8 array)
        Hero's 2 hole cards.
    villain : cards (any format)
        Villain's 2 hole cards.
    board : cards or None
        0-5 known community cards.
    n_samples : int or None
        None = exhaustive enumeration (auto for flop/turn/river,
        explicit for preflop). Int = Monte Carlo with that many samples.

    Returns
    -------
    dict with keys: equity, win, tie, lose (all floats 0-1)
    """
    hero = normalize_cards(hero)
    villain = normalize_cards(villain)
    board = normalize_cards(board)

    board_len = len(board)
    cards_needed = 5 - board_len
    dead = np.concatenate([hero, villain, board])

    if cards_needed == 0:
        # River — single evaluation
        boards = board.reshape(1, 5)
    elif n_samples is not None:
        # Monte Carlo
        completions = deal_random_boards(n_samples, dead, cards_needed)
        if board_len > 0:
            boards = np.hstack([
                np.broadcast_to(board, (n_samples, board_len)),
                completions
            ])
        else:
            boards = completions
    else:
        # Exhaustive
        completions = enumerate_boards(dead, cards_needed)
        if board_len > 0:
            n_comp = completions.shape[0]
            boards = np.hstack([
                np.broadcast_to(board, (n_comp, board_len)),
                completions
            ])
        else:
            boards = completions

    n = boards.shape[0]

    # Build 7-card hands for hero and villain
    hero_hands = make_hands(hero, boards)
    villain_hands = make_hands(villain, boards)

    # Evaluate all hands
    hero_scores = evaluate_hands(hero_hands)
    villain_scores = evaluate_hands(villain_hands)

    # Compare
    wins = (hero_scores > villain_scores).sum()
    ties = (hero_scores == villain_scores).sum()
    losses = n - wins - ties

    return {
        'equity': float(wins + 0.5 * ties) / n,
        'win': float(wins) / n,
        'tie': float(ties) / n,
        'lose': float(losses) / n,
    }


def expand_range(range_names, dead_cards):
    """Expand range name list to concrete card combos, filtering blockers.

    Parameters
    ----------
    range_names : list of str
        Hand type strings like ['AA', 'AKs', 'KK'].
    dead_cards : array-like of int8
        Cards to exclude (hero's hole cards, known board).

    Returns
    -------
    np.ndarray of shape (N, 2), dtype int8
        All valid concrete hole card combos in the range.
    dict
        Mapping from hand_type -> number of valid combos.
    """
    dead_set = set(int(c) for c in dead_cards)
    combos = []
    combo_counts = {}

    for hand_type in range_names:
        if hand_type not in rangeHands:
            continue
        type_combos = []
        for combo in rangeHands[hand_type]:
            # combo is [(rank1, suit1), (rank2, suit2)] in legacy format
            c0 = (combo[0][0] - 1) * 4 + (combo[0][1] - 1)
            c1 = (combo[1][0] - 1) * 4 + (combo[1][1] - 1)
            if c0 not in dead_set and c1 not in dead_set:
                type_combos.append([c0, c1])
        combo_counts[hand_type] = len(type_combos)
        combos.extend(type_combos)

    if not combos:
        return np.array([], dtype=np.int8).reshape(0, 2), combo_counts

    return np.array(combos, dtype=np.int8), combo_counts


def equity_vs_range(hero, range_names, board=None, n_samples=2000):
    """Calculate equity of hero vs a villain range.

    Parameters
    ----------
    hero : cards (any format)
        Hero's 2 hole cards.
    range_names : list of str
        Hand type strings defining villain's range.
    board : cards or None
        0-5 known community cards.
    n_samples : int
        Monte Carlo samples per villain combo for preflop.
        Ignored when board has 3+ cards (exhaustive is fast enough).

    Returns
    -------
    dict with keys:
        equity, win, tie, lose (weighted averages),
        by_hand: {hand_type: equity} breakdown
    """
    hero = normalize_cards(hero)
    board = normalize_cards(board)
    dead = np.concatenate([hero, board])

    villain_combos, combo_counts = expand_range(range_names, dead)

    if len(villain_combos) == 0:
        return {'equity': 0.0, 'win': 0.0, 'tie': 0.0, 'lose': 0.0,
                'by_hand': {}}

    board_len = len(board)
    cards_needed = 5 - board_len

    # For flop/turn/river, use exhaustive per villain combo
    # For preflop, use Monte Carlo
    use_exhaustive = board_len >= 3 or cards_needed <= 2

    total_wins = 0.0
    total_ties = 0.0
    total_boards = 0
    by_hand = {}

    # Track per-hand-type results
    hand_type_results = {ht: {'wins': 0.0, 'ties': 0.0, 'total': 0}
                         for ht in combo_counts if combo_counts[ht] > 0}

    combo_idx = 0
    for hand_type in range_names:
        if hand_type not in combo_counts or combo_counts[hand_type] == 0:
            continue

        n_type = combo_counts[hand_type]

        for i in range(n_type):
            villain = villain_combos[combo_idx]
            combo_idx += 1

            all_dead = np.concatenate([hero, villain, board])

            if cards_needed == 0:
                boards = board.reshape(1, 5)
            elif use_exhaustive:
                completions = enumerate_boards(all_dead, cards_needed)
                n_comp = completions.shape[0]
                if board_len > 0:
                    boards = np.hstack([
                        np.broadcast_to(board, (n_comp, board_len)),
                        completions
                    ])
                else:
                    boards = completions
            else:
                completions = deal_random_boards(n_samples, all_dead, cards_needed)
                if board_len > 0:
                    boards = np.hstack([
                        np.broadcast_to(board, (n_samples, board_len)),
                        completions
                    ])
                else:
                    boards = completions

            n_b = boards.shape[0]
            hero_hands = make_hands(hero, boards)
            villain_hands = make_hands(villain, boards)

            hero_scores = evaluate_hands(hero_hands)
            villain_scores = evaluate_hands(villain_hands)

            w = float((hero_scores > villain_scores).sum())
            t = float((hero_scores == villain_scores).sum())

            total_wins += w
            total_ties += t
            total_boards += n_b

            hand_type_results[hand_type]['wins'] += w
            hand_type_results[hand_type]['ties'] += t
            hand_type_results[hand_type]['total'] += n_b

    # Compute by-hand-type equities
    for ht, res in hand_type_results.items():
        if res['total'] > 0:
            by_hand[ht] = (res['wins'] + 0.5 * res['ties']) / res['total']

    total_losses = total_boards - total_wins - total_ties
    return {
        'equity': (total_wins + 0.5 * total_ties) / total_boards,
        'win': total_wins / total_boards,
        'tie': total_ties / total_boards,
        'lose': total_losses / total_boards,
        'by_hand': by_hand,
    }
