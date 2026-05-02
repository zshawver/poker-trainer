"""
Test suite for the vectorized hand evaluator.

Run from backend/: pytest tests/test_evaluator.py
Or as a script:    python -m tests.test_evaluator
"""

import sys
import time
import numpy as np

from src.engine.cards import encode_card, encode_hand, decode_hand, FULL_DECK
from src.engine.evaluator import evaluate_hands, hand_category

# Map existing score (1-10) category names for readable output
CATEGORY_NAMES = {
    1: "High Card", 2: "Pair", 3: "Two Pair", 4: "Three of a Kind",
    5: "Straight", 6: "Flush", 7: "Full House", 8: "Four of a Kind",
    9: "Straight Flush", 10: "Royal Flush"
}


def make_hand_from_strings(card_strings):
    """Create a hand from human-readable strings like 'Ah', 'Kd', '2c'.

    Rank chars: 2-9, T, J, Q, K, A
    Suit chars: c, h, d, s
    """
    rank_map = {'2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5,
                '8': 6, '9': 7, 'T': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12}
    suit_map = {'c': 0, 'h': 1, 'd': 2, 's': 3}

    encoded = []
    for s in card_strings:
        rank_0 = rank_map[s[0]]
        suit_0 = suit_map[s[1]]
        card_id = rank_0 * 4 + suit_0
        encoded.append(card_id)

    return np.array(encoded, dtype=np.int8)


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
        encoded = make_hand_from_strings(cards)

        hands_arr = encoded.reshape(1, 7)
        numpy_score = int(hand_category(evaluate_hands(hands_arr))[0])

        if numpy_score == expected:
            print(f"  PASS: {name}")
        else:
            all_pass = False
            print(f"  FAIL: {name}")
            print(f"    Expected: {expected} ({CATEGORY_NAMES[expected]})")
            print(f"    NumPy:    {numpy_score} ({CATEGORY_NAMES.get(numpy_score, '?')})")

    assert all_pass, "Some edge case categories disagreed with the expected value"


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
        enc_better = make_hand_from_strings(better_cards)
        enc_worse = make_hand_from_strings(worse_cards)

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

    assert all_pass, "Some tiebreaker orderings were wrong"


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
        enc1 = make_hand_from_strings(hand1)
        enc2 = make_hand_from_strings(hand2)

        hands = np.stack([enc1, enc2]).reshape(2, 7)
        scores = evaluate_hands(hands)

        if scores[0] == scores[1]:
            print(f"  PASS: {name} (tie detected)")
        else:
            all_pass = False
            print(f"  FAIL: {name} (should tie but scores differ)")
            print(f"    Hand 1 score: {scores[0]}")
            print(f"    Hand 2 score: {scores[1]}")

    assert all_pass, "Some hands that should tie produced different scores"


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
    failures = []
    for name, fn in [
        ("Edge Cases", test_edge_cases),
        ("Tiebreaker Ordering", test_tiebreaker_ordering),
        ("Tie Detection", test_tie_detection),
    ]:
        try:
            fn()
        except AssertionError as e:
            failures.append((name, str(e)))
    test_performance_benchmark()

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    if not failures:
        print("All tests passed!")
    else:
        for name, msg in failures:
            print(f"  FAIL: {name} -- {msg}")
        sys.exit(1)
