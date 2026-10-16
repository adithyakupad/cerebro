"""Separate subject-discriminability diagnostic on anonymous neural moments."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix
from sklearn.preprocessing import StandardScaler

from cerebro.benchmark import array_digest
from cerebro.cross_subject import FEATURE_NAMES, prepare_trials
from cerebro.falcon import load_falcon


def select_trial_rows(trials, identities):
    """Return one mean-feature row per exact manifest trial identity."""
    if len(set(identities)) != len(identities):
        raise ValueError('Diagnostic trial identities must be unique within a subject')
    trial_lookup = {trial['trial_id']: trial for trial in trials}
    if not identities or any(identity not in trial_lookup for identity in identities):
        raise ValueError('Diagnostic manifest requires nonempty, fully available eligible trials')
    rows = []
    for identity in identities:
        trial = trial_lookup[identity]
        mean_features = trial['features'].mean(axis=0)
        rows.append(mean_features)
    return np.stack(rows)


def fit_identity(training_rows, training_labels, config):
    """Fit both-subject calibration scaler and fixed balanced classifier."""
    rows = np.asarray(training_rows, dtype=float)
    labels = np.asarray(training_labels)
    if rows.ndim != 2 or rows.shape[0] != len(labels) or not np.isfinite(rows).all():
        raise ValueError('Identity fitting requires finite matching trial rows and labels')
    if set(labels.tolist()) != {0, 1}:
        raise ValueError('Both diagnostic subject classes must be observed in training')
    scaler = StandardScaler().fit(rows)
    normalized_rows = scaler.transform(rows)
    classifier = LogisticRegression(
        C=config['C'], max_iter=config['maximum_iterations'],
        random_state=config['seed'], class_weight=config['class_weight'],
    )
    classifier.fit(normalized_rows, labels)
    return scaler, classifier


def restored_predictions(path, rows):
    with np.load(path, allow_pickle=False) as archive:
        normalized_rows = (rows - archive['feature_mean']) / archive['feature_scale']
        scores = normalized_rows @ archive['coefficients'].T + archive['intercept']
        classes = archive['classes']
        predictions = classes[(scores[:, 0] > 0).astype(int)]
    return predictions


def run(config_path, output):
    config = json.loads(Path(config_path).read_text())
    cross_root = Path(config['cross_subject_run'])
    split_path = cross_root / 'split_manifest.json'
    splits = json.loads(split_path.read_text())
    cross_report_path = cross_root / 'results.json'
    cross_report = json.loads(cross_report_path.read_text())
    if splits != cross_report['splits']:
        raise ValueError('Frozen cross-subject split manifest differs from recorded report')
    frozen_config = cross_report['config']
    config_digest = hashlib.sha256(json.dumps(frozen_config, sort_keys=True).encode()).hexdigest()
    if splits['config_sha256'] != config_digest:
        raise ValueError('Frozen decoder configuration differs from split provenance')
    for name in ('cross_subject.py', 'falcon.py'):
        source_digest = hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
        if cross_report['source_sha256'].get(name) != source_digest:
            raise ValueError('Frozen decoder preparation code differs from current source')
    manifests = [json.loads(Path(config[name]).read_text()) for name in ('source_manifest', 'target_manifest')]
    if manifests[0]['sha256'] != splits['source_asset_sha256'] or manifests[1]['sha256'] != splits['target_asset_sha256']:
        raise ValueError('Diagnostic assets differ from frozen decoder provenance')
    recordings = [load_falcon(manifest) for manifest in manifests]
    if recordings[0]['subject_id'] == recordings[1]['subject_id']:
        raise ValueError('Subject diagnostic requires distinct observed subjects')
    if [recording['subject_id'] for recording in recordings] != [splits['source_subject'], splits['target_subject']]:
        raise ValueError('Diagnostic subject identities disagree with frozen decoder split')
    trials = [prepare_trials(recording)[0] for recording in recordings]
    source_training = select_trial_rows(trials[0], splits['source_training'])
    target_calibration = select_trial_rows(trials[1], splits['target_calibration'])
    source_evaluation = select_trial_rows(trials[0], splits['source_evaluation'])
    target_evaluation = select_trial_rows(trials[1], splits['target_evaluation'])
    if set(splits['source_training']) & set(splits['source_evaluation']):
        raise ValueError('Source diagnostic fitting and evaluation trial identities overlap')
    if set(splits['target_calibration']) & set(splits['target_evaluation']):
        raise ValueError('Target diagnostic fitting and evaluation trial identities overlap')
    source_boundary = frozen_config['source_training_trials']
    inner_boundary = frozen_config['source_inner_training_trials']
    target_boundary = frozen_config['target_calibration_trials']
    if not 1 < inner_boundary < source_boundary < len(recordings[0]['trials']):
        raise ValueError('Frozen source chronological boundaries are invalid')
    if not 1 <= target_boundary < len(recordings[1]['trials']):
        raise ValueError('Frozen target chronological boundary is invalid')
    expected_trials = {
        'source_training': [trial for trial in trials[0] if trial['original_trial_row'] < source_boundary],
        'source_inner_training': [trial for trial in trials[0] if trial['original_trial_row'] < inner_boundary],
        'source_inner_selection': [trial for trial in trials[0]
                                   if inner_boundary <= trial['original_trial_row'] < source_boundary],
        'source_evaluation': [trial for trial in trials[0] if trial['original_trial_row'] >= source_boundary],
        'target_calibration': [trial for trial in trials[1] if trial['original_trial_row'] < target_boundary],
        'target_evaluation': [trial for trial in trials[1] if trial['original_trial_row'] >= target_boundary],
    }
    for name, selected_trials in expected_trials.items():
        expected_ids = [trial['trial_id'] for trial in selected_trials]
        if splits[name] != expected_ids:
            raise ValueError('Frozen trial identities differ from original-row chronological splits')
    expected_rows = {
        name: [trial['original_trial_row'] for trial in expected_trials[name]]
        for name in ('source_training', 'source_evaluation', 'target_calibration', 'target_evaluation')
    }
    expected_budgets = {}
    for budget in frozen_config['label_budgets']:
        if budget < 1 or budget > target_boundary:
            raise ValueError('Frozen label budget exceeds chronological calibration pool')
        budget_trials = [trial for trial in expected_trials['target_calibration']
                         if trial['original_trial_row'] < budget]
        expected_budgets[str(budget)] = [trial['trial_id'] for trial in budget_trials]
    if splits['original_trial_rows'] != expected_rows or splits['target_label_budgets'] != expected_budgets:
        raise ValueError('Frozen original rows or label budgets differ from chronological splits')
    training_rows = np.concatenate([source_training, target_calibration], axis=0)
    training_labels = np.concatenate([np.zeros(len(source_training), dtype=int), np.ones(len(target_calibration), dtype=int)])
    evaluation_rows = np.concatenate([source_evaluation, target_evaluation], axis=0)
    evaluation_labels = np.concatenate([np.zeros(len(source_evaluation), dtype=int), np.ones(len(target_evaluation), dtype=int)])
    scaler, classifier = fit_identity(training_rows, training_labels, config)
    predictions = classifier.predict(scaler.transform(evaluation_rows))
    confusion = confusion_matrix(evaluation_labels, predictions, labels=[0, 1])
    class_counts = confusion.sum(axis=1)
    class_accuracies = np.diag(confusion) / class_counts
    balanced_accuracy = balanced_accuracy_score(evaluation_labels, predictions)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    parameter_path = output / 'parameters.npz'
    np.savez_compressed(parameter_path, feature_mean=scaler.mean_, feature_scale=scaler.scale_,
                        coefficients=classifier.coef_, intercept=classifier.intercept_, classes=classifier.classes_)
    restored = restored_predictions(parameter_path, evaluation_rows)
    if not np.array_equal(restored, predictions):
        raise ValueError('Subject classifier checkpoint restoration changed predictions')
    arrays = {'evaluation_trial_rows': evaluation_rows, 'evaluation_subject_labels': evaluation_labels,
              'evaluation_predictions': predictions,
              'source_evaluation_trial_ids': np.asarray(splits['source_evaluation']),
              'target_evaluation_trial_ids': np.asarray(splits['target_evaluation'])}
    np.savez_compressed(output / 'predictions.npz', **arrays)
    report = {
        'schema_version': 1, 'config': config, 'splits': splits, 'manifests': manifests,
        'cross_subject_report_sha256': hashlib.sha256(cross_report_path.read_bytes()).hexdigest(),
        'cross_subject_split_sha256': hashlib.sha256(split_path.read_bytes()).hexdigest(),
        'cross_subject_bound_source_sha256': cross_report['source_sha256'],
        'feature_names': FEATURE_NAMES, 'feature_reduction': 'mean of anonymous per-bin moments within each eligible trial',
        'subject_labels': {'0': recordings[0]['subject_id'], '1': recordings[1]['subject_id']},
        'training_trial_counts': [len(source_training), len(target_calibration)],
        'evaluation_trial_counts': class_counts.tolist(), 'confusion_true_rows_predicted_columns': confusion.tolist(),
        'balanced_accuracy': float(balanced_accuracy), 'balanced_chance_accuracy': .5,
        'per_subject_accuracy': class_accuracies.tolist(), 'raw_accuracy': float(np.mean(evaluation_labels == predictions)),
        'normalization': {'feature_mean': scaler.mean_.tolist(), 'feature_scale': scaler.scale_.tolist()},
        'parameters_file': parameter_path.name, 'parameters_sha256': hashlib.sha256(parameter_path.read_bytes()).hexdigest(),
        'checkpoint_restored_predictions_identical': True,
        'source_sha256': {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                          for name in ('subject_identity.py', 'cross_subject.py', 'falcon.py')},
        'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip()),
        'package_versions': {name: importlib.metadata.version(name) for name in ('numpy', 'scikit-learn', 'pynwb')},
        'access_rules': 'Fit diagnostic scaler and classifier only on source300 and target75 calibration trial means. This extra75-trial target-feature access is separate from decoder label-budget experiments. No evaluation fitting/selection and no diagnostic feedback into decoders. Explicit subject/session/date/time/trial identifiers are not predictor features.',
        'limitations': [
            'A fixed supervised subject-discriminability probe, not evidence of biological subject recognition',
            'Fixed protocol added after observing the cross-subject benchmark; it was not preregistered before data inspection',
            'One recording per subject confounds subject with session/date/task-distribution and recording differences',
            'Above-chance balanced accuracy indicates retained subject-correlated information, not an identity-free representation',
            'Per-trial mean features use the entire eligible trial offline; this diagnostic is not an online classifier',
            'Balanced class weights compensate the unequal training trial counts; balanced evaluation chance is50%, while raw accuracy has unequal evaluation class priors',
            'Trial independence and confidence/significance are not established; reported accuracy is descriptive',
            'Shared cross12 mask eligibility includes native source masks/coverage and finite author-preprocessed EMG; no EMG amplitudes are predictor inputs',
        ],
        'arrays': {name: {'shape': list(value.shape), 'sha256': array_digest(value)} for name, value in arrays.items()},
    }
    (output / 'results.json').write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n')
    return report


def write_report(report, json_path, markdown_path):
    json_path = Path(json_path)
    markdown_path = Path(markdown_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n')
    labels = report['subject_labels']
    lines = [
        '# Anonymous-feature subject-discriminability diagnostic', '',
        labels['0'] + ' versus ' + labels['1'] + ', using authentic public FALCON calibration recordings.', '',
        'Fixed logistic regression (C1, balanced class weights) receives one mean anonymous-moment vector per eligible trial. No explicit subject, session, timestamp, or trial identifier is a predictor.', '',
        'Fit trial counts: ' + str(report['training_trial_counts']) + '; evaluation trial counts: ' + str(report['evaluation_trial_counts']) + '.', '',
        'Observed balanced accuracy: **' + format(report['balanced_accuracy'] * 100, '.2f') + '%**, versus balanced chance **50%**. Per-subject accuracy: ' + str([round(value * 100, 2) for value in report['per_subject_accuracy']]) + '%.', '',
        'Confusion matrix, true subject rows and predicted subject columns ordered source/target: `' + str(report['confusion_true_rows_predicted_columns']) + '`.', '',
        'Above-chance subject classification indicates subject-correlated information remains in anonymous features. This does not identify its physiological cause or establish subject-independent representations.', '',
        'The diagnostic uses the complete75-trial target calibration feature pool in addition to source300 training trial rows. Its scaler also fits both pools. This access is separate from the5/15/75-label decoder experiments; diagnostic outputs never choose decoder models or preprocessing.', '',
        '## Limitations', '',
    ]
    lines.extend('- ' + limitation for limitation in report['limitations'])
    lines.extend(['', 'Checkpoints and predictions are Git-ignored under `data/processed/subject_identity_13/`; numeric parameters were restored with identical predictions. Frozen cross12 split/report digests, exact asset checksums, code revision, environment versions, and output hashes are recorded in JSON.', '',
                  'Reproduce: `python -m cerebro.subject_identity --config configs/subject_identity_13.json --output data/processed/subject_identity_13`.', ''])
    markdown_path.write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/subject_identity_13.json')
    parser.add_argument('--output', default='data/processed/subject_identity_13')
    parser.add_argument('--report', default='reports/subject_identity_13.json')
    parser.add_argument('--markdown', default='reports/subject_identity_13.md')
    arguments = parser.parse_args()
    report = run(arguments.config, arguments.output)
    write_report(report, arguments.report, arguments.markdown)
    print(json.dumps({'balanced_accuracy': report['balanced_accuracy'], 'per_subject_accuracy': report['per_subject_accuracy']}))


if __name__ == '__main__':
    main()
