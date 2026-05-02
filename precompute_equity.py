"""
One-time precomputation of the 169x169 preflop equity lookup table.

Generates preflop_equity.json — a matrix of win/tie/lose rates for every
pair of the 169 canonical hand types (AA, AKs, AKo, ..., 32o).

Run: python precompute_equity.py
Expected time: ~5-10 minutes depending on hardware.
"""

import sys
import os
import json
import time
import numpy as np

try:
    _dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _dir = os.getcwd()
if _dir not in sys.path:
    sys.path.insert(0, _dir)

from poker_variables import rangeHands
from numpy_cards import deal_random_boards, make_hands
from numpy_eval import evaluate_hands


def _canonical_combo(hand_type):
    """Get the first combo for a hand type, converted to int8 card IDs."""
    combo = rangeHands[hand_type][0]  # [(rank1, suit1), (rank2, suit2)]
    c0 = (combo[0][0] - 1) * 4 + (combo[0][1] - 1)
    c1 = (combo[1][0] - 1) * 4 + (combo[1][1] - 1)
    return np.array([c0, c1], dtype=np.int8)


def _find_non_conflicting_combo(hand_type, dead_set):
    """Find a combo for hand_type that doesn't share cards with dead_set."""
    for combo in rangeHands[hand_type]:
        c0 = (combo[0][0] - 1) * 4 + (combo[0][1] - 1)
        c1 = (combo[1][0] - 1) * 4 + (combo[1][1] - 1)
        if c0 not in dead_set and c1 not in dead_set:
            return np.array([c0, c1], dtype=np.int8)
    return None


def build_equity_table(n_samples=10000):
    """Compute 169x169 preflop equity matrix.

    Parameters
    ----------
    n_samples : int
        Monte Carlo samples per matchup. 10000 gives ~0.5% accuracy.

    Returns
    -------
    dict with 'hand_types', 'n_samples', 'matrix'
    """
    hand_types = list(rangeHands.keys())
    n_types = len(hand_types)
    rng = np.random.default_rng(42)

    # Pre-compute canonical combos
    canonical = {ht: _canonical_combo(ht) for ht in hand_types}

    # Initialize results: matrix[i][j] = [win, tie, lose]
    # We'll compute upper triangle (i <= j) and derive lower triangle
    win_matrix = np.zeros((n_types, n_types), dtype=np.float64)
    tie_matrix = np.zeros((n_types, n_types), dtype=np.float64)

    total_pairs = n_types * (n_types + 1) // 2
    computed = 0
    t0 = time.perf_counter()

    for i in range(n_types):
        hero = canonical[hand_types[i]]
        hero_set = set(int(c) for c in hero)

        for j in range(i, n_types):
            # Find non-conflicting villain combo
            villain = canonical[hand_types[j]]
            if int(villain[0]) in hero_set or int(villain[1]) in hero_set:
                villain = _find_non_conflicting_combo(hand_types[j], hero_set)
                if villain is None:
                    # Impossible matchup (e.g., same pair with not enough suits)
                    # Treat as 50/50
                    win_matrix[i, j] = 0.5
                    tie_matrix[i, j] = 0.0
                    computed += 1
                    continue

            dead = np.concatenate([hero, villain])
            boards = deal_random_boards(n_samples, dead, 5, rng=rng)

            hero_hands = make_hands(hero, boards)
            villain_hands = make_hands(villain, boards)

            hero_scores = evaluate_hands(hero_hands)
            villain_scores = evaluate_hands(villain_hands)

            w = float((hero_scores > villain_scores).sum()) / n_samples
            t = float((hero_scores == villain_scores).sum()) / n_samples

            win_matrix[i, j] = w
            tie_matrix[i, j] = t

            computed += 1
            if computed % 500 == 0:
                elapsed = time.perf_counter() - t0
                pct = computed / total_pairs * 100
                rate = computed / elapsed
                eta = (total_pairs - computed) / rate
                print(f"  {computed:,}/{total_pairs:,} ({pct:.1f}%) "
                      f"- {elapsed:.0f}s elapsed, ~{eta:.0f}s remaining")

    # Fill lower triangle from symmetry
    for i in range(n_types):
        for j in range(i):
            win_matrix[i, j] = 1.0 - win_matrix[j, i] - tie_matrix[j, i]
            tie_matrix[i, j] = tie_matrix[j, i]

    # Build the JSON structure
    matrix = {}
    for i, ht_i in enumerate(hand_types):
        row = {}
        for j, ht_j in enumerate(hand_types):
            w = round(win_matrix[i, j], 5)
            t = round(tie_matrix[i, j], 5)
            l = round(1.0 - w - t, 5)
            row[ht_j] = [w, t, l]
        matrix[ht_i] = row

    return {
        'hand_types': hand_types,
        'n_samples': n_samples,
        'matrix': matrix,
    }


def main():
    print("Precomputing 169x169 preflop equity table...")
    print(f"  10,000 samples per matchup")
    print(f"  {169 * 170 // 2:,} unique matchups to compute")
    print()

    t0 = time.perf_counter()
    table = build_equity_table(n_samples=10000)
    elapsed = time.perf_counter() - t0

    # Save
    out_path = os.path.join(_dir, 'preflop_equity.json')
    with open(out_path, 'w') as f:
        json.dump(table, f, separators=(',', ':'))

    file_size = os.path.getsize(out_path)
    print(f"\nDone in {elapsed:.1f}s")
    print(f"Saved to {out_path} ({file_size / 1024 / 1024:.1f} MB)")

    # Spot checks
    m = table['matrix']
    aa_kk = m['AA']['KK']
    print(f"\nSpot checks:")
    print(f"  AA vs KK: win={aa_kk[0]:.3f}, tie={aa_kk[1]:.3f}, "
          f"lose={aa_kk[2]:.3f} (expected ~0.81 win)")

    aks_qq = m['AKs']['QQ']
    print(f"  AKs vs QQ: win={aks_qq[0]:.3f}, tie={aks_qq[1]:.3f}, "
          f"lose={aks_qq[2]:.3f} (expected ~0.46 win)")

    aa_aa = m['AA']['AA']
    print(f"  AA vs AA: win={aa_aa[0]:.3f}, tie={aa_aa[1]:.3f}, "
          f"lose={aa_aa[2]:.3f} (expected ~0.0/1.0/0.0)")


if __name__ == '__main__':
    main()
