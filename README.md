# Joint Order Selection, Allocation, Batching and Picking 

This project contains accompanying code for Zalando Team BART's (Batching Algorithms) publication [Joint Order Selection, Allocation, Batching and Picking for Large Scale Warehouses](https://arxiv.org/abs/2401.04563).
The instances used to create results in the paper are stored in `instances.zip`.

## How to use

1. Clone this project and copy the files into your own project
2. Generate batching instances via `python generate_instances.py` (any Python 3.6+ works). For each generated instance (per default in the `instances` folder) four files will be created: `{articles, orders, parameters, warehouse_items}.json`. 
3. Run the Distance Greedy Algorithm (DGA) via `python solve_instances.py`. Two files will be stored per instance under `instances/<instance>/dga/`: `batches.json` and `statistics.json`. The runtime in `statistics.json` covers the algorithm only, not reading the instance from disk.
4. Run the Randomized DGA via `python solve_instances.py -a rdga`, which writes to `instances/<instance>/rdga/`, optionally with `-k <N>` (default `1`) to sample `N` random orders per step and take the best of them, e.g. `python solve_instances.py -a rdga -k 50`.
5. Write your own solver to outperform these baseline algorithms :)

Run the tests with `python -m unittest discover`.


## Randomized DGA: configurable best-of-`k` sampling (`-k`)

The Randomized DGA (RDGA) built each batch by repeatedly picking **one** random order from the remaining pool and adding it as-is, with no comparison against alternatives. This generalizes that single random pick into a **best-of-`k` random sample**:

- `distance_greedy_algorithm/solver.py`'s `greedy_solver()` now takes a `k: int = None` parameter (replacing the old `choose_random_order: bool` flag). `k=None` is plain DGA: deterministic, evaluates every remaining order at each step, unchanged from before. `k=<int>` is RDGA: at each step, `min(k, pool size)` orders are sampled uniformly at random, without replacement, from the remaining pool, and the best of that sample (by the same cost function DGA uses to compare candidates) is picked. `k=1` reproduces the original RDGA behavior.
- `solve_instances.py` exposes this as a new `-k` CLI flag (default `1`, ignored when `-a dga`): `python solve_instances.py -a rdga -k 50` samples 50 random orders per step and takes the best of them.
- This makes `k` a tunable quality/speed dial sitting between RDGA's original speed (`k=1`) and DGA's quality (large `k`).
- The random-order-picking implementation changed under the hood (from `random.randrange` to `random.sample`), but this does *not* break reproducibility: CPython's `random.sample(range(n), 1)` reduces to a single `random._randbelow(n)` call internally, exactly like `random.randrange(n)` does, so it consumes the RNG identically. Verified directly: replaying the previous RDGA code (`choose_random_order=True`) against the new `k=1` path under the same seed produces byte-identical order sequences and objective values, across multiple seeds and instance sizes. `-a rdga -k 1` (and `-a dga`, unaffected either way) remain bit-for-bit reproducible against prior runs.

### Experimental results

Measured via `python solve_instances.py -a rdga -k <K>` on the `medium-0` and `large-0` demo instances, compared against the DGA baseline. DGA is deterministic (single run); RDGA is randomized, so each `k` was run with RNG seeds 1 through 10 and the results averaged:

**medium-0** (5,000 orders, item goal 2,659):

| Algorithm | Avg. time | Avg. # picklists | Avg. objective (total distance) |
|---|---:|---:|---:|
| dga         | 176s  | 825   | 65,410    |
| rdga, k=500 | 25.2s | 872.2 | 68,828.4  |
| rdga, k=50  | 2.1s  | 925.0 | 79,819.4  |
| rdga, k=1   | 0.13s | 907.0 | 138,374.0 |

**large-0** (50,000 orders, item goal 26,349):

| Algorithm | Avg. time | Avg. # picklists | Avg. objective (total distance) |
|---|---:|---:|---:|
| dga          | 16,419s (4h 33m) | 10,882   | 605,888     |
| rdga, k=5000 | 1,814.2s (~30m)  | 11,216.4 | 627,581.2   |
| rdga, k=500  | 193.1s (3m 13s)  | 12,135.2 | 713,235.2   |
| rdga, k=50   | 26.3s            | 13,706.2 | 857,581.6   |
| rdga, k=1    | 1.5s             | 14,150.9 | 1,490,776.8 |

Observations:
- Quality improves and runtime grows monotonically with `k` on both instances, converging toward DGA's result:
   - on `medium-0`, `k=500` (10% of its order pool) lands within ~5.2% of DGA's objective while running ~7x faster than DGA
   - on `large-0`, `k=5000` (10% of its order pool) lands within ~3.6% of DGA's objective while running ~9x faster.
- From RDGA run on `large-0`, runtime appears to scale almost exactly linearly with `k` (e.g., `k=500`->`k=5000` is a 10x increase in `k` for a ~9x increase in runtime).
- The gap to DGA at a fixed `k` widens as the order pool grows, since a fixed sample size covers a shrinking fraction of a bigger pool (`k=500` is 10% of `medium-0`'s 5,000-order pool but only 1% of `large-0`'s 50,000-order pool).
- All 70 runs (2 instances x `k` in {1, 50, 500} plus `large-0`'s `k=5000`, x 10 seeds) are feasible (`Instance.check_feasibility()` passes). Variance across seeds is fairly tight at every `k` (e.g. `large-0`'s `k=500` objective ranges 711,150-715,970 across seeds, `k=5000` ranges 625,020-630,034); picklist counts shrink toward DGA's as `k` grows, reflecting better order sequencing at higher `k`.


## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our process for submitting pull requests to us, and please ensure
you follow the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
