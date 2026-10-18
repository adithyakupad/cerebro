"""Regenerate the M023 dynamics report and figures from committed metrics."""

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    result = json.loads(Path('reports/m023_dynamics.json').read_text())
    sessions = result['sessions']
    lines = ['# M023 observed population dynamics', '',
             'Development study: one macaque, one source session and three previously inspected target sessions. '
             'Jan27 first300 trials train source models; Jan30/Feb4/Feb5 first45 trials supply local models, '
             'and next30 trials per date are development evaluation. Original rows75:375 are excluded. '
             'This is not independent final validation.', '',
             '## Primary temporal comparison', '',
             'Fixed source-trained PCA6 plus ridge AR1, one native sample ahead. Neural errors are '
             'source-standardized threshold-crossing count², averaged equally over trials. '
             'Intervals resample contiguous five-trial blocks within dates; dates are not animals. '
             'Static PCA/FA inference and behavior probes are offline; AR forecasts propagate from past neural observations.', '',
             '| Control | Equal-date relative improvement | Paired MSE difference | Conditional 95% interval | Gate |',
             '|---|---:|---:|---|---|']
    for row in result['temporal_gate']['comparisons']:
        low, high = row['conditional_95_block_interval']
        lines.append(f"| {row['control']} | {100 * row['equal_date_mean_relative_improvement']:.3f}% | {row['equal_date_paired_mse_difference']:.6f} | [{low:.6f}, {high:.6f}] | {'PASS' if row['passed'] else 'FAIL'} |")
    lines += ['', '**The fixed temporal promotion gate failed.** Source PCA6 AR1 improves beyond a training mean '
              'and shuffled-training AR, but not by the prespecified 5% against both controls. '
              'No untouched-session temporal outcomes were evaluated. Beating neural persistence is insufficient: '
              'persistence carries preceding-bin observation noise, whereas low-rank predictions remove substantial observation variation.', '',
              '## Complete prespecified ablations', '',
              'PCA/FA dimensions3/6/12; source, local15/local45 models; dimension6 local-scaler sensitivity. '
              'AR ridge1, behavior ridge1000. Local training uses target pool rows only. '
              'No family or dimension is promoted retrospectively. The full machine report contains per-trial losses, '
              'all controls, likelihoods and conditional intervals.', '',
              '| Date | Observation model | d | Fit | Reconstruction neural MSE | h1 neural MSE | h5 neural MSE | Offline behavior MSE flexion² |',
              '|---|---|---:|---|---:|---:|---:|---:|']
    for session in sessions:
        for row in session['comparisons']:
            metrics = row['metrics']
            lines.append(f"| {session['session_id']} | {row['model']} | {row['dimension']} | {row['fit']} | {metrics['reconstruction_neural_mse']['mean_trial']:.6f} | {metrics['h1_latent_ar_neural_mse']['mean_trial']:.6f} | {metrics['h5_latent_ar_neural_mse']['mean_trial']:.6f} | {metrics['offline_behavior_mse_flexion2']['mean_trial']:.6f} |")
    lines += ['', '## Geometry, clocks and coverage', '',
              '| Date | Training covariance cosine | Common commands with ≥2 trials each | Mean phase-trajectory cosine | h1 elapsed seconds | h5 elapsed seconds |',
              '|---|---:|---:|---:|---|---|']
    for session in sessions:
        conditions = session['condition_matching']
        cosines = [value for value in conditions['phase_trajectory_centered_cosine'] if value is not None]
        clocks = session['forecast_actual_elapsed_clock']
        one = clocks['1']
        five = clocks['5']
        lines.append(f"| {session['session_id']} | {session['covariance_frobenius_cosine']:.6f} | {len(conditions['conditions_with_two_repetitions_each'])} | {np.mean(cosines):.6f} | [{one['minimum_seconds']:.3f}, {one['maximum_seconds']:.3f}] | [{five['minimum_seconds']:.3f}, {five['maximum_seconds']:.3f}] |")
    scoring_warnings = sum(row['metrics']['fa_scoring_warning_count'] for session in sessions for row in session['comparisons'])
    fitting_warnings = sum(row['fitting_warning_count'] for session in sessions for row in session['comparisons'])
    max_replay = max(row['checkpoint_replay_max_abs_count_error'] for session in sessions for row in session['comparisons'])
    lines += ['', 'Contact-coordinate alignment establishes a shared recorded feature space, not stable neuron identity. '
              'Reported principal angles map source and local loadings into the same raw-count axes; '
              'this raw-count geometry weights contacts differently from source-standardized neural MSE. '
              'Covariance and geometry changes mix task sampling, observation noise, count statistics and possible physiology. '
              'Ten phase segments are acausal descriptive trial normalization, not synchronized physical movement phases. '
              'Condition subsets differ by date and contain few repeated trials; the cosines do not establish invariant population representations.', '',
              '## Numerical and interpretation limits', '',
              f'All saved PCA/FA forecast checkpoints replayed with maximum absolute raw-count error {max_replay:.3g}. '
              f'Population fitting emitted {fitting_warnings} warnings. FA held-out scoring emitted {scoring_warnings} '
              'NumPy slogdet runtime warnings (divide/overflow/invalid); these are recorded in the machine report. '
              'Every final reported Gaussian likelihood was finite, but this numerical caveat limits interpretation of FA likelihood differences. '
              'Gaussian observation scores describe this continuous approximation, not a count-data likelihood.', '',
              'The model is a two-stage static observation projection plus affine latent AR, not a jointly estimated '
              'maximum-likelihood latent dynamical system or Kalman smoother. No physiological mechanism or causal neural connection is identified. '
              'Source-to-target distribution differences and extra local fit information can improve neural prediction without improving behavior decoding. '
              'A small positive development forecast effect does not independently validate an adaptation policy.', '',
              '## Reproduction', '', '```sh',
              'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 conda run -n cerebro python -m cerebro.research_dynamics',
              'conda run -n cerebro python tools/m023_dynamics_report.py', '```', '',
              'Pinned assets are listed in configs/m023_protocol.json and the referenced LINK manifests. '
              'Raw data and numerical checkpoints remain Git-ignored. Source/config hashes and array hashes are in '
              'reports/m023_dynamics.json. No historical experiment artifact is replaced.', '']
    Path('reports/m023_dynamics.md').write_text('\n'.join(lines))
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    colors = ['#277da8', '#c67619', '#58803c']
    names = ['Persistence', 'Training mean', 'Permuted AR']
    for index, session in enumerate(sessions):
        values = [100 * row['per_date_relative_improvement'][index] for row in result['temporal_gate']['comparisons']]
        axes[0].plot(np.arange(3), values, marker='o', color=colors[index], label=session['session_id'][:10])
        for kind, style in [('pca', '-'), ('fa', '--')]:
            comparisons = [row for row in session['comparisons'] if row['fit'] == 'source' and row['model'] == kind]
            comparisons.sort(key=lambda row: row['dimension'])
            dimensions = [row['dimension'] for row in comparisons]
            errors = [row['metrics']['h1_latent_ar_neural_mse']['mean_trial'] for row in comparisons]
            axes[1].plot(dimensions, errors, linestyle=style, marker='o', color=colors[index], label=f"{session['session_id'][:10]} {kind.upper()}")
    axes[0].axhline(5, color='black', linestyle=':', label='Prespecified 5% threshold')
    axes[0].set_xticks(np.arange(3), names)
    axes[0].set_ylabel('Source PCA6 AR1 relative MSE reduction (%)')
    axes[0].set_title('Development dates remain distinguishable')
    axes[0].legend(fontsize=7)
    axes[1].set_xticks([3, 6, 12])
    axes[1].set_xlabel('Source-fitted latent dimensions')
    axes[1].set_ylabel('Equal-trial one-step MSE (standardized count²)')
    axes[1].set_title('Matched-dimensionality sensitivity')
    axes[1].legend(fontsize=6, ncol=2)
    figure.suptitle('LINK DANDI001201/0.251023.2336 · Monkey N · development rows45:75', fontsize=10)
    root = Path('reports/figures/m023_dynamics_comparison')
    figure.savefig(root.with_suffix('.pdf'), metadata={'CreationDate': None, 'ModDate': None})
    figure.savefig(root.with_suffix('.png'), dpi=180)
    plt.close(figure)


if __name__ == '__main__':
    main()
