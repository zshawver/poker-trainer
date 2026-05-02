"""
Card encoding utilities for vectorized poker simulation.

Encoding: single integer 0-51
    card_id = rank * 4 + suit
    rank = card_id // 4   (0=deuce, 1=three, ..., 12=ace)
    suit = card_id % 4    (0=clubs, 1=hearts, 2=diamonds, 3=spades)

Legacy format (from hand_Backend.py):
    (rank_1based, suit_1based) where rank 1-13, suit 1-4
"""

import numpy as np
from itertools import combinations


# Full deck as a sorted array of 52 card IDs
FULL_DECK = np.arange(52, dtype=np.int8)

# Display lookup tables
_RANK_CHARS = '23456789TJQKA'
_SUIT_CHARS = 'chds'
_RANK_MAP = {c: i for i, c in enumerate(_RANK_CHARS)}
_SUIT_MAP = {c: i for i, c in enumerate(_SUIT_CHARS)}


def encode_card(rank_1based, suit_1based):
    """Convert legacy (rank, suit) tuple to 0-based card ID."""
    return np.int8((rank_1based - 1) * 4 + (suit_1based - 1))


def decode_card(card_id):
    """Convert 0-based card ID to legacy (rank, suit) tuple."""
    return (int(card_id) // 4 + 1, int(card_id) % 4 + 1)


def encode_hand(tuple_list):
    """Convert list of (rank, suit) tuples to int8 array."""
    return np.array(
        [(r - 1) * 4 + (s - 1) for r, s in tuple_list], dtype=np.int8
    )


def decode_hand(arr):
    """Convert int8 array of card IDs to list of (rank, suit) tuples."""
    return [(int(c) // 4 + 1, int(c) % 4 + 1) for c in arr]


def card_str(card_id):
    """Convert card ID to human-readable string like 'As', 'Kh', '2c'."""
    rank = int(card_id) // 4
    suit = int(card_id) % 4
    return _RANK_CHARS[rank] + _SUIT_CHARS[suit]


def cards_str(card_ids):
    """Convert array of card IDs to list of strings."""
    return [card_str(c) for c in card_ids]


def parse_card(s):
    """Parse string like 'As', 'Kh', '2c' to int8 card ID."""
    return np.int8(_RANK_MAP[s[0]] * 4 + _SUIT_MAP[s[1]])


def parse_cards(strings):
    """Parse list of card strings to int8 array."""
    return np.array([parse_card(s) for s in strings], dtype=np.int8)


def normalize_cards(cards):
    """Convert any card format to int8 array.

    Accepts:
    - int8 array (passthrough)
    - list of ints (converted to int8)
    - list of strings like ['As', 'Kh'] (parsed)
    - list of legacy tuples like [(13, 4), (12, 1)] (encoded)
    - None (returns empty array)
    """
    if cards is None:
        return np.array([], dtype=np.int8)
    if isinstance(cards, np.ndarray) and cards.dtype == np.int8:
        return cards
    if not cards:
        return np.array([], dtype=np.int8)
    first = cards[0] if hasattr(cards, '__getitem__') else next(iter(cards))
    if isinstance(first, str):
        return parse_cards(cards)
    if isinstance(first, tuple):
        return encode_hand(cards)
    return np.array(cards, dtype=np.int8)


def build_deck():
    """Return a fresh copy of the 52-card deck as int8 array."""
    return FULL_DECK.copy()


def remaining_deck(dead_cards):
    """Return deck excluding dead cards.

    Parameters
    ----------
    dead_cards : array-like of int8
        Card IDs to exclude.

    Returns
    -------
    np.ndarray of int8
    """
    mask = np.ones(52, dtype=bool)
    mask[dead_cards] = False
    return FULL_DECK[mask]


def deal_random_boards(n, dead_cards, num_cards, rng=None):
    """Generate n random boards from remaining deck.

    Parameters
    ----------
    n : int
        Number of boards to generate.
    dead_cards : array-like of int8
        Cards already dealt (hole cards, known community, etc.).
    num_cards : int
        Number of community cards to draw per board.
    rng : np.random.Generator, optional
        Random number generator for reproducibility.

    Returns
    -------
    np.ndarray of shape (n, num_cards), dtype int8
    """
    if rng is None:
        rng = np.random.default_rng()

    deck = remaining_deck(dead_cards)
    deck_size = len(deck)

    # Generate n permutations and take first num_cards from each
    indices = np.argsort(rng.random((n, deck_size)), axis=1)[:, :num_cards]
    return deck[indices].astype(np.int8)


def enumerate_boards(dead_cards, num_cards):
    """Enumerate all possible boards from remaining deck.

    Parameters
    ----------
    dead_cards : array-like of int8
        Cards already dealt.
    num_cards : int
        Number of cards to draw.

    Returns
    -------
    np.ndarray of shape (C(remaining, num_cards), num_cards), dtype int8
    """
    deck = remaining_deck(dead_cards)
    combos = np.array(
        list(combinations(deck, num_cards)), dtype=np.int8
    )
    return combos


def make_hands(hole_cards, boards):
    """Combine hole cards with boards into 7-card hands.

    Parameters
    ----------
    hole_cards : np.ndarray of shape (2,) or (N, 2)
        Hero's hole cards.
    boards : np.ndarray of shape (N, 5)
        Community boards.

    Returns
    -------
    np.ndarray of shape (N, 7), dtype int8
    """
    if hole_cards.ndim == 1:
        # Single hole card pair, broadcast across all boards
        n = boards.shape[0]
        holes = np.broadcast_to(hole_cards, (n, 2))
    else:
        holes = hole_cards
    return np.concatenate([holes, boards], axis=1).astype(np.int8)
