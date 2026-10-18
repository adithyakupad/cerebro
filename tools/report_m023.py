"""Render the frozen M023 reliability study; no model fitting or new outcomes."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from cerebro.benchmark import array_digest


def render(path='data/processed/m023_reliability_verified/results.json', output='reports'):
    path = Path(path)
    original = json.loads(path.read_text())
    if original['evaluation']['selected_method'] is not None:
        raise ValueError('The M023 negative-study narrative requires the frozen null decision')
    report = copy.deepcopy(original)
    report['full_results_path'] = str(path)
    report['full_results_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    report['renderer_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for index, row in enumerate(report['rows']):
        resampling = np.asarray(row.pop('within_selected_trial_indices'), dtype=np.int64)
        row['within_budget_bootstrap_index_sha256'] = array_digest(resampling)
        row['within_budget_bootstrap_seed'] = original['config']['random_seed'] + index
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    figures = output / 'figures'
    figures.mkdir(exist_ok=True)
    result = original['evaluation']
    primary = result['budgets']['15']
    models = primary['models']
    figure, axes = plt.subplots(2, 2, figsize=(12, 8))
    dates = ['Jan30', 'Feb4', 'Feb5']
    names = ['constant', 'label_only', 'combined', 'task_plus_dynamics']
    colors = ['#666666', '#009E73', '#0072B2', '#D55E00']
    for name, color in zip(names, colors):
        values = [row['risk_mse_flexion4'] for row in models[name]['per_session']]
        axes[0, 0].plot(range(3), np.asarray(values) * 1e6, 'o-', label=name.replace('_', ' '), color=color)
        budgets = original['config']['budgets']
        sensitivity = [result['budgets'][str(budget)]['models'][name]['risk_mse_flexion4'] for budget in budgets]
        axes[0, 1].plot(budgets, np.asarray(sensitivity) * 1e6, 'o-', label=name.replace('_', ' '), color=color)
    axes[0, 0].set(xticks=range(3), xticklabels=dates, title='Entire-session-held-out risk prediction at15 labels', ylabel='Risk MSE (10⁻⁶ flexion⁴)')
    axes[0, 0].legend(fontsize=8)
    axes[0, 1].set(xticks=budgets, xlabel='Labeled calibration trials', ylabel='Equal-date risk MSE (10⁻⁶ flexion⁴)', title='Budget sensitivity, no budget selection')
    for index, session in enumerate(sorted(set(primary['sessions']))):
        mask = np.asarray(primary['sessions']) == session
        actual = np.asarray(primary['outcomes'])[mask]
        predicted = np.asarray(models['combined']['predicted_differences'])[mask]
        axes[1, 0].scatter(actual, predicted, label=dates[index], alpha=.7)
    actual = np.asarray(primary['outcomes'])
    predicted = np.asarray(models['combined']['predicted_differences'])
    limits = [min(actual.min(), predicted.min()), max(actual.max(), predicted.max())]
    axes[1, 0].plot(limits, limits, '--', color='black', linewidth=1)
    axes[1, 0].axvline(0, color='#999999', linewidth=.7)
    axes[1, 0].axhline(0, color='#999999', linewidth=.7)
    axes[1, 0].set(xlabel='Observed direct − frozen MSE (flexion²)', ylabel='Predicted direct − frozen MSE (flexion²)', title='20 overlapping calibration subsets/date')
    axes[1, 0].legend(fontsize=8)
    controls = ['constant', 'label_only', 'shift']
    for index, control in enumerate(controls):
        comparison = primary['comparisons']['combined'][control]
        interval = np.asarray(comparison['conditional_paired_risk_mse_interval']) * 1e6
        difference = (models['combined']['risk_mse_flexion4'] - models[control]['risk_mse_flexion4']) * 1e6
        axes[1, 1].plot(interval, [index, index], color='#0072B2', linewidth=2)
        axes[1, 1].scatter([difference], [index], color='#0072B2')
    axes[1, 1].axvline(0, color='black', linestyle='--')
    axes[1, 1].set(yticks=range(3), yticklabels=controls, xlabel='Combined − control risk MSE (10⁻⁶ flexion⁴)', title='Conditional95% trial-block intervals')
    figure.suptitle('M023 reliability: no model passes the frozen development gate', fontsize=14)
    figure.text(.5, .012, 'LINK DANDI001201/0.251023.2336, CC-BY-4.0 · one macaque,3 development dates · sourceJan27 · original75-trial pools only · no untouched outcomes', ha='center', fontsize=8)
    figure.tight_layout(rect=(0, .04, 1, .95))
    figure.savefig(figures / 'm023_reliability.pdf', metadata={'CreationDate': None, 'ModDate': None})
    figure.savefig(figures / 'm023_reliability.png', dpi=170)
    plt.close(figure)
    lines = ['# M023 calibration-only adaptation reliability', '',
             '**Result: no reliability model passes the prespecified promotion gate.** This is a development study, not independently validated reliability.', '',
             'Protocol `a2861a2`, pre-execution reliability clarification `ca5a0ad`; see [protocol](../docs/research/m023_protocol.md). '
             'Only the previously permitted first75 trials of Jan30/Feb4/Feb5 are used, with pool45 and evaluation30. '
             'One source date and three development dates belong to one Monkey N. Each budget has20 uniform subsets/date and three entire-session folds. '
             '369 total allocations include chronological/balanced sensitivity cases; overlapping subsets are not biological replicates.', '',
             'Inputs are recomputed from calibration data: selected-command coverage,20 within-B trial-bootstrap prediction dispersion, '
             'neural mean shift, frozen/direct disagreement on45 unlabeled pool trials, calibration-label moments and a source-neural dynamics mismatch. '
             'No evaluation means, evaluation neural probes, post-hoc M022 prediction dispersion or extra position labels enter features. '
             'All scalers/risk regressors fit on the other two dates only. B selected command labels are additional information for coverage features.', '',
             'Leave-one-session-out development folds may train on dates later than the held-out date; this is not rolling chronological deployment validation. '
             'Only the gated later cohort could supply independent forward evaluation, and its outcomes remain unscored.', '',
             '## Primary15-label comparison', '',
             '| Model | Risk MSE (flexion⁴) | Pooled two-class balanced accuracy |',
             '|---|---:|---:|']
    for name, row in models.items():
        accuracy = row['pooled_session_weighted_balanced_accuracy']
        lines.append(f"| {name} | {row['risk_mse_flexion4']:.10g} | {accuracy} |")
    lines.extend(['', f"Majority-class balanced accuracy: {primary['majority_balanced_accuracy']}.",
                  'Balanced accuracy is undefined within single-class folds; only the pooled session-equally weighted two-class metric is used for promotion. '
                  'The combined model improves aggregate risk MSE9.46% versus constant but is51.86% worse than label-only. '
                  'Its balanced accuracy67.5% equals the permuted-combined control and trails label-only76.25%. '
                  'Classification alone therefore provides insufficient evidence of useful neural reliability information.', '',
                  '## Primary contrasts and uncertainty', '',
                  '| Candidate | Control | Aggregate relative risk-MSE improvement | Better every date | Conditional95% risk-MSE difference interval | Pass |',
                  '|---|---|---:|---|---|---|'])
    for name in ('disagreement', 'coverage', 'instability', 'combined'):
        for control, row in primary['comparisons'][name].items():
            interval = ', '.join(f'{value:.7g}' for value in row['conditional_paired_risk_mse_interval'])
            lines.append(f"| {name} | {control} | {100 * row['relative_risk_mse_improvement']:.2f}% | {row['lower_on_every_date']} | [{interval}] | {row['passed']} |")
    lines.extend(['', 'Relative improvement is one minus the ratio of equal-date mean risk errors, not the mean of date-wise percentages. '
                  'Intervals resample shared ordered five-trial blocks across every overlapping allocation within each date, while fitted risk models stay fixed. '
                  'They exclude risk-training uncertainty and population variability; only three development dates from one animal exist. '
                  'Every primary candidate fails. No best-budget or balanced-allocation fallback is promoted.', '',
                  '## Complete budget and action-policy controls', '',
                  '| Budget | Model | Held-out date | Risk MSE flexion⁴ | Harm fraction | Adaptive-policy MSE flexion² | Always frozen | Always direct |',
                  '|---:|---|---|---:|---:|---:|---:|---:|'])
    for budget, evaluation in result['budgets'].items():
        for name, model in evaluation['models'].items():
            for session in model['per_session']:
                lines.append(f"| {budget} | {name} | {session['session']} | {session['risk_mse_flexion4']:.8g} | {session['harm_fraction']:.3f} | {session['policy_mse_flexion2']:.8f} | {session['always_frozen_mse_flexion2']:.8f} | {session['always_direct_mse_flexion2']:.8f} |")
    task = models['task_control']['risk_mse_flexion4']
    extended = models['task_plus_dynamics']['risk_mse_flexion4']
    lines.extend(['', '## Dynamics information beyond task/label controls', '',
                  f'Adding the source-neural forecast mismatch to coverage+label moments changes primary risk MSE from{task:.10g} to{extended:.10g} flexion⁴ '
                  f'({100 * (extended / task - 1):.2f}% worse). This secondary comparison supplies no consistent added predictive benefit. '
                  'Complete per-date errors, chronological/balanced allocation transfer and training-date-only prediction stability remain in the [machine report](m023_reliability.json).', '',
                  '## Independent validation and interpretation', '',
                  '[Native eligibility](../docs/datasets/m023_native_eligibility.md) passes for Feb24/Feb25/Jun26. '
                  '**No new-session model outcomes were scored**, because the frozen development promotion gate failed. '
                  'This is a null-rule decision, not an unavailable-data blocker. New native arrays were audited for coverage and compatibility only. '
                  'The results support a bounded negative finding for these fixed reliability models; they do not establish that all possible reliability diagnostics fail. '
                  'M022 statistical calibration effects do not automatically become prospective harm predictors, and none identifies physiological drift.', '',
                  'Data: Temmar and colleagues, LINK, [DANDI001201 v0.251023.2336](https://doi.org/10.48324/dandi.001201/0.251023.2336), CC-BY-4.0. '
                  'Native20-ms timestamps and count/unit caveats remain unchanged. [Reviewer reproduction guide](../docs/research/m023_reproduction.md) '
                  'and [primary figure](figures/m023_reliability.pdf).', ''])
    text = '\n'.join(lines)
    for before, after in {'first75':'first 75', 'Jan30':'Jan 30', 'Feb4':'Feb 4', 'Feb5':'Feb 5', 'pool45':'pool 45', 'evaluation30':'evaluation 30',
                          'budget has20':'budget has 20', 'coverage,20':'coverage, 20', 'on45':'on 45', 'MSE9.46':'MSE 9.46', 'is51.86':'is 51.86',
                          'accuracy67.5':'accuracy 67.5', 'label-only76.25':'label-only 76.25', 'Primary15':'Primary 15', 'primary15':'primary 15',
                          'Conditional95':'Conditional 95', 'from7':'from 7', 'to7':'to 7', 'Feb24':'Feb 24', 'Feb25':'Feb 25', 'Jun26':'Jun 26', 'Native20':'Native 20'}.items():
        text = text.replace(before, after)
    (output / 'm023_reliability.md').write_text(text)
    (output / 'm023_reliability.json').write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', default='data/processed/m023_reliability_verified/results.json')
    parser.add_argument('--output', default='reports')
    arguments = parser.parse_args()
    render(arguments.results, arguments.output)
