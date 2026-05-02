"""
Vectorized poker hand evaluator using NumPy.

Evaluates N 7-card hands simultaneously with no Python loops over N.
Returns composite scores that encode both hand category and tiebreaker,
so a single integer comparison determines the winner.

Composite score layout (int64):
    category * 10^8 + tiebreaker
    where category 1-10 (high card through royal flush)
    and tiebreaker is a base-13 encoded ranking of relevant cards.
"""

import numpy as np

# Hand categories
HIGH_CARD = 1
PAIR = 2
TWO_PAIR = 3
THREE_OF_A_KIND = 4
STRAIGHT = 5
FLUSH = 6
FULL_HOUSE = 7
FOUR_OF_A_KIND = 8
STRAIGHT_FLUSH = 9
ROYAL_FLUSH = 10

CATEGORY_SCALE = np.int64(10**8)

# Powers of 13 for tiebreaker encoding (up to 5 kicker positions)
_POW13 = np.array([13**4, 13**3, 13**2, 13, 1], dtype=np.int64)


def evaluate_hands(hands):
    """Evaluate N 7-card poker hands.

    Parameters
    ----------
    hands : np.ndarray of shape (N, 7), dtype int8
        Card IDs 0-51 for each hand.

    Returns
    -------
    np.ndarray of shape (N,), dtype int64
        Composite scores. Higher is better.
    """
    n = hands.shape[0]

    # Extract ranks (0-12) and suits (0-3)
    ranks = (hands // 4).astype(np.int8)   # (N, 7)
    suits = (hands % 4).astype(np.int8)    # (N, 7)

    # Build rank histogram: (N, 13) — count of each rank per hand
    rank_counts = np.zeros((n, 13), dtype=np.int8)
    for col in range(7):
        np.add.at(rank_counts, (np.arange(n), ranks[:, col]), 1)

    # Build suit histogram: (N, 4)
    suit_counts = np.zeros((n, 4), dtype=np.int8)
    for col in range(7):
        np.add.at(suit_counts, (np.arange(n), suits[:, col]), 1)

    # Rank presence: (N, 13) boolean
    rank_present = rank_counts > 0

    # ========== Detect each hand type ==========

    # --- Flush detection ---
    flush_suit = np.argmax(suit_counts, axis=1)        # (N,)
    is_flush = suit_counts[np.arange(n), flush_suit] >= 5  # (N,)

    # --- Straight detection ---
    straight_high, is_straight = _detect_straight(rank_present)

    # --- Straight flush detection ---
    is_straight_flush = np.zeros(n, dtype=bool)
    sf_high = np.zeros(n, dtype=np.int8)
    flush_candidates = np.where(is_flush & is_straight)[0]
    if len(flush_candidates) > 0:
        is_sf_sub, sf_high_sub = _detect_straight_flush(
            ranks[flush_candidates], suits[flush_candidates],
            flush_suit[flush_candidates]
        )
        is_straight_flush[flush_candidates] = is_sf_sub
        sf_high[flush_candidates] = sf_high_sub

    # --- Royal flush: straight flush with high card = 12 (ace) ---
    is_royal = is_straight_flush & (sf_high == 12)

    # --- Pair-based hand detection from rank_counts ---
    max_count = rank_counts.max(axis=1)                 # (N,)
    num_pairs = (rank_counts == 2).sum(axis=1)          # (N,)
    num_trips = (rank_counts == 3).sum(axis=1)          # (N,)

    is_four_kind = max_count == 4
    is_full_house = (num_trips >= 2) | ((num_trips == 1) & (num_pairs >= 1))
    is_three_kind = (num_trips == 1) & (num_pairs == 0)
    is_two_pair = num_pairs >= 2
    is_one_pair = (num_pairs == 1) & (num_trips == 0)

    # ========== Assign categories (lowest to highest priority) ==========
    category = np.ones(n, dtype=np.int64)  # default: high card

    category[is_one_pair] = PAIR
    category[is_two_pair] = TWO_PAIR
    category[is_three_kind] = THREE_OF_A_KIND
    category[is_straight] = STRAIGHT
    category[is_flush] = FLUSH
    category[is_full_house] = FULL_HOUSE
    category[is_four_kind] = FOUR_OF_A_KIND
    category[is_straight_flush] = STRAIGHT_FLUSH
    category[is_royal] = ROYAL_FLUSH

    # ========== Compute tiebreakers ==========
    tiebreaker = np.zeros(n, dtype=np.int64)

    # High card: top 5 ranks descending
    mask = category == HIGH_CARD
    if mask.any():
        tiebreaker[mask] = _tiebreak_high_card(rank_counts[mask])

    # Pair: pair rank, then top 3 kickers
    mask = category == PAIR
    if mask.any():
        tiebreaker[mask] = _tiebreak_pair(rank_counts[mask])

    # Two pair: higher pair, lower pair, kicker
    mask = category == TWO_PAIR
    if mask.any():
        tiebreaker[mask] = _tiebreak_two_pair(rank_counts[mask])

    # Three of a kind: trip rank, top 2 kickers
    mask = category == THREE_OF_A_KIND
    if mask.any():
        tiebreaker[mask] = _tiebreak_three_kind(rank_counts[mask])

    # Straight: high card of straight
    mask = category == STRAIGHT
    if mask.any():
        tiebreaker[mask] = straight_high[mask].astype(np.int64)

    # Flush: top 5 cards of flush suit
    mask = category == FLUSH
    if mask.any():
        tiebreaker[mask] = _tiebreak_flush(
            ranks[mask], suits[mask], flush_suit[mask]
        )

    # Full house: trip rank, pair rank
    mask = category == FULL_HOUSE
    if mask.any():
        tiebreaker[mask] = _tiebreak_full_house(rank_counts[mask])

    # Four of a kind: quad rank, kicker
    mask = category == FOUR_OF_A_KIND
    if mask.any():
        tiebreaker[mask] = _tiebreak_four_kind(rank_counts[mask])

    # Straight flush: high card
    mask = category == STRAIGHT_FLUSH
    if mask.any():
        tiebreaker[mask] = sf_high[mask].astype(np.int64)

    # Royal flush: all equal (tiebreaker 0 is fine)

    return category * CATEGORY_SCALE + tiebreaker


def hand_category(composite_scores):
    """Extract hand category (1-10) from composite scores."""
    return (composite_scores // CATEGORY_SCALE).astype(np.int32)


# ========== Straight detection ==========

def _detect_straight(rank_present):
    """Detect straights from rank presence array.

    Parameters
    ----------
    rank_present : (N, 13) bool array

    Returns
    -------
    straight_high : (N,) int8 — high card rank of best straight (0 if none)
    is_straight : (N,) bool
    """
    n = rank_present.shape[0]

    # For ace-low straight: create extended presence with ace wrapped to position -1
    # We'll check windows across ranks 0-12, plus the special A-2-3-4-5 case

    # Standard straights: check windows of 5 consecutive ranks
    # rank_present[:, i:i+5] all True means straight with high card i+4
    # Check from highest possible down
    straight_high = np.zeros(n, dtype=np.int8)
    is_straight = np.zeros(n, dtype=bool)

    # Check each possible 5-card window (high card from rank 4 up to rank 12)
    for high in range(12, 3, -1):  # 12, 11, 10, ..., 4
        low = high - 4
        window = rank_present[:, low:high + 1]  # (N, 5)
        has_straight = window.all(axis=1) & ~is_straight
        straight_high[has_straight] = high
        is_straight |= has_straight

    # Ace-low straight: A(12)-2(0)-3(1)-4(2)-5(3) -> high card is 3 (the 5)
    ace_low = (
        rank_present[:, 12] &  # ace
        rank_present[:, 0] &   # deuce
        rank_present[:, 1] &   # three
        rank_present[:, 2] &   # four
        rank_present[:, 3] &   # five
        ~is_straight
    )
    straight_high[ace_low] = 3  # 5-high straight
    is_straight |= ace_low

    return straight_high, is_straight


def _detect_straight_flush(ranks_sub, suits_sub, flush_suit_sub):
    """Detect straight flushes for hands already known to have flush + straight.

    Parameters
    ----------
    ranks_sub : (M, 7) int8
    suits_sub : (M, 7) int8
    flush_suit_sub : (M,) int8

    Returns
    -------
    is_sf : (M,) bool
    sf_high : (M,) int8
    """
    m = ranks_sub.shape[0]

    # Build rank presence for flush-suited cards only
    flush_rank_present = np.zeros((m, 13), dtype=bool)
    for col in range(7):
        is_flush_card = suits_sub[:, col] == flush_suit_sub
        flush_rank_present[np.where(is_flush_card)[0],
                           ranks_sub[np.where(is_flush_card)[0], col]] = True

    # Reuse straight detection on flush-only ranks
    sf_high, is_sf = _detect_straight(flush_rank_present)
    return is_sf, sf_high


# ========== Tiebreaker computation ==========

def _top_k_ranks(rank_counts, count_value, k):
    """Get top k ranks that have exactly count_value occurrences.

    Returns (N, k) int64 array, sorted descending.
    """
    # Mask ranks matching the count value
    match = rank_counts == count_value  # (N, 13)
    # Multiply by rank indices to get rank values (non-matching become 0)
    # But rank 0 (deuce) is valid, so use -1 for non-matching
    rank_indices = np.arange(13, dtype=np.int64)
    vals = np.where(match, rank_indices, -1)  # (N, 13)
    # Sort descending and take top k
    vals = np.sort(vals, axis=1)[:, ::-1][:, :k]
    return vals


def _kickers_excluding(rank_counts, exclude_ranks_mask, k):
    """Get top k kicker ranks excluding certain ranks.

    Parameters
    ----------
    rank_counts : (N, 13)
    exclude_ranks_mask : (N, 13) bool — True for ranks to exclude
    k : int

    Returns
    -------
    (N, k) int64 — kicker ranks sorted descending
    """
    rank_indices = np.arange(13, dtype=np.int64)
    present = (rank_counts > 0) & ~exclude_ranks_mask
    vals = np.where(present, rank_indices, -1)
    vals = np.sort(vals, axis=1)[:, ::-1][:, :k]
    return vals


def _tiebreak_high_card(rc):
    """Tiebreaker for high card hands: top 5 ranks."""
    top5 = _top_k_ranks(rc, 1, 5)
    # Also consider ranks with count > 1 shouldn't appear here,
    # but for safety use all present ranks
    rank_indices = np.arange(13, dtype=np.int64)
    present = rc > 0
    vals = np.where(present, rank_indices, -1)
    vals = np.sort(vals, axis=1)[:, ::-1][:, :5]
    return (vals * _POW13).sum(axis=1)


def _tiebreak_pair(rc):
    """Tiebreaker for pair: pair rank, then top 3 kickers."""
    pair_ranks = _top_k_ranks(rc, 2, 1)  # (N, 1)
    pair_mask = rc == 2
    kickers = _kickers_excluding(rc, pair_mask, 3)  # (N, 3)
    combined = np.concatenate([pair_ranks, kickers], axis=1)  # (N, 4)
    # Pad to 5 with zeros
    padded = np.zeros((combined.shape[0], 5), dtype=np.int64)
    padded[:, :4] = combined
    return (padded * _POW13).sum(axis=1)


def _tiebreak_two_pair(rc):
    """Tiebreaker for two pair: high pair, low pair, kicker."""
    pair_ranks = _top_k_ranks(rc, 2, 2)  # (N, 2) — already sorted desc
    pair_mask = rc == 2
    # Handle 3-pair case: take top 2 pairs, kicker from remaining
    kickers = _kickers_excluding(rc, pair_mask, 1)  # (N, 1)
    # But if there are 3 pairs, the lowest pair ranks as a kicker candidate
    # The kicker is the max of: lowest pair rank and highest non-pair rank
    n = rc.shape[0]
    all_pair_ranks = _top_k_ranks(rc, 2, 3)  # (N, 3), may have -1
    third_pair = all_pair_ranks[:, 2:3]  # (N, 1), -1 if no third pair
    best_kicker = np.maximum(kickers, third_pair)
    combined = np.concatenate([pair_ranks, best_kicker], axis=1)  # (N, 3)
    padded = np.zeros((combined.shape[0], 5), dtype=np.int64)
    padded[:, :3] = combined
    return (padded * _POW13).sum(axis=1)


def _tiebreak_three_kind(rc):
    """Tiebreaker for three of a kind: trip rank, top 2 kickers."""
    trip_ranks = _top_k_ranks(rc, 3, 1)  # (N, 1)
    trip_mask = rc == 3
    kickers = _kickers_excluding(rc, trip_mask, 2)  # (N, 2)
    combined = np.concatenate([trip_ranks, kickers], axis=1)  # (N, 3)
    padded = np.zeros((combined.shape[0], 5), dtype=np.int64)
    padded[:, :3] = combined
    return (padded * _POW13).sum(axis=1)


def _tiebreak_flush(ranks_sub, suits_sub, flush_suit_sub):
    """Tiebreaker for flush: top 5 cards of flush suit, by rank descending."""
    m = ranks_sub.shape[0]
    # Build rank values for flush-suited cards, -1 for non-flush
    flush_ranks = np.where(
        suits_sub == flush_suit_sub[:, np.newaxis],
        ranks_sub.astype(np.int64),
        np.int64(-1)
    )  # (M, 7)
    # Sort descending and take top 5
    flush_ranks = np.sort(flush_ranks, axis=1)[:, ::-1][:, :5]
    return (flush_ranks * _POW13).sum(axis=1)


def _tiebreak_full_house(rc):
    """Tiebreaker for full house: trip rank, then pair rank."""
    trip_ranks = _top_k_ranks(rc, 3, 2)  # (N, 2) — handles two-trips case
    # Best trip is the highest
    best_trip = trip_ranks[:, 0:1]  # (N, 1)

    # Best pair: highest rank with count >= 2, excluding the trip rank
    # This handles: two-trips (lower trip acts as pair) and trip+pair(s)
    n = rc.shape[0]
    rank_indices = np.arange(13, dtype=np.int64)
    # Exclude the best trip rank
    is_candidate = (rc >= 2) & (rank_indices[np.newaxis, :] != best_trip)
    vals = np.where(is_candidate, rank_indices, -1)
    best_pair = vals.max(axis=1, keepdims=True)  # (N, 1)

    combined = np.concatenate([best_trip, best_pair], axis=1)  # (N, 2)
    padded = np.zeros((combined.shape[0], 5), dtype=np.int64)
    padded[:, :2] = combined
    return (padded * _POW13).sum(axis=1)


def _tiebreak_four_kind(rc):
    """Tiebreaker for four of a kind: quad rank, kicker."""
    quad_ranks = _top_k_ranks(rc, 4, 1)  # (N, 1)
    quad_mask = rc == 4
    kickers = _kickers_excluding(rc, quad_mask, 1)  # (N, 1)
    combined = np.concatenate([quad_ranks, kickers], axis=1)  # (N, 2)
    padded = np.zeros((combined.shape[0], 5), dtype=np.int64)
    padded[:, :2] = combined
    return (padded * _POW13).sum(axis=1)
