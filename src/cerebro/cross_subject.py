"""Lossy anonymous population-moment transfer between public FALCON subjects."""

import argparse
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import shlex

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from cerebro.benchmark import array_digest, save_immutable
from cerebro.evaluation import loss_summary
from cerebro.falcon import load_falcon


FEATURE_NAMES = ['mean_count', 'count_std', 'zero_fraction', 'q25_count',
                 'median_count', 'q75_count', 'maximum_count']


def anonymous_features(counts):
    """Return bins × seven permutation-invariant, deliberately lossy moments."""
    counts = np.asarray(counts, dtype=float)
    if counts.ndim != 2 or counts.shape[1] < 1:
        raise ValueError('Counts require observation bins × anonymous neural units')
    if not np.all(np.isfinite(counts)) or np.any(counts < 0) or np.any(counts != np.floor(counts)):
        raise ValueError('Anonymous features require valid nonnegative integer counts')
    mean_count = counts.mean(axis=1)
    count_std = counts.std(axis=1)
    zero_fraction = np.mean(counts == 0, axis=1)
    count_quantiles = np.quantile(counts, [.25, .5, .75], axis=1)
    maximum_count = counts.max(axis=1)
    features = np.column_stack([
        mean_count, count_std, zero_fraction, count_quantiles[0],
        count_quantiles[1], count_quantiles[2], maximum_count,
    ])
    return features


def prepare_trials(recording):
    """Mask source-native samples, retaining exact identities and bin clocks."""
    retained = []
    exclusions = []
    previous_stop = -np.inf
    seen_ids = set()
    for source_row, trial in enumerate(recording['trials']):
        identity = int(trial['trial_id'])
        if identity in seen_ids:
            raise ValueError('Trial identities must be unique within each subject')
        seen_ids.add(identity)
        left = np.asarray(trial['timestamps'])
        right = np.asarray(trial['bin_right_seconds'])
        counts = np.asarray(trial['counts'])
        targets = np.asarray(trial['targets'])
        neural_valid = np.asarray(trial['neural_valid'])
        target_valid = np.asarray(trial['target_valid'])
        keep_mask = np.asarray(trial['source_eval_mask'])
        if counts.ndim != 2 or targets.shape != (len(left), len(recording['muscle_names'])):
            raise ValueError('Native count and EMG dimensions do not match trial timestamps')
        if counts.shape[0] != len(left) or right.shape != left.shape:
            raise ValueError('Native neural and behavioral sample axes differ')
        if neural_valid.shape != counts.shape or neural_valid.dtype != np.bool_:
            raise ValueError('Native neural coverage mask must match every neural unit')
        if target_valid.shape != left.shape or keep_mask.shape != left.shape:
            raise ValueError('Target and source evaluation masks must match sample axes')
        if target_valid.dtype != np.bool_ or keep_mask.dtype != np.bool_:
            raise ValueError('Native sample masks must be Boolean')
        if len(left):
            valid_clock = np.isfinite(left).all() and np.isfinite(right).all()
            increasing = np.all(np.diff(left) > 0)
            correct_width = np.allclose(right - left, .020, rtol=0, atol=1e-9)
            if not valid_clock or not increasing or not correct_width or left[0] < previous_stop - 1e-10:
                raise ValueError('Native half-open bins must preserve chronological trial boundaries')
            previous_stop = right[-1]
        complete_neural = neural_valid.all(axis=1)
        finite_targets = np.isfinite(targets).all(axis=1)
        selected_rows = keep_mask & complete_neural & target_valid & finite_targets
        sample_indices = np.flatnonzero(selected_rows)
        audit = {
            'trial_id': identity, 'original_trial_row': source_row,
            'native_samples': len(left), 'eligible_samples': len(sample_indices),
            'source_mask_false': int(np.sum(~keep_mask)),
            'neural_coverage_incomplete': int(np.sum(~complete_neural)),
            'target_missing': int(np.sum(~target_valid | ~finite_targets)),
            'excluded_samples_union': int(np.sum(~selected_rows)),
        }
        if len(sample_indices) == 0:
            audit['whole_trial_excluded'] = True
            exclusions.append(audit)
            continue
        selected_counts = counts[selected_rows]
        features = anonymous_features(selected_counts)
        retained.append({
            'trial_id': identity, 'original_trial_row': source_row,
            'features': features, 'targets': targets[selected_rows],
            'left_seconds': left[selected_rows], 'right_seconds': right[selected_rows],
            'native_sample_indices': sample_indices,
            'audit': audit,
        })
    if not retained:
        raise ValueError('No fully covered, source-mask-eligible trial samples remain')
    return retained, exclusions


def flatten(trials, field):
    return np.concatenate([trial[field] for trial in trials], axis=0)


def trial_losses(trials, prediction):
    lengths = np.asarray([len(trial['targets']) for trial in trials])
    if prediction.shape != (int(lengths.sum()), trials[0]['targets'].shape[1]):
        raise ValueError('Prediction dimensions must preserve source trial sample lengths')
    if not np.all(np.isfinite(prediction)):
        raise ValueError('Predictions must be finite')
    offsets = np.concatenate([[0], np.cumsum(lengths)])
    losses = []
    for row, trial in enumerate(trials):
        trial_prediction = prediction[offsets[row]:offsets[row + 1]]
        differences = trial_prediction - trial['targets']
        losses.append(float(np.mean(differences ** 2)))
    return np.asarray(losses)


def _checkpoint_prediction(path, model, scaler, observations, base=None):
    parameters = {
        'coefficients': model.coef_, 'intercept': model.intercept_,
        'feature_mean': scaler.mean_, 'feature_scale': scaler.scale_,
    }
    if base is not None:
        parameters['base_coefficients'] = base.coef_
        parameters['base_intercept'] = base.intercept_
    np.savez_compressed(path, **parameters)
    transformed = scaler.transform(observations)
    prediction = model.predict(transformed)
    if base is not None:
        prediction = prediction + base.predict(transformed)
    with np.load(path, allow_pickle=False) as archive:
        normalized = (observations - archive['feature_mean']) / archive['feature_scale']
        restored = normalized @ archive['coefficients'].T + archive['intercept']
        if base is not None:
            base_prediction = normalized @ archive['base_coefficients'].T + archive['base_intercept']
            restored = restored + base_prediction
    if not np.array_equal(restored, prediction):
        raise ValueError('Saved decoder parameters changed predictions')
    return prediction


def run(config_path, output):
    config = json.loads(Path(config_path).read_text())
    source_manifest = json.loads(Path(config['source_manifest']).read_text())
    target_manifest = json.loads(Path(config['target_manifest']).read_text())
    source = load_falcon(source_manifest)
    target = load_falcon(target_manifest)
    if source['subject_id'] == target['subject_id']:
        raise ValueError('Cross-subject coverage requires distinct observed subjects')
    if source['muscle_names'] != target['muscle_names']:
        raise ValueError('Exact source muscle names/order must match without guessed coordinates')
    if len(set(source['muscle_names'])) != len(source['muscle_names']):
        raise ValueError('Source muscle names must be unique')
    source_trials, source_excluded = prepare_trials(source)
    target_trials, target_excluded = prepare_trials(target)
    source_number = config['source_training_trials']
    inner_number = config['source_inner_training_trials']
    calibration_number = config['target_calibration_trials']
    if not 1 < inner_number < source_number < len(source['trials']):
        raise ValueError('Source chronology requires fitting, internal selection, and evaluation trials')
    if not 1 <= calibration_number < len(target['trials']):
        raise ValueError('Target calibration must precede disjoint evaluation trials')
    if any(size < 1 or size > calibration_number for size in config['label_budgets']):
        raise ValueError('Target label budgets exceed the chronological calibration pool')
    alphas = np.asarray(config['ridge_alphas'], dtype=float)
    if alphas.ndim != 1 or len(alphas) == 0 or not np.isfinite(alphas).all() or np.any(alphas < 0):
        raise ValueError('Ridge candidates must be finite nonnegative penalties')
    training = [trial for trial in source_trials if trial['original_trial_row'] < source_number]
    inner_training = [trial for trial in training if trial['original_trial_row'] < inner_number]
    inner_selection = [trial for trial in training if trial['original_trial_row'] >= inner_number]
    source_evaluation = [trial for trial in source_trials if trial['original_trial_row'] >= source_number]
    calibration = [trial for trial in target_trials if trial['original_trial_row'] < calibration_number]
    target_evaluation = [trial for trial in target_trials if trial['original_trial_row'] >= calibration_number]
    for split in (inner_training, inner_selection, source_evaluation, calibration, target_evaluation):
        if not split:
            raise ValueError('Coverage exclusions leave a required chronological split empty')
    identities = lambda trials: [trial['trial_id'] for trial in trials]
    source_rows = lambda trials: [trial['original_trial_row'] for trial in trials]
    splits = {
        'source_subject': source['subject_id'], 'target_subject': target['subject_id'],
        'source_asset_sha256': source_manifest['sha256'], 'target_asset_sha256': target_manifest['sha256'],
        'source_training': identities(training), 'source_inner_training': identities(inner_training),
        'source_inner_selection': identities(inner_selection), 'source_evaluation': identities(source_evaluation),
        'target_calibration': identities(calibration), 'target_evaluation': identities(target_evaluation),
        'target_label_budgets': {
            str(size): identities([trial for trial in calibration if trial['original_trial_row'] < size])
            for size in config['label_budgets']
        },
        'original_trial_rows': {'source_training': source_rows(training), 'source_evaluation': source_rows(source_evaluation),
                                'target_calibration': source_rows(calibration), 'target_evaluation': source_rows(target_evaluation)},
        'muscle_names': source['muscle_names'], 'anonymous_features': FEATURE_NAMES,
        'config_sha256': hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
    }
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    save_immutable(output / 'split_manifest.json', splits)
    inner_scaler = StandardScaler().fit(flatten(inner_training, 'features'))
    inner_features = inner_scaler.transform(flatten(inner_training, 'features'))
    selection_features = inner_scaler.transform(flatten(inner_selection, 'features'))
    inner_targets = flatten(inner_training, 'targets')
    alpha_scores = []
    for alpha in alphas:
        model = Ridge(alpha=alpha).fit(inner_features, inner_targets)
        prediction = model.predict(selection_features)
        losses = trial_losses(inner_selection, prediction)
        alpha_scores.append({'alpha': float(alpha), 'mean_trial_selection_mse': float(losses.mean())})
    selected_alpha = min(alpha_scores, key=lambda item: item['mean_trial_selection_mse'])['alpha']
    training_features = flatten(training, 'features')
    training_targets = flatten(training, 'targets')
    scaler = StandardScaler().fit(training_features)
    normalized_training = scaler.transform(training_features)
    source_model = Ridge(alpha=selected_alpha).fit(normalized_training, training_targets)
    source_mean = training_targets.mean(axis=0)
    mean_model = copy.copy(source_model)
    mean_model.coef_ = np.zeros_like(source_model.coef_)
    mean_model.intercept_ = source_mean
    source_features = flatten(source_evaluation, 'features')
    target_features = flatten(target_evaluation, 'features')
    saved_arrays = {}
    for prefix, recording in (('source_native', source), ('target_native', target)):
        native_trials = recording['trials']
        native_lengths = [len(trial['timestamps']) for trial in native_trials]
        saved_arrays[prefix + '_trial_ids'] = np.asarray(identities(native_trials))
        saved_arrays[prefix + '_trial_offsets'] = np.concatenate([[0], np.cumsum(native_lengths)])
        for field in ('source_eval_mask', 'neural_valid', 'target_valid', 'timestamps', 'bin_right_seconds'):
            saved_arrays[prefix + '_' + field] = flatten(native_trials, field)
    for prefix, trials in (('source_evaluation', source_evaluation), ('target_evaluation', target_evaluation)):
        lengths = [len(trial['targets']) for trial in trials]
        saved_arrays[prefix + '_trial_ids'] = np.asarray(identities(trials))
        saved_arrays[prefix + '_original_trial_rows'] = np.asarray(source_rows(trials))
        saved_arrays[prefix + '_trial_offsets'] = np.concatenate([[0], np.cumsum(lengths)])
        saved_arrays[prefix + '_targets_normalized_emg'] = flatten(trials, 'targets')
        saved_arrays[prefix + '_left_seconds'] = flatten(trials, 'left_seconds')
        saved_arrays[prefix + '_right_seconds'] = flatten(trials, 'right_seconds')
        saved_arrays[prefix + '_native_sample_indices'] = flatten(trials, 'native_sample_indices')
    results = []
    for name, model in (('source_frozen', source_model), ('source_mean', mean_model)):
        for domain, trials, observations in (
            ('source', source_evaluation, source_features), ('target', target_evaluation, target_features),
        ):
            identifier = domain + '_' + name
            path = output / (identifier + '.npz')
            prediction = _checkpoint_prediction(path, model, scaler, observations)
            losses = trial_losses(trials, prediction)
            saved_arrays[identifier + '_prediction_normalized_emg'] = prediction
            results.append({'domain': domain, 'control': name, 'label_budget': 0,
                            'mean_trial_mse_normalized_emg_squared': float(losses.mean()),
                            'trial_mse_normalized_emg_squared': losses.tolist(),
                            'checkpoint_file': path.name,
                            'checkpoint_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'checkpoint_restored_predictions_identical': True})
    for budget in config['label_budgets']:
        labeled_trials = [trial for trial in calibration if trial['original_trial_row'] < budget]
        if not labeled_trials:
            raise ValueError('Coverage exclusions leave a requested label budget empty')
        label_features = scaler.transform(flatten(labeled_trials, 'features'))
        label_targets = flatten(labeled_trials, 'targets')
        frozen_training_prediction = source_model.predict(label_features)
        residual_targets = label_targets - frozen_training_prediction
        for name, fitted_targets, base in (
            ('target_calibration_mean', label_targets, None),
            ('target_direct', label_targets, None), ('source_plus_residual', residual_targets, source_model),
        ):
            if name == 'target_calibration_mean':
                model = copy.copy(source_model)
                model.coef_ = np.zeros_like(source_model.coef_)
                model.intercept_ = label_targets.mean(axis=0)
            else:
                model = Ridge(alpha=selected_alpha).fit(label_features, fitted_targets)
            identifier = name + '_budget_' + str(budget)
            path = output / (identifier + '.npz')
            prediction = _checkpoint_prediction(path, model, scaler, target_features, base)
            losses = trial_losses(target_evaluation, prediction)
            saved_arrays[identifier + '_prediction_normalized_emg'] = prediction
            results.append({'domain': 'target', 'control': name, 'label_budget': budget,
                            'eligible_label_trials': len(labeled_trials),
                            'mean_trial_mse_normalized_emg_squared': float(losses.mean()),
                            'trial_mse_normalized_emg_squared': losses.tolist(),
                            'checkpoint_file': path.name,
                            'checkpoint_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'checkpoint_restored_predictions_identical': True})
    summaries = []
    for row in results:
        domain = row['domain']
        reference = next(item for item in results if item['domain'] == domain and item['control'] == 'source_mean')
        references = [('source_training_mean', reference)]
        if domain == 'target' and row['control'] in ('target_direct', 'source_plus_residual'):
            calibration_mean = next(item for item in results
                                    if item['control'] == 'target_calibration_mean' and item['label_budget'] == row['label_budget'])
            references.append(('target_calibration_mean_same_budget', calibration_mean))
        if row['control'] == 'source_plus_residual':
            direct = next(item for item in results
                          if item['control'] == 'target_direct' and item['label_budget'] == row['label_budget'])
            references.append(('target_direct_same_budget', direct))
        trials = source_evaluation if domain == 'source' else target_evaluation
        for reference_name, reference_row in references:
            for block_length in config['uncertainty_block_lengths']:
                summary = loss_summary(
                    row['trial_mse_normalized_emg_squared'], identities(trials),
                    reference_row['trial_mse_normalized_emg_squared'], block_length=block_length,
                    draws=config['bootstrap_draws'], seed=config['seed'],
                )
                summaries.append({'domain': domain, 'control': row['control'], 'label_budget': row['label_budget'],
                                  'paired_reference': reference_name, **summary})
    np.savez_compressed(output / 'predictions.npz', **saved_arrays)
    report = {
        'schema_version': 1, 'config': config, 'manifests': [source_manifest, target_manifest],
        'recording_metadata': [source['metadata'], target['metadata']], 'splits': splits,
        'source_target_units': [source['source_target_units'], target['source_target_units']],
        'source_unit_count': len(source['unit_keys']), 'target_unit_count': len(target['unit_keys']),
        'coverage_audit': {
            'source_retained': [trial['audit'] for trial in source_trials], 'source_whole_trial_exclusions': source_excluded,
            'target_retained': [trial['audit'] for trial in target_trials], 'target_whole_trial_exclusions': target_excluded,
        },
        'source_selection': alpha_scores, 'selected_ridge_alpha': selected_alpha,
        'normalization': {'feature_mean': scaler.mean_.tolist(), 'feature_scale': scaler.scale_.tolist()},
        'results': results, 'uncertainty': summaries,
        'source_sha256': {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                          for name in ('cross_subject.py', 'falcon.py', 'evaluation.py')},
        'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip()),
        'package_versions': {name: importlib.metadata.version(name) for name in ('numpy', 'scikit-learn', 'pynwb')},
        'protocol': 'Custom chronological calibration-asset split, not official FALCON scoring. Original source trial-row boundaries define every split and label budget; missing trials are excluded without replacement by later trials. Fit source-only CEREBRO normalization and select ridge on source internal trials only. No target evaluation fitting/selection; nested chronological target calibration budgets only. Optimization weights samples; reported error averages trial rows equally.',
        'limitations': [
            'Seven anonymous neural moments are deliberately lossy population summaries, not unit-identity alignment or learned foundation representations',
            'Sorted units have no cross-subject identity; unit row positions are never used as shared feature coordinates',
            'Exact muscle names establish output coordinates only; object conditions, task distributions, and physiological scaling need not match across subjects',
            'Published author quantile-normalized EMG is used in native values; NWB mV metadata does not certify calibrated absolute amplitude',
            'Author full-recording EMG filters and quantile normalization precede these trial splits; original preprocessing cannot be certified leakage-free',
            'Native target at left bin edge is paired with neural counts through right edge; this is offline prediction with current-bin access, not a causal real-time controller',
            'Only one public calibration recording per subject; subject, session, and date effects are confounded',
            'Source B is a mutable draft release pinned by asset UUID and verified checksum',
            'Moving-block intervals are descriptive sensitivity analyses; independence and block-length adequacy are not established',
        ],
        'arrays': {name: {'shape': list(value.shape), 'sha256': array_digest(value)} for name, value in saved_arrays.items()},
    }
    (output / 'results.json').write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n')
    return report


def write_artifacts(report, report_path, markdown_path, figure_path,
                    config_path='configs/cross_subject_12.json', output_path='data/processed/cross_subject_12'):
    """Render measured trial-error comparisons with disclosed temporal blocks."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    report_path = Path(report_path)
    markdown_path = Path(markdown_path)
    figure_path = Path(figure_path)
    for path in (report_path, markdown_path, figure_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n')
    target_rows = [row for row in report['results'] if row['domain'] == 'target']
    chosen_block = max(report['config']['uncertainty_block_lengths'])
    figure, axis = plt.subplots(figsize=(8, 5))
    for name, label in (
        ('target_direct', 'Direct target ridge'), ('source_plus_residual', 'Source + target residual'),
        ('target_calibration_mean', 'Target calibration mean (no neural features)'),
    ):
        rows = sorted([row for row in target_rows if row['control'] == name], key=lambda row: row['label_budget'])
        budgets = np.asarray([row['label_budget'] for row in rows])
        means = np.asarray([row['mean_trial_mse_normalized_emg_squared'] for row in rows])
        intervals = []
        for row in rows:
            summary = next(item for item in report['uncertainty']
                           if item['domain'] == 'target' and item['control'] == name
                           and item['label_budget'] == row['label_budget']
                           and item['resampling']['block_length_trials'] == chosen_block)
            intervals.append(summary['percentile_interval'])
        intervals = np.asarray(intervals)
        # Percentile bands need not contain the empirical mean; draw bounds directly.
        axis.plot(budgets, means, marker='o', label=label)
        axis.vlines(budgets, intervals[:, 0], intervals[:, 1], alpha=.6)
    for name, label, style in (('source_frozen', 'Frozen source ridge', '--'), ('source_mean', 'Source-training mean', ':')):
        row = next(item for item in target_rows if item['control'] == name)
        axis.axhline(row['mean_trial_mse_normalized_emg_squared'], linestyle=style, label=label)
    axis.set_xlabel('Chronological target calibration trial budget')
    axis.set_ylabel('Mean trial MSE (published normalized EMG values²)')
    subjects = report['splits']['source_subject'] + ' → ' + report['splits']['target_subject']
    axis.set_title(subjects + ': anonymous population moments\nCustom calibration-asset split; 20 ms native neural bins')
    axis.legend(fontsize=9)
    axis.grid(alpha=.2)
    provenance = 'DANDI 000941 v0.241029.1405 / 001209 draft (pinned assets); '
    provenance += str(chosen_block) + '-trial block percentile intervals; offline same-bin access'
    figure.text(.5, .015, provenance, ha='center', fontsize=7)
    figure.tight_layout(rect=(0, .045, 1, 1))
    figure.savefig(figure_path, dpi=160)
    plt.close(figure)
    source_mean = next(row for row in target_rows if row['control'] == 'source_mean')
    lines = [
        '# Cross-subject anonymous-population baseline', '',
        subjects + '; authentic public FALCON calibration recordings. This is a custom chronological experiment, not an official FALCON score.', '',
        'Observed recordings contain ' + str(report['source_unit_count']) + ' source and ' + str(report['target_unit_count']) + ' target units. Neural unit rows have no assumed cross-subject identity. Seven permutation-invariant count moments are deliberately lossy features; exact source muscle names define shared output coordinates only.', '',
        'Common muscle coordinates: ' + ', '.join(report['splits']['muscle_names']) + '.', '',
        'Source first' + str(report['config']['source_training_trials']) + ' original trial rows fit the final model, with first' + str(report['config']['source_inner_training_trials']) + ' used for internal fitting and the rest for ridge selection. Source-selected alpha: ' + str(report['selected_ridge_alpha']) + '. Target first' + str(report['config']['target_calibration_trials']) + ' original trial rows are the calibration pool; remaining eligible trials are evaluation only. Empty trials never shift these boundaries.', '',
        'Native source keep masks, per-unit observation coverage, finite targets, original sample indices, and exact timestamps are preserved. Eligible source evaluation trials: ' + str(len(report['splits']['source_evaluation'])) + '; target evaluation trials: ' + str(len(report['splits']['target_evaluation'])) + '.', '',
        '| Target control | Label trials | Mean trial MSE (normalized EMG²) |',
        '|---|---:|---:|',
    ]
    for row in target_rows:
        lines.append('| ' + row['control'] + ' | ' + str(row['label_budget']) + ' | ' + format(row['mean_trial_mse_normalized_emg_squared'], '.8f') + ' |')
    frozen = next(row for row in target_rows if row['control'] == 'source_frozen')
    difference = frozen['mean_trial_mse_normalized_emg_squared'] - source_mean['mean_trial_mse_normalized_emg_squared']
    largest_budget = max(report['config']['label_budgets'])
    direct = next(row for row in target_rows if row['control'] == 'target_direct' and row['label_budget'] == largest_budget)
    mean = next(row for row in target_rows if row['control'] == 'target_calibration_mean' and row['label_budget'] == largest_budget)
    residual = next(row for row in target_rows if row['control'] == 'source_plus_residual' and row['label_budget'] == largest_budget)
    direct_minus_mean = direct['mean_trial_mse_normalized_emg_squared'] - mean['mean_trial_mse_normalized_emg_squared']
    residual_minus_direct = residual['mean_trial_mse_normalized_emg_squared'] - direct['mean_trial_mse_normalized_emg_squared']
    lines.extend(['', 'Frozen source ridge minus source-training mean target MSE: ' + format(difference, '.8f') + ' normalized EMG². Negative values favor ridge. This measurement does not establish universal transfer or neural correspondence.', '',
                  'Target calibration means use the same labeled trial pool without neural features, separating EMG baseline adjustment from measured neural-feature benefit.', '',
                  'At the largest label budget (' + str(largest_budget) + '), direct target ridge minus target calibration mean MSE is ' + format(direct_minus_mean, '.8f') + '; source-plus-residual minus direct ridge is ' + format(residual_minus_direct, '.8f') + ' normalized EMG². Negative contrasts favor the first method. Paired block intervals for both contrasts are recorded in JSON; these measured differences do not imply generalizable transfer superiority.', '',
                  'Uncertainty uses paired trial losses and both independent-trial and moving-block resampling at configured block lengths; the figure shows the largest configured block. These descriptive intervals do not certify independence or significance.', '',
                  '## Provenance and limitations', ''])
    for manifest in report['manifests']:
        lines.append('- DANDI ' + manifest['dandiset_id'] + ', version ' + manifest['version'] + ', asset `' + manifest['asset_id'] + '`, SHA256 `' + manifest['sha256'] + '`.')
    lines.append('')
    for limitation in report['limitations']:
        lines.append('- ' + limitation)
    command = shlex.join(['python', '-m', 'cerebro.cross_subject', '--config', str(config_path),
                          '--output', str(output_path), '--report', str(report_path),
                          '--markdown', str(markdown_path), '--figure', str(figure_path)])
    lines.extend(['', 'Published native targets are author quantile-normalized EMG. Full-recording author filters/scaling predate CEREBRO splits, so original preprocessing is not certified leakage-free. The stored mV label does not establish absolute EMG amplitude.', '',
                  'Checkpoints and prediction/mask archives remain in Git-ignored `' + str(output_path) + '`. Every checkpoint was restored and predictions verified; JSON binds code/environment, splits, checkpoints, and array hashes.', '',
                  'Reproduce: `' + command + '`.', '',
                  '![Calibration comparison](figures/' + figure_path.name + ')', ''])
    markdown_path.write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/cross_subject_12.json')
    parser.add_argument('--output', default='data/processed/cross_subject_12')
    parser.add_argument('--report', default='reports/cross_subject_12.json')
    parser.add_argument('--markdown', default='reports/cross_subject_12.md')
    parser.add_argument('--figure', default='reports/figures/cross_subject_12_calibration.png')
    arguments = parser.parse_args()
    report = run(arguments.config, arguments.output)
    write_artifacts(report, arguments.report, arguments.markdown, arguments.figure,
                    arguments.config, arguments.output)
    print(json.dumps({'subjects': [report['splits']['source_subject'], report['splits']['target_subject']],
                      'selected_alpha': report['selected_ridge_alpha'], 'controls': len(report['results'])}))


if __name__ == '__main__':
    main()
