"""Render M022 frozen development outcomes without fitting any models."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from cerebro.calibration_mechanisms import paired_session_interval


def group_for(session, budget, policy):
    return next(group for group in session['groups'] if group['budget'] == budget and group['policy'] == policy)


def render(results_path, output_directory='reports'):
    results_path = Path(results_path)
    original = json.loads(results_path.read_text())
    frozen_config = json.loads(Path('configs/m022_calibration.json').read_text())
    expected_dates = ['20200130', '20200204', '20200205']
    dates = [session['session'] for session in original['sessions']]
    compatible = original['config'] == frozen_config and dates == expected_dates
    compatible = compatible and original['source_training_bins'] == 21701
    compatible = compatible and original['selected_source_alpha'] == 1000
    compatible = compatible and original['promotion']['selected_method'] is None
    if not compatible:
        raise ValueError('This scientific narrative only renders the frozen M022 negative development study')
    report = copy.deepcopy(original)
    report['full_results_path'] = str(results_path)
    report['full_results_sha256'] = hashlib.sha256(results_path.read_bytes()).hexdigest()
    report['renderer_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report['protocol_commit'] = '56b0a1c'
    report['interpretation'] = {
        'mechanism': 'Finite-calibration estimation variability and allocation sensitivity supported as development statistical contributors; physiological cause unidentified.',
        'mitigation': 'No prespecified mitigation passes the full promotion gate.',
        'independent_validation': 'NOT EXECUTED by null rule, not because no metadata candidates exist. Three candidate dates remain unscored and native eligibility unverified.',
        'biological_unit': 'One Monkey N; three development dates, not three animals.',
    }
    report['diagnostic_contrasts'] = []
    for session in report['sessions']:
        chronological = group_for(session, 15, 'chronological')
        reference = np.asarray(chronological['models']['direct_1']['subset_trial_mse'][0])
        for policy in ('uniform', 'balanced'):
            group = group_for(session, 15, policy)
            subset_losses = np.asarray(group['models']['direct_1']['subset_trial_mse'])
            average_losses = subset_losses.mean(axis=0)
            differences = average_losses - reference
            interval = paired_session_interval([differences], 1000, 5, 22022)
            label_distance = np.array([row['label_mean_distance_squared_posthoc'] for row in group['draw_diagnostics']])
            subset_means = subset_losses.mean(axis=1)
            correlation = None
            if label_distance.std() > 0 and subset_means.std() > 0:
                correlation = float(np.corrcoef(label_distance, subset_means)[0, 1])
            report['diagnostic_contrasts'].append({
                'session': session['session'], 'budget': 15, 'allocation': policy,
                'relative_mse_reduction_from_chronological': float(1 - average_losses.mean() / reference.mean()),
                'paired_mse_difference': float(differences.mean()),
                'conditional_evaluation_trial_block_interval': interval,
                'subset_mse_range_not_confidence_interval': [float(subset_means.min()), float(subset_means.max())],
                'within_policy_label_distance_mse_correlation_posthoc': correlation,
            })
        for group in session['groups']:
            for model in group['models'].values():
                subset_losses = np.asarray(model['subset_trial_mse'])
                model['subset_mean_trial_mse'] = subset_losses.mean(axis=1).tolist()
                if group['policy'] != 'chronological':
                    del model['subset_trial_mse']
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    figures = directory / 'figures'
    figures.mkdir(exist_ok=True)
    figure, axes = plt.subplots(2, 3, figsize=(13, 8))
    colors = ['#0072B2', '#D55E00', '#009E73']
    budgets = original['config']['budgets']
    for index, session in enumerate(original['sessions']):
        axis = axes[0, index]
        for name, label, color in [('direct_1', 'Direct ridge', colors[0]), ('residual_1', 'Source + residual', colors[1]),
                                    ('direct_shrink_0.25', '25% direct shrink (diagnostic)', colors[2])]:
            losses = [group_for(session, budget, 'chronological')['models'][name]['mean_subset_mse'] for budget in budgets]
            axis.plot(budgets, losses, 'o-', label=label, color=color)
        axis.axhline(np.mean(session['frozen_trial_mse']), color='black', linestyle='--', label='Frozen source')
        axis.set(title=session['session'] + ' development', xlabel='Chronological labeled trials', ylabel='Equal-trial MSE (flexion²)')
        axis.set_xticks(budgets)
    axes[0, 0].legend(fontsize=7)
    for session, color in zip(original['sessions'], colors):
        groups = [group_for(session, budget, 'uniform') for budget in budgets]
        fractions = [group['models']['direct_1']['prediction_dispersion'] / group['models']['direct_1']['mean_subset_mse'] for group in groups]
        axes[1, 0].plot(budgets, np.asarray(fractions) * 100, 'o-', color=color, label=session['session'])
        policies = ['chronological', 'uniform', 'balanced']
        allocation_losses = [group_for(session, 15, policy)['models']['direct_1']['mean_subset_mse'] for policy in policies]
        axes[1, 1].plot(range(3), allocation_losses, 'o-', color=color, label=session['session'])
        uniform = group_for(session, 15, 'uniform')
        distances = [row['label_mean_distance_squared_posthoc'] for row in uniform['draw_diagnostics']]
        losses = uniform['models']['direct_1']['subset_trial_mse']
        axes[1, 2].scatter(distances, np.mean(losses, axis=1), alpha=.7, color=color, label=session['session'])
    axes[1, 0].set(xlabel='Uniformly sampled labeled trials', ylabel='Prediction dispersion / subset MSE (%)', title='20 calibration subsets per date')
    axes[1, 0].set_xticks(budgets)
    axes[1, 0].legend(fontsize=8)
    axes[1, 1].set(xticks=range(3), xticklabels=['First 15', 'Uniform 15', 'Balanced 15'], ylabel='Direct ridge equal-trial MSE (flexion²)', title='Balanced uses all 45 command labels')
    axes[1, 2].set(xlabel='Calibration–evaluation label-mean distance\n(flexion²)', ylabel='Direct ridge MSE (flexion²)', title='Post-hoc coverage association\n(not physiology)')
    figure.suptitle('M022: development evidence only — no mitigation promoted, no untouched-session outcomes', fontsize=12)
    figure.text(.5, .015, 'LINK DANDI 001201/0.251023.2336 · Monkey N · source Jan 27 first 300; development first 75 split45/30 · nominal 20-ms native bins', ha='center', fontsize=8)
    figure.tight_layout(rect=(0, .04, 1, .95))
    figure.savefig(figures / 'm022_mechanism_comparison.pdf', metadata={'CreationDate': None, 'ModDate': None})
    figure.savefig(figures / 'm022_mechanism_comparison.png', dpi=170)
    plt.close(figure)
    lines = [
        '# M022: statistical mechanisms of low-budget decoder adaptation', '',
        '**Decision:** no candidate satisfies the frozen development gate. No mitigation is promoted; no previously uninspected session is scored.', '',
        '## Design and lineage', '',
        'The [protocol](../docs/research/m022_protocol.md) was committed at `56b0a1c` before execution; '
        'the owner confirmed the 5% practical threshold before results. Start: v1.0.0 `b780e5cc53f246f4b305d413c4bd1afb962ff42c`. '
        'Jan 27 source first 300 trials (21,701 bins), inner 225/75 alpha selection, selected alpha 1000. '
        'Jan 30/Feb 4/Feb 5 use **only first 75 previously permitted calibration trials**, pool 45 versus pseudo-evaluation 30. '
        'This is development on inspected dates, never independent validation. Original target evaluation rows 75:375 and Feb 6/11/22 outcomes do not enter this study.', '',
        'Native 96-contact threshold-crossing counts and two synchronized normalized finger-flexion targets retain jittered nominal 20-ms clocks. '
        'Prediction is same-bin offline regression, not causal streaming. Native volts/count label conflict and absent quality masks remain disclosed. '
        'Exact asset IDs, SHA256, trial IDs, channel joins, permutation, sample counts, environment, source hashes and all allocation seeds are in the '
        '[machine report](m022_calibration_mechanisms.json). One monkey supplies all dates. No raw recordings or prediction checkpoints are redistributed.', '',
        'Data attribution: Temmar and colleagues, LINK dataset, DANDI 001201 v0.251023.2336, '
        '[version DOI](https://doi.org/10.48324/dandi.001201/0.251023.2336), CC-BY-4.0. '
        '[Author documentation](https://chesteklab.github.io/LINK_dataset/) describes the acquisition and normalized targets.', '',
        '## Primary 15-trial development outcomes', '',
        '| Date | Pool/evaluation bins | Frozen | Direct | Source + residual | Label-only mean | Intercept correction |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for session in original['sessions']:
        models = group_for(session, 15, 'chronological')['models']
        values = [np.mean(session['frozen_trial_mse'])]
        values.extend(models[name]['mean_subset_mse'] for name in ('direct_1', 'residual_1', 'calibration_mean', 'intercept_correction'))
        lines.append(f"| {session['session']} | {session['pool_bins']}/{session['evaluation_bins']} | " + ' | '.join(f'{value:.8f}' for value in values) + ' |')
    lines.extend(['', 'Values are equal-trial MSE in flexion² over 30 whole trials/date. Direct and residual ridge use source scaling and alpha 1000. '
                  'Frozen is better than both on Jan 30/Feb 4 but worse on Feb 5. This heterogeneity prevents a blanket adaptation-failure claim.', '',
                  '## Discriminating findings', '',
                  '| Date | Uniform direct MSE B = 5 → 15 → 30 | Prediction-dispersion fraction B = 5 → 15 → 30 | Balanced 15 change vs chronological 15 |',
                  '|---|---|---|---:|'])
    for session in original['sessions']:
        groups = [group_for(session, budget, 'uniform')['models']['direct_1'] for budget in budgets]
        losses = ' → '.join(f"{group['mean_subset_mse']:.6f}" for group in groups)
        fractions = ' → '.join(f"{100 * group['prediction_dispersion'] / group['mean_subset_mse']:.1f}%" for group in groups)
        contrast = next(row for row in report['diagnostic_contrasts'] if row['session'] == session['session'] and row['allocation'] == 'balanced')
        lines.append(f"| {session['session']} | {losses} | {fractions} | {100 * contrast['relative_mse_reduction_from_chronological']:.2f}% reduction |")
    lines.extend(['',
        '1. **Allocation/coverage contributor supported, not sufficient.** Balanced 15 covers 15 commands versus 6–7 for chronological 15 and 7.5–7.8 on average for uniform 15. '
        'It lowers direct MSE on all three dates, but receives all 45 pool command labels and accesses later pool trials. It is not a free-label or chronology-matched intervention. '
        'Uniform15 improves Jan 30/Feb 4 and worsens Feb 5; chronology is not uniformly harmful. Post-hoc label-distance associations and conditional paired intervals are retained in JSON; no causal physiology follows.',
        '2. **Finite-calibration prediction variability supported.** Across 20 fixed uniform subsets, the exact empirical MSE identity separates ensemble error from prediction dispersion. '
        'Dispersion falls substantially from 5 to 30 trials on each date. Raw-count coefficient dispersion is recorded and need not decline monotonically at every budget. '
        'The ensemble uses the union of many subsets and is a diagnostic, not a deployable B-label decoder. The ensemble-error term includes noise and model mismatch, not identified physiological bias.',
        '3. **Regularization contributes but is not a universal remedy.** Lower alpha 10 worsens chronological 15 direct MSE on all dates relative to alpha 1000. '
        'Alpha100000 improves Feb 4 but worsens Jan 30/Feb 5; it fails promotion. The nearly flat source-only selection curve does not identify an optimal small-target penalty. '
        'Ridge effective degrees of freedom exclude the intercept; native bins are correlated and are not independent trial replicates.',
        '4. **Scaling/marginal shift is present but mechanism remains inconclusive.** B-fitted direct scaling improves chronological 15 Jan 30/Feb 4 and worsens Feb 5. '
        '45-unlabeled-trial normalization has mixed effects; it changes the information budget. Re-scaling also changes the effective ridge prior, so these comparisons cannot isolate physiological drift.',
        '5. **Stable neuron identity unestablished.** Exact 96-contact joins pass. Fixed column permutation increases frozen MSE on all dates, showing mapping sensitivity. '
        'Condition-matched count-pattern cosines and repetition counts are descriptive, not proof that contacts retain or lose identical neurons. '
        'Task distribution and measurement changes remain confounded.',
        '6. **Offset and label-only controls matter.** JSON separates squared trial-mean residual offsets from centered temporal errors. '
        'Calibration-mean and intercept-only controls explain substantial error changes, but do not universally match neural recalibration. '
        'An intercept correction retains frozen neural predictions and is not mislabeled a label-only method.', '',
        '## Promotion, uncertainty and untouched recordings', '',
        '| Candidate | Mean reduction vs frozen | Mean reduction vs direct 15 | Conditional 95% interval ΔMSE vs frozen | Conditional 95% interval ΔMSE vs direct | Every date better vs both? | Pass? |',
        '|---|---:|---:|---|---|---|---|'])
    for decision in original['promotion']['candidate_decisions']:
        frozen = decision['comparisons']['frozen']
        direct = decision['comparisons']['direct_1']
        every = frozen['every_date_better'] and direct['every_date_better']
        frozen_interval = ', '.join(f'{value:.6f}' for value in frozen['conditional_block_interval'])
        direct_interval = ', '.join(f'{value:.6f}' for value in direct['conditional_block_interval'])
        lines.append(f"| {decision['candidate']} | {100 * frozen['mean_relative_improvement']:.2f}% | {100 * direct['mean_relative_improvement']:.2f}% | [{frozen_interval}] | [{direct_interval}] | {every} | {decision['passed']} |")
    lines.extend(['',
        'The gate requires ≥5% equal-date mean reduction versus **both** controls, strictly lower MSE on every date, and conditional 95% moving-five-trial-block intervals below zero against both. '
        'All seven fail; complete intervals and every failure component remain in JSON. Intervals resample evaluation trials within fixed sessions and calibration choices; '
        'they do not include unseen-animal variability, guarantee temporal independence or correct exploratory diagnostic multiplicity. Subset ranges are not confidence intervals.', '',
        'Metadata-only lineage screening identifies first later compatible CO candidates Feb 24, Feb 25 and Jun 26 in the same pinned DANDI release; '
        'the intervening listed dates are RD and excluded by task. [Exact identities and access evidence](../docs/datasets/m022_eligibility.json) are preserved. '
        'These dates have no repository outcome history found, but external human exposure cannot be guaranteed. **No new native files were acquired or modeled:** '
        'the frozen null rule stops independent mitigation validation. Their native coverage/contact/target eligibility remains unverified, and June introduces a large time gap.', '',
        '## Reproduction and limits', '',
        'Use Conda `cerebro` with Python3.11 and existing declared classical dependencies; download the four exact pinned LINK manifests with the existing dataset downloader. '
        'From repository root, run:', '',
        '```sh',
        'for date in 20200127 20200130 20200204 20200205; do',
        '  conda run -n cerebro python -m cerebro.dataset "configs/link_${date}.json"',
        'done',
        'OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n cerebro python -m cerebro.calibration_mechanisms --output data/processed/m022_calibration_verified',
        'conda run -n cerebro python tools/report_m022.py',
        'conda run -n cerebro python -m pytest',
        '```', '',
        '[Verification record](../docs/research/m022_validation.json) distinguishes executed unit/data checks, full rerun equality and independent review. '
        'Original historical outputs remain unchanged. The primary [PDF](figures/m022_mechanism_comparison.pdf) separates date-level curves from 20-subset variability; '
        'there are no independent-session validation outcomes to plot. No new dependency, model family, physiology, subject-invariance or foundation-model claim is introduced.', '',
        '## Technical abstract', '',
        'We prospectively tested statistical explanations of low-budget LINK decoder adaptation using three previously inspected development dates from one macaque. '
        'A fixed 45/30-trial pool/evaluation partition confined all new fitting and evaluation to historically permitted75-trial calibration partitions. '
        'Ridge, residual correction, shrinkage, allocation and scaling controls at 5/15/30 labels revealed substantial finite-calibration prediction dispersion and condition-coverage sensitivity. '
        'Prediction dispersion fell with larger calibration budgets, while allocation, regularization and scaling effects varied by date. '
        'No prespecified mitigation met the 5% practical threshold and all-date requirements against both frozen-source and direct 15 decoders. '
        'Accordingly, apparently uninspected later CO sessions remained unscored. The findings identify bounded statistical contributors and a negative mitigation decision, '
        'without establishing physiological drift or broad adaptation efficacy.', '',
        '## Five researcher questions', '',
        '1. What estimand should determine success when equal-trial, equal-bin and task-condition weighting disagree?',
        '2. Is access to all commanded conditions plus later calibration trials a fair operational information budget?',
        '3. Which independent measurement could distinguish electrode/neural drift from behavioral-distribution change?',
        '4. What justifies trial-block uncertainty and a 5% practical threshold for the intended use?',
        '5. What new evidence, beyond these inspected dates, would justify changing the failed mitigation protocol?', '',
    ])
    (directory / 'm022_calibration_mechanisms.md').write_text('\n'.join(lines))
    (directory / 'm022_calibration_mechanisms.json').write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', default='data/processed/m022_calibration_verified/results.json')
    parser.add_argument('--output', default='reports')
    arguments = parser.parse_args()
    render(arguments.results, arguments.output)
