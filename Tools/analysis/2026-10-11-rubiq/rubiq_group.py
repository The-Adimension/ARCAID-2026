"""Torch-free check of RubiQ's lattice group and module selection.

Copies, without changes in logic, RubiQ/bench/harness.py lines 138-250 (_lattice_geometry,
_verify_parity's sign rule, _bytes_to_group_element, _prf_element, _server_config,
_active_identity_indices) and the selection rules of _RubiQTrainer._active_for_client
(lines 513-521) and _RandomCSITrainer (random_active, lines 513-516), and the module sizes
of CSIModule (lines 258-271) with d_s = 128. Prints every number the 2026-10-11 note cites.

Usage: python rubiq_group.py     (sympy optional, for the group order)
"""
from __future__ import annotations

import collections
import hashlib
import hmac
import math
import random
import statistics as st

N = 3
NUM = N ** 3
D_S = 128


def p2i(x, y, z):
    return x * N * N + y * N + z


def i2p(i):
    return (i // (N * N), (i % (N * N)) // N, i % N)


CANON = [p2i(*c) for c in [(0, 0, 0), (0, 1, 1), (0, 2, 2), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 2), (2, 2, 0)]]
IDENT = list(range(NUM))


def compose(p1, p2):
    return [p1[p2[i]] for i in range(NUM)]


def invert(p):
    q = [0] * NUM
    for i, j in enumerate(p):
        q[j] = i
    return q


def make_cw(axis, layer):
    perm = list(IDENT)
    for i in range(NUM):
        c = list(i2p(i))
        if c[axis] != layer:
            continue
        a1, a2 = [a for a in range(3) if a != axis]
        c1 = c[a1]
        c[a1], c[a2] = c[a2], (N - 1) - c1
        perm[i] = p2i(*c)
    return perm


GENS = []
for ax in range(3):
    for ly in range(N):
        cw = make_cw(ax, ly)
        GENS += [cw, compose(compose(cw, cw), cw)]


def odd(p):
    seen, s = set(), 0
    for start in range(NUM):
        if start in seen:
            continue
        j, L = start, 0
        while j not in seen:
            seen.add(j)
            j = p[j]
            L += 1
        s ^= (L - 1) % 2
    return s


def prf(secret, rnd, max_moves=15):
    h = hmac.new(secret, rnd.to_bytes(8, "big"), hashlib.sha256).digest()
    g = list(IDENT)
    for b in h[:max_moves]:
        gen = GENS[b % len(GENS)]
        g = [gen[g[i]] for i in range(NUM)]
    return g


def rubiq_set(client, rnd):
    eff = compose(prf(b"rubiq_public_seed_v1", rnd, 10), prf(f"client_{client}".encode(), rnd))
    inv = invert(eff)
    return [inv[p] for p in CANON]


def ptype(i):
    return {0: "corner", 1: "edge", 2: "centre", 3: "core"}[sum(c == 1 for c in i2p(i))]


DIM = {"corner": 96, "edge": 64, "centre": 48, "core": 32}


def module_params(i):
    d = DIM[ptype(i)]
    return (D_S * d + d) + 2 * d + (d * d + d) + (d * D_S + D_S)


def depth(s):
    return len({i2p(i)[0] for i in s})


def main():
    print("generator parities (1 = odd):", [odd(g) for g in GENS])
    fixed = [i for i in range(NUM) if all(g[i] == i for g in GENS)]
    print("positions fixed by every generator:", fixed, "(core index", p2i(1, 1, 1), ")")
    print("canonical path type mix:", dict(collections.Counter(ptype(i) for i in CANON)))
    try:
        from sympy.combinatorics import Permutation, PermutationGroup
        G = PermutationGroup([Permutation(g) for g in GENS])
        print("group order:", G.order(), "orbits:", [sorted(o) for o in G.orbits()])
    except ImportError:
        print("group order: sympy not installed")

    sets, freq, mixes = collections.Counter(), collections.Counter(), collections.Counter()
    for k in range(10):
        for r in range(10000):
            s = tuple(sorted(rubiq_set(k, r)))
            sets[s] += 1
            freq.update(s)
            mixes[tuple(sorted(collections.Counter(ptype(i) for i in s).items()))] += 1
    print("rubiq: client-rounds=100000 distinct active sets:", len(sets), "type mixes:", dict(mixes))
    print("rubiq: core activations:", freq[13], "| per-module frequency min/max (non-core):",
          min(freq[i] for i in range(NUM) if i != 13), max(freq[i] for i in range(NUM) if i != 13))

    rub = [rubiq_set(k, r) for k in range(10) for r in range(2000)]
    rng = random.Random(0)
    rnd = [rng.sample(range(NUM), len(CANON)) for _ in range(20000)]
    for name, ss in (("rubiq", rub), ("random_csi", rnd)):
        P = [sum(module_params(i) for i in s) for s in ss]
        print(f"{name}: active params mean={st.mean(P):,.0f} min={min(P):,} max={max(P):,}; "
              f"depth (x-layers) = {dict(sorted(collections.Counter(depth(s) for s in ss).items()))}")
    print("all 27 modules params:", f"{sum(module_params(i) for i in range(NUM)):,}")
    print("random_csi: P(core active) = 8/27 = %.4f; P(same type mix as rubiq) = %.4f" % (
        8 / 27, math.comb(8, 3) * math.comb(12, 4) * math.comb(6, 1) / math.comb(27, 8)))


if __name__ == "__main__":
    main()
