# Signal characterization: decisions and validation

Human-selected scope: MC_Maze Small's exact pinned training asset; 5, 20, and
50 ms bins; descriptive statistics before population models. All 100 source
trials and 142 units are retained, including documented train/val and held-out
unit labels. No transform is fitted or bin width optimized against accuracy.

## PREDICT → LEARN → IMPLEMENT → INTERROGATE → VALIDATE

- **Predict:** wider bins should contain fewer zero-count cells. On identical
  observation intervals, total spikes and pooled per-unit mean rates should
  agree across widths. These expectations are arithmetic checks, not claims
  about a neural mechanism.
- **Learn:** the original observations have trial boundaries and incomplete
  tails. The least common grid for 5/20/50 ms is 100 ms. Matching endpoints
  removes coverage differences while native grids retain more source spikes.
- **Implement:** trial-local half-open bins from SENSE; native and matched
  summaries; no fitted representations. Mean rate is spikes / observed seconds;
  sparsity is the fraction of observed cells with zero counts. Missing counts
  are excluded explicitly. Count variance uses ddof=1; Fano is variance / mean
  across temporal bins, undefined for zero mean or fewer than two observations.
- **Interrogate:** task epochs, different conditions, and train/val trials are
  mixed in these summaries. Temporal Fano is not repeated-trial noise Fano.
  Compare tails and matched intervals before attributing any rate difference
  to binning. Anatomical labels are not inferred from incorrect electrode links.
- **Validate:** conserve spikes for every unit/trial on each retained interval;
  require equal per-unit matched totals across widths; exercise silent/missing
  counts and boundaries with labeled synthetic software fixtures; regenerate
  the real-data JSON twice and compare bytes. Visually inspect all five figures.

Observed results and definitions are in `reports/signal_characterization.md`
and the corresponding JSON. The original NWB is never changed. The metadata
audit preserves every stored link and records the publisher's +96 candidate
without applying it or treating it as independent anatomical verification.

Before a subsequent scientific experiment, the human researcher should select
an event reference, repeated-condition grouping, minimum trial counts, and a
coverage policy. Separate task-epoch effects from across-trial variability before
interpreting Fano as trial-to-trial neural variability. This mission selects no
model and recommends no optimal width.
