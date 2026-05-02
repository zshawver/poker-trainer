"""
Test suite for numpy_eval — validates against the existing Hand.scoreHand().

Run: python test_eval.py
"""

import sys
import os
# Support both script execution (__file__ available) and interactive/notebook use
try:
    _dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _dir = os.getcwd()
if _dir not in sys.path:
    sys.path.insert(0, _dir)
import time
import numpy as np
from collections import Counter
from itertools import combinations

# Import existing evaluator
from hand_Backend import Hand

# Import new evaluator
from numpy_cards import encode_card, encode_hand, decode_hand, FULL_DECK
from numpy_eval import evaluate_hands, hand_category

# Map existing score (1-10) category names for readable output
CATEGORY_NAMES = {
    1: "High Card", 2: "Pair", 3: "Two Pair", 4: "Three of a Kind",
    5: "Straight", 6: "Flush", 7: "Full House", 8: "Four of a Kind",
    9: "Straight Flush", 10: "Royal Flush"
}


def generate_random_hands(n, rng=None):
    """Generate n random 7-card hands as both tuples and encoded arrays."""
    if rng is None:
        rng = np.random.default_rng(42)

    # Generate hands as encoded card IDs
    encoded = np.zeros((n, 7), dtype=np.int8)
    for i in range(n):
        cards = rng.choice(52, size=7, replace=False)
        encoded[i] = cards

    # Convert to legacy tuple format for the old evaluator
    tuple_hands = []
    for i in range(n):
        hand_tuples = decode_hand(encoded[i])
        tuple_hands.append(hand_tuples)

    return encoded, tuple_hands


def make_hand_from_strings(card_strings):
    """Create a hand from human-readable strings like 'Ah', 'Kd', '2c'.

    Rank chars: 2-9, T, J, Q, K, A
    Suit chars: c, h, d, s
    """
    rank_map = {'2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5,
                '8': 6, '9': 7, 'T': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12}
    suit_map = {'c': 0, 'h': 1, 'd': 2, 's': 3}

    encoded = []
    tuples = []
    for s in card_strings:
        rank_0 = rank_map[s[0]]
        suit_0 = suit_map[s[1]]
        card_id = rank_0 * 4 + suit_0
        encoded.append(card_id)
        tuples.append((rank_0 + 1, suit_0 + 1))  # 1-based for legacy

    return np.array(encoded, dtype=np.int8), tuples


def test_category_agreement(n=100000):
    """Test that numpy evaluator agrees with legacy on hand categories."""
    print(f"\n=== Category Agreement Test ({n:,} random hands) ===")

    encoded, tuple_hands = generate_random_hands(n)

    # Evaluate with legacy
    t0 = time.perf_counter()
    legacy_scores = [Hand.scoreHand(h) for h in tuple_hands]
    legacy_time = time.perf_counter() - t0

    # Evaluate with numpy
    t0 = time.perf_counter()
    numpy_scores = evaluate_hands(encoded)
    numpy_time = time.perf_counter() - t0

    numpy_categories = hand_category(numpy_scores)

    # Compare
    legacy_arr = np.array(legacy_scores, dtype=np.int32)
    mismatches = np.where(legacy_arr != numpy_categories)[0]

    # Known bug in legacy checkStraightFlush: returns False too early
    # in the loop (line 650), missing straight flushes when the first
    # window doesn't match. These show up as legacy=6 (Flush) when
    # numpy correctly identifies them as 9 (Straight Flush) or 10 (Royal Flush).
    known_bug_count = 0
    real_mismatches = []
    for idx in mismatches:
        if legacy_scores[idx] == 6 and int(numpy_categories[idx]) in (9, 10):
            known_bug_count += 1
        else:
            real_mismatches.append(idx)

    if known_bug_count > 0:
        print(f"  INFO: {known_bug_count} hands are straight flushes that "
              f"legacy misclassifies as flushes (known bug in checkStraightFlush)")

    if len(real_mismatches) == 0:
        print(f"  PASS: All {n:,} hands agree on category "
              f"(excluding {known_bug_count} known legacy bugs)")
    else:
        print(f"  FAIL: {len(real_mismatches)} real mismatches out of {n:,}")
        for idx in real_mismatches[:10]:
            print(f"    Hand {idx}: legacy={legacy_scores[idx]} "
                  f"({CATEGORY_NAMES[legacy_scores[idx]]}), "
                  f"numpy={numpy_categories[idx]} "
                  f"({CATEGORY_NAMES.get(int(numpy_categories[idx]), '?')})")
            print(f"    Cards: {tuple_hands[idx]}")

    has_real_failures = len(real_mismatches) > 0

    # Category distribution
    dist = Counter(legacy_scores)
    print(f"\n  Category distribution:")
    for cat in sorted(dist.keys()):
        pct = dist[cat] / n * 100
        print(f"    {CATEGORY_NAMES[cat]:20s}: {dist[cat]:>7,} ({pct:5.2f}%)")

    # Timing
    print(f"\n  Legacy time:  {legacy_time:.3f}s ({n/legacy_time:,.0f} hands/sec)")
    print(f"  NumPy time:   {numpy_time:.3f}s ({n/numpy_time:,.0f} hands/sec)")
    print(f"  Speedup:      {legacy_time/numpy_time:.1f}x")

    return not has_real_failures


def test_edge_cases():
    """Test specific hand types that are tricky to evaluate."""
    print("\n=== Edge Case Tests ===")
    all_pass = True

    cases = [
        # (name, cards, expected_category)
        ("Royal flush (spades)",
         ['Ts', 'Js', 'Qs', 'Ks', 'As', '2c', '3d'],
         10),

        ("Straight flush (5-high, wheel)",
         ['Ac', '2c', '3c', '4c', '5c', 'Kd', 'Qh'],
         9),

        ("Straight flush (9-high)",
         ['5h', '6h', '7h', '8h', '9h', 'Kd', '2c'],
         9),

        ("Four of a kind",
         ['8c', '8h', '8d', '8s', 'Ac', 'Kd', '2h'],
         8),

        ("Full house (basic)",
         ['Jc', 'Jh', 'Jd', '9s', '9c', '2h', '3d'],
         7),

        ("Full house (two trips)",
         ['7c', '7h', '7d', '3c', '3h', '3d', 'Ks'],
         7),

        ("Flush (7 suited cards)",
         ['2h', '4h', '6h', '8h', 'Th', 'Qh', 'Ah'],
         6),

        ("Flush (5 suited + pair)",
         ['2h', '4h', '6h', '8h', 'Th', '2d', '3c'],
         6),

        ("Straight (ace-high)",
         ['Tc', 'Jd', 'Qh', 'Ks', 'Ac', '2d', '3h'],
         5),

        ("Straight (ace-low, wheel)",
         ['Ac', '2d', '3h', '4s', '5c', 'Kd', 'Qh'],
         5),

        ("Straight (middle)",
         ['5c', '6d', '7h', '8s', '9c', '2d', '3h'],
         5),

        ("Three of a kind",
         ['Tc', 'Th', 'Td', '2s', '5c', '8d', 'Kh'],
         4),

        ("Two pair",
         ['Ac', 'Ad', 'Kh', 'Ks', '2c', '3d', '5h'],
         3),

        ("Two pair (three pairs in 7 cards)",
         ['Ac', 'Ad', 'Kh', 'Ks', '5c', '5d', '2h'],
         3),

        ("One pair",
         ['Jc', 'Jd', '2h', '4s', '6c', '8d', 'Th'],
         2),

        ("High card",
         ['2c', '4d', '6h', '8s', 'Tc', 'Qd', 'Ah'],
         1),
    ]

    for name, cards, expected in cases:
        encoded, tuples = make_hand_from_strings(cards)

        # Legacy check
        legacy_score = Hand.scoreHand(tuples)

        # Numpy check
        hands_arr = encoded.reshape(1, 7)
        numpy_score = hand_category(evaluate_hands(hands_arr))[0]

        legacy_ok = legacy_score == expected
        numpy_ok = int(numpy_score) == expected
        status = "PASS" if (legacy_ok and numpy_ok) else "FAIL"

        if status == "FAIL":
            all_pass = False
            print(f"  {status}: {name}")
            print(f"    Expected: {expected} ({CATEGORY_NAMES[expected]})")
            print(f"    Legacy:   {legacy_score} ({CATEGORY_NAMES[legacy_score]})")
            print(f"    NumPy:    {numpy_score} ({CATEGORY_NAMES.get(int(numpy_score), '?')})")
        else:
            print(f"  {status}: {name}")

    return all_pass


def test_tiebreaker_ordering():
    """Test that composite scores correctly order hands within same category."""
    print("\n=== Tiebreaker Ordering Tests ===")
    all_pass = True

    # Pairs of hands where first should beat second
    ordered_pairs = [
        # Higher pair beats lower pair
        ("Pair of aces vs pair of kings",
         ['Ac', 'Ad', '2h', '3s', '5c', '7d', '9h'],
         ['Kc', 'Kd', '2h', '3s', '5c', '7d', '9h']),

        # Same pair, better kicker
        ("Pair of aces, K kicker vs Q kicker",
         ['Ac', 'Ad', 'Kh', '3s', '5c', '7d', '9h'],
         ['Ac', 'Ad', 'Qh', '3s', '5c', '7d', '9h']),

        # Higher two pair
        ("Aces and kings vs aces and queens",
         ['Ac', 'Ad', 'Kh', 'Ks', '2c', '3d', '5h'],
         ['Ac', 'Ad', 'Qh', 'Qs', '2c', '3d', '5h']),

        # Higher straight
        ("9-high straight vs 8-high straight",
         ['5c', '6d', '7h', '8s', '9c', '2d', '3h'],
         ['4c', '5d', '6h', '7s', '8c', '2d', '3h']),

        # Ace-high straight beats king-high straight
        ("Ace-high straight vs king-high straight",
         ['Tc', 'Jd', 'Qh', 'Ks', 'Ac', '2d', '3h'],
         ['9c', 'Td', 'Jh', 'Qs', 'Kc', '2d', '3h']),

        # Higher flush
        ("Ace-high flush vs king-high flush",
         ['Ah', '9h', '7h', '5h', '3h', '2c', '4d'],
         ['Kh', '9h', '7h', '5h', '3h', '2c', '4d']),

        # Higher full house (trips)
         ("Kings full of twos vs queens full of jacks",
         ['Kc', 'Kd', 'Kh', '2s', '2c', '3d', '5h'],
         ['Qc', 'Qd', 'Qh', 'Js', 'Jc', '3d', '5h']),

        # Higher four of a kind
        ("Quad aces vs quad kings",
         ['Ac', 'Ad', 'Ah', 'As', '2c', '3d', '5h'],
         ['Kc', 'Kd', 'Kh', 'Ks', '2c', '3d', '5h']),

        # Flush beats straight
        ("Flush vs straight",
         ['2h', '4h', '6h', '8h', 'Th', 'Kd', '3c'],
         ['5c', '6d', '7h', '8s', '9c', '2d', '3h']),
    ]

    for name, better_cards, worse_cards in ordered_pairs:
        enc_better, _ = make_hand_from_strings(better_cards)
        enc_worse, _ = make_hand_from_strings(worse_cards)

        hands = np.stack([enc_better, enc_worse]).reshape(2, 7)
        scores = evaluate_hands(hands)

        if scores[0] > scores[1]:
            print(f"  PASS: {name}")
        else:
            all_pass = False
            print(f"  FAIL: {name}")
            cat0 = hand_category(scores[0:1])[0]
            cat1 = hand_category(scores[1:2])[0]
            print(f"    Better: score={scores[0]}, cat={cat0}")
            print(f"    Worse:  score={scores[1]}, cat={cat1}")

    return all_pass


def test_tie_detection():
    """Test that identical-strength hands produce equal composite scores."""
    print("\n=== Tie Detection Tests ===")
    all_pass = True

    # Hands that should tie
    ties = [
        # Same straight, different suits
        ("Same straight different suits",
         ['5c', '6d', '7h', '8s', '9c', '2d', '3h'],
         ['5d', '6h', '7s', '8c', '9d', '2h', '3c']),

        # Same flush strength is harder to construct — skip
        # Same pair with same kickers
        ("Same pair same kickers",
         ['Ac', 'Ad', 'Kh', 'Qs', '9c', '3d', '2h'],
         ['Ah', 'As', 'Kd', 'Qc', '9h', '3c', '2d']),
    ]

    for name, hand1, hand2 in ties:
        enc1, _ = make_hand_from_strings(hand1)
        enc2, _ = make_hand_from_strings(hand2)

        hands = np.stack([enc1, enc2]).reshape(2, 7)
        scores = evaluate_hands(hands)

        if scores[0] == scores[1]:
            print(f"  PASS: {name} (tie detected)")
        else:
            all_pass = False
            print(f"  FAIL: {name} (should tie but scores differ)")
            print(f"    Hand 1 score: {scores[0]}")
            print(f"    Hand 2 score: {scores[1]}")

    return all_pass


def test_performance_benchmark():
    """Benchmark the numpy evaluator on 1M hands."""
    print("\n=== Performance Benchmark ===")
    n = 1_000_000
    rng = np.random.default_rng(123)

    # Generate random hands
    encoded = np.zeros((n, 7), dtype=np.int8)
    for i in range(n):
        encoded[i] = rng.choice(52, size=7, replace=False)

    # Warm up
    _ = evaluate_hands(encoded[:1000])

    # Benchmark
    t0 = time.perf_counter()
    scores = evaluate_hands(encoded)
    elapsed = time.perf_counter() - t0

    print(f"  Evaluated {n:,} hands in {elapsed:.3f}s")
    print(f"  Throughput: {n/elapsed:,.0f} hands/sec")
    print(f"  Category distribution:")
    cats = hand_category(scores)
    for cat in range(1, 11):
        count = (cats == cat).sum()
        if count > 0:
            print(f"    {CATEGORY_NAMES[cat]:20s}: {count:>8,} ({count/n*100:5.2f}%)")


if __name__ == "__main__":
    results = []

    results.append(("Edge Cases", test_edge_cases()))
    results.append(("Tiebreaker Ordering", test_tiebreaker_ordering()))
    results.append(("Tie Detection", test_tie_detection()))
    results.append(("Category Agreement", test_category_agreement()))
    test_performance_benchmark()

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    all_pass = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_pass = False

    if all_pass:
        print("\nAll tests passed!")
    else:
        print("\nSome tests FAILED.")
        sys.exit(1)
