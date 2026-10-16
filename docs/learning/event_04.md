# Event-aligned population activity: what can be learned

The researcher selected the source photobox go cue as primary alignment. A source
offline movement-onset annotation provides a secondary timing comparison. Both
use 20 ms bins from −400 to +1000 ms, without smoothing or timestamp correction.
The event-aligned observation tensor is trials × time bins × units. Each time
bin is a simultaneous 142-unit observation, not an independent trial replicate.

**Signal correlation** conventionally compares neurons' mean responses across
conditions. Here it is Pearson correlation across 21 compatible-condition mean
rates in the declared response epoch. With only three trials per mean, sampling
noise contaminates it; we label it *signal-like* and do not infer reliable tuning.

**Residual correlation** compares fluctuations around an expected response to
the same condition. Expected responses here are specific to both condition and
event-time bin. We compute illustrative residuals, but do not estimate their
correlation matrix: three repeats give a covariance rank ceiling of two for
142 units. The residuals sum to zero because the same trials formed their means;
that constraint is arithmetic, not a biological finding.

**Population covariance** measures joint variation in simultaneous activity.
The total covariance at +300 to +320 ms uses 75 training trial vectors and mixes
task-condition effects with residual fluctuations. It is neither a noise covariance
nor a connectivity map. Zero-variance units have undefined Pearson coefficients;
they remain NaN/gray. Very sparse shared observations can produce coefficients
of one without robust coupling. These distinctions follow the discussion in
[Cohen and Kohn (2011)](https://www.nature.com/articles/nn.2842).

Uncertainty uses entire trial vectors, sampled within compatible conditions;
neurons and temporal bins are never counted as independent replicates. Bootstrap
bands are pointwise and weakly calibrated with two or three repeats per stratum.
Independence of source trials is an assumption, not established from this session.

PREDICT → LEARN → IMPLEMENT → INTERROGATE → VALIDATE:

- Predict that event alignment may expose reproducible descriptive profiles;
  do not equate an average transient with a causal movement mechanism.
- Learn the actual repetitions and marker provenance first. Maze-only grouping
  mixes target/barrier variants and falsely inflates compatible repetition counts.
- Implement training-only windows and geometry-compatible condition means.
- Interrogate task-stage differences, onset uncertainty, sparse coincidences,
  in-sample centering, and covariance rank limits before interpreting matrices.
- Validate timestamp/bin boundaries, source IDs, coverage, conservation, exclusion
  of validation trials, numerical edge cases, and deterministic report regeneration.

MC_Maze Small supports this descriptive exploration, not reliable condition-time
residual covariance. Audit a larger published variant's repetitions before the
next variability experiment. Model selection, scientific interpretation and the
next event/condition protocol remain human decisions. No PCA or decoder is used.
