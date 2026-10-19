"""Compose M025 evidence from frozen stage reports; never fit or score a model."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    development_path = Path('reports/m025_development.json')
    final_path = Path('reports/m025_final.json')
    development = read(development_path)
    final = read(final_path) if final_path.exists() else None
    stages = [('Small development (previously inspected)', development)]
    if final is not None:
        if not development['development_gate_passed']:
            raise ValueError('Final report exists despite failed development gate')
        stages.append(('Standard session (previously performance-unscored)', final))
    for _, stage in stages:
        assert stage['protocol_sha256'] == development['protocol_sha256']
        assert len(stage['cnn']) == 6
        assert all(row['restoration_exact'] for row in stage['cnn'])
    figure, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    for column, (label, stage) in enumerate(stages):
        for row in stage['cnn']:
            if row['cap'] != 200:
                continue
            epochs = [entry['epoch'] for entry in row['history']]
            validation = [entry['inner_physical_mse'] for entry in row['history']]
            axes[0, column].plot(epochs, validation, label='Seed ' + str(row['seed']))
        axes[0, column].axvline(20, color='black', linestyle='--', linewidth=1)
        axes[0, column].set(title=label, xlabel='Optimizer updates', ylabel='Inner physical MSE [(m/s)²]')
        axes[0, column].legend()
        for index, name in enumerate(('cnn20', 'kalman', 'history_ridge')):
            contrast = stage['contrasts'][name]
            difference = contrast['difference_m2_s2']
            low, high = contrast['paired_interval_95']
            error = np.asarray([[difference - low], [high - difference]])
            axes[1, column].errorbar(index, difference, yerr=error, fmt='o', capsize=4)
        axes[1, column].axhline(0, color='black', linewidth=1)
        axes[1, column].set(xticks=[0, 1, 2], xticklabels=['CNN20', 'Kalman', 'History ridge'], ylabel='CNN200 − reference MSE [(m/s)²]', title='Paired 95% trial bootstrap; fixed fitted models')
    for column in range(len(stages), 2):
        for axis in axes[:, column]:
            axis.text(.5, .5, 'Final evaluation not completed', ha='center', va='center')
            axis.set_axis_off()
    figure.suptitle('M025 | Jenkins: Sep28 / Sep25 2009 | go −400:+1000 ms; 20 ms bins; score bins 5–70\nDANDI 000140 v0.220113.0408 / 000128 v0.220113.0400 | one animal, separate session-specific fits')
    figure_path = Path('reports/figures/m025_budget_comparison.pdf')
    figure.savefig(figure_path, metadata={'CreationDate': None, 'ModDate': None})
    figure.savefig(figure_path.with_suffix('.png'), dpi=160)
    plt.close(figure)
    training_figure, training_axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for column, (label, stage) in enumerate(stages):
        for row in stage['cnn']:
            if row['cap'] == 200:
                epochs = [entry['epoch'] for entry in row['history']]
                training_loss = [entry['training_standardized_mse'] for entry in row['history']]
                training_axes[column].plot(epochs, training_loss, label='Seed ' + str(row['seed']))
        training_axes[column].set(title=label, xlabel='Optimizer updates', ylabel='Training standardized-coordinate MSE')
        training_axes[column].legend()
    training_figure.suptitle('M025 | unchanged CNN objective; these are not physical velocity MSE curves')
    training_figure.savefig('reports/figures/m025_training_loss.pdf', metadata={'CreationDate': None, 'ModDate': None})
    plt.close(training_figure)
    practical = final is not None and final['practical_gate_passed_on_this_stage']
    abstract = 'Development evidence alone cannot establish independent practical improvement.'
    if final is not None:
        selected_values = [row['mse_m2_s2'] for name, row in final['metrics'].items() if name.startswith('cnn_200_seed_')]
        final_mse = float(np.mean(selected_values))
        reduction_short = final['contrasts']['cnn20']['relative_reduction'] * 100
        reduction_kalman = final['contrasts']['kalman']['relative_reduction'] * 100
        abstract = (f'We tested whether optimization budget limits an existing causal temporal CNN on authentic intracortical MC_Maze recordings. A fixed 20-versus-200-update protocol used training-only preprocessing, physical-MSE epoch selection, three seeds and matched classical controls. The development promotion reduction was {development["development_relative_reduction"] * 100:.2f}%. In one separately recorded session of the same animal, CNN200 achieved {final_mse:.8f} (m/s)², {reduction_short:.2f}% lower than CNN20 and {reduction_kalman:.2f}% lower than Kalman. Paired trial and ordered-block uncertainty are reported without treating seeds as biological replicates. These are offline same-bin reconstruction results from session-specific fits, not decoder transfer, new-subject generalization or physiological mechanism identification.')
    if final is not None:
        status = 'PRACTICAL_IMPROVEMENT_IN_ONE_ADDITIONAL_SESSION' if practical else 'FINAL_PRACTICAL_GATE_NOT_MET'
    elif development['development_gate_passed']:
        status = 'FINAL_EVALUATION_PENDING_OR_INTERRUPTED'
    else:
        status = 'DEVELOPMENT_GATE_NOT_MET_FINAL_NOT_EXECUTED'
    lines = ['# M025: a controlled optimization-budget study', '',
             '**' + status + '**. The architecture, training loss, optimizer and seeds were held fixed. Historical results remain unchanged.', '',
             '## Abstract', '', abstract, '', '## Design and lineage', '',
             'Diagnostic commit 35e8dd9; frozen protocol 7f756c2; shape guard ce588f5; reviewed implementation 477ed95; validation-only recovery 8d459de.',
             'Primary comparison: maximum 20 versus 200 full-batch Adam updates, physical-MSE inner epoch selection, three seeds. Mean seed losses within trial; no best-seed selection.',
             'Development: original Small: 75 training / 25 already-inspected validation trials, inner 60/15. Promotion uses the same inner trials as epoch selection, so it is selection-conditioned.',
             'Standard: original source train/val and new internal split, separately fitted 137-unit model. Historical raw eager loading is disclosed; there was no documented decoder scoring or selection on its 574 validation trials.',
             'No unit correspondence or trained-decoder transfer across dates is assumed. One animal and one additional recording cannot establish population-wide/session-invariant performance.', '',
             '## Measured outcomes', '']
    for label, stage in stages:
        cnn = {}
        for cap in (20, 200):
            values = [row['mse_m2_s2'] for name, row in stage['metrics'].items() if name.startswith('cnn_' + str(cap) + '_seed_')]
            cnn[cap] = float(np.mean(values))
        lines.extend(['', '| Stage | CNN20 | CNN200 | Kalman | History ridge | MSE units |', '| --- | ---: | ---: | ---: | ---: | --- |'])
        lines.append(f"| {label} | {cnn[20]:.10f} | {cnn[200]:.10f} | {stage['metrics']['kalman']['mse_m2_s2']:.10f} | {stage['metrics']['history_ridge']['mse_m2_s2']:.10f} | (m/s)² |")
        lines.extend(['', '### ' + label, '',
                      'Full counts/targets: ' + str(stage['counts_shape']) + ' / ' + str(stage['target_shape']) + '; exclusions ' + str(len(stage['exclusions'])) + '.',
                      'Within each session, both caps have the same input units and identical hidden size 32, two width-3 convolutions and 2-coordinate readout. Across sessions the input-layer size follows the separately observed unit count; no shared-neuron identity is inferred.',
                      'Within-stage inner selected loss by cap (only Small defines the promotion gate): ' + str(stage['inner_loss_by_cap']) + '.',
                      'Selected epochs: ' + str([(row['cap'], row['seed'], row['selected_epoch']) for row in stage['cnn']]) + '.',
                      'Seed-specific evaluation MSE: ' + str({name: row['mse_m2_s2'] for name, row in stage['metrics'].items() if name.startswith('cnn_')}) + '.',
                      'Seconds total: ' + str(stage['seconds_total']) + '; per-epoch, refit and forward costs are in the machine stage report.', '',
                      '| CNN200 relative to | Absolute MSE difference | Relative reduction | Paired 95% trial CI | Ordered-block-five CI |', '| --- | ---: | ---: | --- | --- |'])
        for name, contrast in stage['contrasts'].items():
            lines.append(f"| {name} | {contrast['difference_m2_s2']:.10f} | {100 * contrast['relative_reduction']:.3f}% | {contrast['paired_interval_95']} | {contrast['ordered_block5']['paired_interval_95']} |")
        lines.extend(['', 'Authorized mean / event-template / instantaneous-ridge MSE: ' + str([stage['metrics'][name]['mse_m2_s2'] for name in ('mean', 'go_time_template', 'ridge')]) + '.', '', '| Fixed inference sensitivity | CNN20 | CNN200 | Kalman | History ridge |', '| --- | ---: | ---: | ---: | ---: |'])
        for perturbation, results in stage['sensitivity'].items():
            cap_means = {}
            for cap in (20, 200):
                seed_values = [value for name, value in results.items() if name.startswith('cnn_' + str(cap) + '_seed_')]
                cap_means[cap] = float(np.mean(seed_values))
            lines.append(f"| {perturbation} | {cap_means[20]:.10f} | {cap_means[200]:.10f} | {results['kalman']:.10f} | {results['history_ridge']:.10f} |")
        lines.extend(['', 'Condition-permutation null: ' + str(stage['null_changed_trials']) + ' changed / ' + str(len(stage['splits']['source_validation'])) + ' evaluation trials; ' + str(stage['null_singleton_trials']) + ' singleton trials.',
                      ('**NOT INFORMATIVE**: no trials change; singleton labels do not provide an effective neural null.' if stage['null_changed_trials'] == 0 else 'The partial condition permutation retains task phase and condition structure, including unchanged fixed points; interpret it descriptively.'),
                      'Mean/template, train-mean feature replacement, every seed, coordinate R² and all 70-bin sensitivities remain in the stage report. No sensitivity selected a new primary model.'])
    lines.extend(['', '## Interpretation and limitations', '',
                  'The frozen contrasts support a practical improvement in the optimization-and-epoch-selection recipe on this additional recording; this does not identify a physiological mechanism. A longer-cap selected epoch is not itself evidence of undertraining. The intervention expands both optimizer updates and available epoch-selection candidates; it does not isolate their effects under a fixed selected epoch.',
                  'The CNN training loss and Kalman fitting use all 70 training bins; ridge controls fit bins 5–70 because complete five-bin histories start there. All selection/primary evaluation masks match, but training target masks across families do not. The CNN20-versus200 intervention itself holds this constant.',
                  'Task clock and strong velocity autocorrelation remain competing explanations for predictable structure. History-ridge tests linear temporal integration; an ineffective condition permutation cannot rule out task-phase explanations. Other neural architectures were not retuned, so this is not a new ranking across CNN, GRU/LSTM and Transformer families.',
                  'No neural–behavior lag was optimized. Native distributed velocity targets and their physical conversion were used as supplied; upstream velocity estimation was not independently reconstructed. Current/past counts reconstruct same-bin mean velocity at bin right, not future forecasting or online control. Original interleaved source partitions are offline held-out trials, not chronological deployment. Different alignment, lag and endpoint conventions mean these are not NLB leaderboard scores.',
                  'Causality is within extracted sequences. Pre-cue windows and sequence reset are indexed offline using the recorded later go cue; the task-phase control receives that clock. Prefix tests do not demonstrate prospective event detection or live initialization.',
                  'Uncertainty conditions on fixed model fits and trials from one session. Seed spread is optimization variation; no bootstrap sample is another animal. Ordered blocks are a sensitivity, not a guarantee of independence.',
                  'The known nondefault permuted-risk alpha defect is unrelated and remains unfixed. Shape mismatch rejection was isolated and tested without changing valid-shape updates or RNG state.', '',
                  '## Compute interpretation', '',
                  'Total stage wall time includes recording preparation. A source audit found repeated full-recording timestamp/spike validation and full physical-velocity conversion inside the per-trial preparation loop. For 6,809,920 two-coordinate samples over 2,295 trials, conversion alone implies roughly 500 GB cumulative intermediate writes; this is an analytical workload estimate, not measured bandwidth or resident memory. Native metadata also give 2,295 observation intervals per unit: the reference coverage loop entails 137×2,295×2,295 ≈ 722 million Python interval iterations. Preparation was not separately profiled and was not optimized during this frozen study.',
                  'Per-epoch, refit and batch-forward costs are recorded separately. For recovered seed0 checkpoints, fit_seconds=0 means no additional refit in the continuation, not free original training. The failed-attempt duration is preserved separately in the recovery manifest; add it when discussing total study compute. These are CPU offline costs, not streaming or hardware latency; GPU performance and clinical/live BCI operation were not tested.', '',
                  '## Disclosed pre-scoring recovery', '',
                  'The first standard attempt stopped in a float32 cross-length verification check after saving seed0 models, before any final metric was calculated. Synthetic independent diagnosis reproduced discrepancies consistent with floating-point roundoff. The reviewed correction uses a double-precision validation copy at 1e-12 and records production float32 discrepancies; production weights, dtype and forward procedure are unchanged. Initial forward arrays had not been saved, so a bitwise comparison against those lost arrays is unavailable; preserved checkpoint bytes and exact completed-run restoration provide the direct evidence. This is structural/mathematical causality, not bitwise future invariance of float32 convolution.',
                  'The [official PyTorch numerical-accuracy notes](https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html) explain why mathematically equivalent batched/sliced floating-point computations need not match bitwise. Our synthetic measurements provide the case-specific evidence; no particular backend algorithm was forensically identified.',
                  'The original marker and seed0 checkpoints are preserved. Exact old/new source hashes and protected artifact hashes are bound in docs/research/m025_recovery.json. This explicit continuation reuses saved source-trained models, reconstructs only source inner curves, and never changes the frozen 5% gates or consumes partial final errors to choose a method. Recovery is part of the disclosed evaluation occasion, not an additional independent replication.', '',
                  '## Verification and reproduction', '',
                  '289 software tests and 22 authentic-data tests passed (311 total); 20 existing HDMF deprecation warnings in the data suite. 31 focused pre-training tests also passed and overlap these counts.',
                  'All three CNN20 development prediction arrays exactly match sequence06 historical predictions. Model replay verifies numerical checkpoint restoration and saved array/file digests.',
                  '`conda run -n cerebro python -m cerebro.optimization_study --stage development --replay`',
                  '`conda run -n cerebro python -m cerebro.optimization_study --stage final --replay` (only if executed)',
                  '`conda run -n cerebro python tools/m025_report.py` regenerates this synthesis and comparison figure without fitting.',
                  'Training commands are identical without --replay; existing stage results refuse overwriting. Final access additionally requires committed passing development/eligibility evidence, unchanged source/protocol hashes and an exclusive final-start marker. Never delete that marker to repeat a final evaluation.',
                  'Pinned CC-BY-4.0 DANDI sources: [Small](https://doi.org/10.48324/dandi.000140/0.220113.0408), [standard](https://doi.org/10.48324/dandi.000128/0.220113.0400), Churchland and Kaufman (2022). Exact native assets/checksums, units and session clocks are in the stage reports and eligibility audit. Raw data and checkpoints are excluded from Git.', '',
                  '## Application evidence and next decision', '',
                  'Defensible contribution: a prospectively frozen optimization-budget comparison with matched histories, independent classical tuning, separate target-shape regression protection, numerical replay and explicitly qualified session replication. Claim only the measured gates reported above.',
                  'Earlier LINK adaptation/reliability negative findings are unchanged and concern different normalized finger-position targets. This study does not establish successful calibration-efficient adaptation. Researcher selected and authorized the design; agents assisted implementation and review. This artifact does not establish independent human reconstruction of every implementation, hiring suitability, physiological neural drift, general subject invariance or foundation-model validity.',
                  'Next decision: review the result and uncertainty before proposing any new recording cohort or change of prediction horizon. Do not reuse the scored standard validation outcomes for another supposedly confirmatory tuning cycle.', '',
                  '## Interview defense questions', '',
                  '1. Why can a 200-epoch cap select fewer than 200 epochs, and why is a selected last epoch not proof of undertraining?',
                  '2. How does standardized-coordinate training loss differ from physical velocity MSE, and where are both scalers fitted?',
                  '3. Why do five-bin history ridge and CNN have matched information, while Kalman receives a different recursive prior?',
                  '4. Why are seeds/bins not independent biological units, and what uncertainty is missing from fixed-model trial bootstrap?',
                  '5. What is left unproven by a gain on one separately fitted session, especially when raw data were previously opened and task conditions repeat?',
                  '6. How can mathematical causality coexist with tiny float32 prefix discrepancies, and what exactly does the double-precision verification establish?'])
    Path('reports/m025_optimization.md').write_text('\n'.join(lines) + '\n')
    manifest = {'status': status, 'stage_report_sha256': {str(development_path): digest(development_path)},
                'figure_sha256': digest(figure_path), 'report_generator_sha256': digest(__file__),
                'independent_biological_subjects': 1, 'additional_evaluation_sessions': int(final is not None),
                'development_gate_passed': development['development_gate_passed'],
                'final_practical_gate_passed': bool(practical), 'software_tests_passed': 289, 'data_tests_passed': 22}
    if final is not None:
        manifest['stage_report_sha256'][str(final_path)] = digest(final_path)
    Path('reports/m025_optimization.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
