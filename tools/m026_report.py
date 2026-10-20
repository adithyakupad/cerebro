"""Render frozen M026 results without fitting or selecting any model."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from cerebro.optimization_study import digest, read_json


def main():
    report = read_json('reports/m026_neural_information.json')
    if report['evidence_status'] != 'RETROSPECTIVE_SINGLE_SESSION_DIAGNOSTIC':
        raise ValueError('M026 figures require explicitly retrospective evidence')
    if len(report['models']) != 9 or not all(row['restoration_exact'] for row in report['models']):
        raise ValueError('All nine fixed controls must restore exactly before reporting')
    summary = report['summary']
    metrics = summary['metrics']
    order = ['neural_200', 'neural_20', 'clock', 'zero', 'permuted', 'permuted_real',
             'condition_template', 'go_time_template', 'history_ridge', 'kalman', 'mean']
    labels = ['Real CNN200', 'Real CNN20', 'Clock CNN', 'Zero CNN', 'Permuted train+eval',
              'Permuted train/real eval', 'Condition×time', 'Global time', 'History ridge', 'Kalman', 'Mean']
    figure, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)
    values = [metrics[name]['mse_m2_s2'] for name in order]
    positions = np.arange(len(order))
    axes[0].barh(positions, values, color=['tab:blue'] + ['0.65'] * (len(order) - 1))
    for index, name in enumerate(order):
        seeds = metrics[name]['seed_mse_m2_s2']
        axes[0].scatter(seeds, np.full(len(seeds), index), s=14, color='black', zorder=3)
    axes[0].set(yticks=positions, yticklabels=labels, xlabel='Equal-trial MSE [(m/s)²]', title='Fixed controls; points = optimization seeds')
    axes[0].invert_yaxis()
    references = ['clock', 'permuted', 'condition_template', 'go_time_template', 'history_ridge', 'kalman']
    for index, name in enumerate(references):
        row = summary['contrasts'][name]
        difference = row['difference_m2_s2']
        lower, upper = row['paired_interval_95']
        error = np.asarray([[difference - lower], [upper - difference]])
        axes[1].errorbar(difference, index, xerr=error, fmt='o', capsize=4)
    axes[1].axvline(0, color='black', linewidth=1)
    axes[1].set(yticks=np.arange(len(references)), yticklabels=references,
                xlabel='Real CNN200 − control MSE [(m/s)²]', title='Paired 95% trial intervals; fixed fitted models')
    axes[1].invert_yaxis()
    figure.suptitle('M026 RETROSPECTIVE | Jenkins Sep25 2009 | DANDI 000128 v0.220113.0400\n574 trials, one subject/session | go −400:+1000 ms; 20 ms bins; score bins 5–70')
    figure_path = Path('reports/figures/m026_neural_information.pdf')
    figure.savefig(figure_path, metadata={'CreationDate': None, 'ModDate': None})
    figure.savefig(figure_path.with_suffix('.png'), dpi=160)
    plt.close(figure)
    sensitivity, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    for name in ('neural_200', 'clock', 'permuted', 'condition_template'):
        for axis, dimension in zip(axes, ('speed_m_s', 'direction')):
            groups = summary['stratification'][name][dimension]
            strata_labels = list(groups)
            stratum_values = [groups[label]['equal_trial_mse'] for label in strata_labels]
            plotted = [np.nan if value is None else value for value in stratum_values]
            axis.plot(np.arange(len(groups)), plotted, marker='o', label=name)
            axis.set(xticks=np.arange(len(groups)), xticklabels=strata_labels, ylabel='Within-stratum equal-trial MSE [(m/s)²]', title=dimension)
            axis.tick_params(axis='x', labelrotation=25)
            axis.legend(fontsize=8)
    sensitivity.suptitle('M026 descriptive target strata | no model selection | one session, fixed target-defined bins')
    sensitivity.savefig('reports/figures/m026_error_strata.pdf', metadata={'CreationDate': None, 'ModDate': None})
    plt.close(sensitivity)
    learning, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    for axis, mode in zip(axes, ('zero', 'clock', 'permuted')):
        for row in report['models']:
            if row['mode'] == mode:
                epochs = [entry['epoch'] for entry in row['history']]
                errors = [entry['inner_physical_mse'] for entry in row['history']]
                axis.plot(epochs, errors, label='seed ' + str(row['seed']))
        axis.set(title=mode, xlabel='Full-batch optimizer updates', ylabel='Inner physical MSE [(m/s)²]')
        axis.legend()
    learning.suptitle('M026 training-only epoch selection | identical fixed cap200, architecture and optimizer')
    learning.savefig('reports/figures/m026_training_curves.pdf', metadata={'CreationDate': None, 'ModDate': None})
    plt.close(learning)
    lines = ['# M026: neural information and decoder validity', '',
             '**Retrospective diagnostic analysis.** The standard validation outcomes were already inspected in M025. These comparisons are not a second independent confirmation.', '',
             '## Question and design', '',
             'We tested whether the M025 CNN gain can be explained by task-phase predictability or persists against trained controls that disrupt trial-specific neural–behavior pairing. No CNN architecture, historical output, trial partition, loss or optimizer was changed.', '',
             'The frozen [protocol](../docs/research/m026_protocol.md) ranks alternatives before training. The [control validity matrix](../docs/research/m026_control_validity.md) documents removed/preserved information, task clocks, distribution shifts and limitations. All control seeds 0/1/2 receive at most 200 updates; epoch selection uses only 1377/344 inner fitting/validation trials, then refits 1721 original training trials. Both coordinates and all 70 bins enter training loss; common primary scoring uses 574 trials × 66 bins × 2 coordinates, equal-trial physical MSE. These are separately fitted models of one animal and one recording.', '',
             '## Measurements', '', '| Model / information | MSE [(m/s)²] | Seed-specific MSE |', '| --- | ---: | --- |']
    for name, label in zip(order, labels):
        row = metrics[name]
        lines.append(f"| {label} | {row['mse_m2_s2']:.10f} | {row['seed_mse_m2_s2']} |")
    lines.extend(['', '| Real CNN200 minus control | Absolute MSE difference [(m/s)²] | Relative reduction | Paired95% interval | Ordered-block 5 interval |', '| --- | ---: | ---: | --- | --- |'])
    for name, row in summary['contrasts'].items():
        lines.append(f"| {name} | {row['difference_m2_s2']:.10f} | {100 * row['relative_reduction']:.3f}% | {row['paired_interval_95']} | {row['ordered_block5']['paired_interval_95']} |")
    lines.extend(['', 'Both frozen primary descriptive thresholds (5% and negative paired interval): **' + str(summary['primary_descriptive_support']) + '**. These thresholds do not restore untouched-test status.', '',
                  'Condition-template fallback: ' + str(report['condition_template_fallback_trials']) + '/574 trials. Unseen conditions use the global training-bin template. Condition, speed and direction tables in JSON include participating trial/bin counts and per-trial errors, averaged over seed losses rather than ensemble predictions. Speed strata are [0,.1,.25,.5,infinity] m/s; direction uses four Cartesian quadrants and stationary samples separately. Strata are descriptive, with no outcome-driven thresholds or per-bin biological inference.', '',
                  '## Training and information budgets', '',
                  '| Control, seed | Selected epoch | Inner selected MSE [(m/s)²] | Refit seconds | Batch forward seconds |', '| --- | ---: | ---: | ---: | ---: |'])
    for row in report['models']:
        selected_loss = row['history'][row['selected_epoch'] - 1]['inner_physical_mse']
        lines.append(f"| {row['name']} | {row['selected_epoch']} | {selected_loss:.10f} | {row['fit_seconds']:.4f} | {row['evaluation_forward_seconds']:.4f} |")
    permutation = next(row for row in report['models'] if row['mode'] == 'permuted')
    lines.extend(['', 'Fixed donor-map unchanged counts by partition: ' + str({name: row['unchanged'] for name, row in permutation['mapping'].items()}) + '. Every nonsingleton is deranged; singleton pairs retain original information. One fixed surrogate per partition is shared across optimization seeds; seeds do not sample independent permutations.', '',
                  'All newly trained CNN controls have the same nominal parameter count (' + str(report['models'][0]['parameters']) + '); effective input rank and usable functional capacity differ. Repeated explicit-clock channels intentionally provide task timing, not neural observations. Zero CNN becomes constant after its four-bin padding transient and is not a strong task-phase predictor. The unrestricted training-bin template and condition×time template supplement the optimized clock model. The latter receives task-condition metadata that the original CNN does not receive explicitly.', '',
                  'The permuted-training model is evaluated on both partition-local permuted inputs and original inputs. The matched permuted-input comparison disrupts residual pairing during training AND inference while preserving complete donor trajectories and condition/time structure. Original-input inference is separately reported; no favorable variant was selected. Fixed-map finite-sample surrogate error and singleton retention prevent interpreting this as perfect conditional independence.', '',
                  'Total fit/stage seconds: ' + str(report['seconds_total']) + '; unchanged native preparation seconds: ' + str(report['lineage']['seconds']) + '. Batch-forward timings describe offline CPU execution, not prospective streaming latency. All per-epoch histories are in JSON.', '',
                  '## Four interpretation questions', '',
                  '1. **Historical accuracy:** M025 real CNN200 remains 0.0127916679 versus CNN200-cap20 reference 0.0266053581, Kalman 0.0302108898 and history ridge 0.0220675991 (m/s)². M026 does not modify or independently reconfirm those comparisons.',
                  '2. **Neural beyond phase:** compare real CNN200 with explicit clock and global time template. An advantage is relative to these specified task estimators, not proof that all possible task predictors have been exhausted.',
                  '3. **Training advantage and task conditions:** compare real CNN with matched condition-permuted training/evaluation, the same permuted-trained model on real inputs, and condition×time template. These are controls for predictive information, not physiological necessity or causal neural effects. Convergent advantages support trial-specific neural–behavior association beyond these task summaries. Information budgets and finite optimization differ in effective capacity despite equal nominal architecture.',
                  '4. **Generalization:** none of these retrospective same-session controls demonstrates outside-task/recording prediction, cross-subject invariance, decoder transfer or online BCI. No future-behavior forecast is evaluated.', '',
                  '## Integrity, uncertainty and limitations', '',
                  'All comparisons retain exact M025 evaluation targets/IDs and complete-coverage bins. Data are genuine intracortical spikes and supplied hand velocity in physical m/s; no synthetic observation replaces an empirical claim. Source is DANDI 000128 v0.220113.0400, asset 26e85f09-39b7-480f-b337-278a8f034007, SHA256 a27f84f9c31f077011062fd99a6ced199fdf19e656151f056c3c6244a408a3c4. [Churchland and Kaufman (2022), CC-BY-4.0](https://doi.org/10.48324/dandi.000128/0.220113.0400). Raw recordings and checkpoints are not redistributed.',
                  'Paired 10,000-draw intervals resample whole trials with seed 26; block 5 is a temporal-dependence sensitivity. Uncertainty conditions on fixed fits in one session. It excludes independent-session/subject variation and repeated surrogate-generation variability. Optimization seeds are not biological replicates; no multiplicity-adjusted confirmatory p-value is claimed.',
                  'The CNN has a five-bin causal receptive field but reconstructs contemporaneous velocity at bin right. Offline pre-cue windows depend on a later recorded go cue. Task selection and native upstream velocity estimation remain potential structure; causal neural input does not imply prospective task initialization or a physiologically causal target. Ridge training masks differ from CNN/Kalman, although evaluation masks agree; see original audit.',
                  'Only cap200 input controls were trained. A full cap×input factorial was not run; these contrasts cannot quantitatively apportion the 20→200 improvement into additive neural, task and optimization components. Task-condition clusters and alternative donor maps are not resampled by the conditional trial intervals.',
                  'Partial feature replacement from M025 is a distribution-shift sensitivity, not a no-neural baseline. A permuted neural population still contains abundant condition/time information and donor dynamics. Task templates are particular estimators, not all-task-information ceilings. No positive control result establishes a physiological mechanism, general subject invariance, adaptive decoder superiority or foundation-model validity.', '',
                  '## Reproduction and review', '',
                  'Use the existing Conda cerebro Python 3.11 environment and declared dev,classical,deep extras. Parent M025 artifacts are local inputs, with exact original hashes authenticated; regenerate M025 from its public guide in a separate clone if absent. The corrected M025 numerical verification/recovery remains unchanged.', '',
                  '```sh', 'conda run -n cerebro python tools/m026_prepare.py', 'conda run -n cerebro python -m cerebro.neural_information', 'conda run -n cerebro python -m cerebro.neural_information --replay', 'conda run -n cerebro python tools/m026_report.py', 'conda run -n cerebro python -m pytest -q', '```', '',
                  'Preparation refuses to overwrite its cache; fitting uses an exclusive start marker and refuses an implicit rerun. Execute fresh reproduction in a separate clone and archive canonical reports. Reproduction of published outcomes is not a new independent test. Replay restores every new checkpoint, verifies array digests and original M025 file hashes without fitting. Independent review and executed validation are recorded separately in m026_validation.json / m026_independent_review.md.', '',
                  '## Application evidence', '',
                  'A. Demonstrated earlier: frozen CNN optimization-and-selection recipe reduced MSE 51.92% versus 20 updates and 57.66% versus tuned Kalman in a separately fitted recording of the same animal.',
                  'B. Incremental neural evidence: report the fixed real-versus-control contrasts above explicitly as retrospective; promotion thresholds do not establish new independent confirmation.',
                  'C. Unresolved: broader task representations, finite surrogate/optimization uncertainty, one-session diagnostics, repeated condition structure and native target estimation.',
                  'D. Unsupported: physiological causation, future forecasting, clinical/online BCI, subject-invariant representations, general-purpose foundation models or independent human authorship of agent-assisted code.',
                  'Conservative resume bullet: “Built and audited reproducible neural-velocity decoding experiments on public intracortical recordings; demonstrated a prespecified CNN optimization gain and evaluated trained task-clock and condition-matched neural-pairing controls, preserving trial-aware uncertainty and negative findings.” Narrow neural-information numbers may be added only with their retrospective qualification after researcher review.'])
    text = '\n'.join(lines) + '\n'
    text = text.replace('CNN200-cap20 reference', 'CNN20 reference')
    Path('reports/m026_neural_information.md').write_text(text)
    manifest = {'results_sha256': digest('reports/m026_neural_information.json'), 'report_sha256': digest('reports/m026_neural_information.md'),
                'primary_figure_sha256': digest(figure_path), 'generator_sha256': digest(__file__)}
    Path('reports/m026_artifacts.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
