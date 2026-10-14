"""Generate a local, offline explorer of provenance-verified research outputs."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from cerebro.benchmark import array_digest


def verified_arrays(directory, report, filename):
    with np.load(directory / filename, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    if set(arrays) != set(report["arrays"]):
        raise ValueError("Array provenance does not cover all archive entries")
    for name, metadata in report["arrays"].items():
        if name not in arrays or array_digest(arrays[name]) != metadata["sha256"]:
            raise ValueError(f"Array provenance mismatch: {name}")
    return arrays


def explorer_data(classical, sequence=None):
    directory = Path(classical)
    report_bytes = (directory / "results.json").read_bytes()
    report = json.loads(report_bytes)
    arrays = verified_arrays(directory, report, "arrays.npz")
    trial_ids = np.asarray(report["evaluation_trial_ids"])
    validation_rows = []
    for trial_id in trial_ids:
        matching = np.flatnonzero(arrays["trial_ids"] == trial_id)
        if len(matching) != 1:
            raise ValueError("Evaluation trial must have one original identity")
        validation_rows.append(int(matching[0]))
    predictions = {}
    metrics = {}
    limitations = list(report["limitations"])
    for name, values in report["metrics"].items():
        predictions[name] = arrays[name + "_prediction_m_s"].tolist()
        metrics[name] = values["mse_m2_s2"]
    if sequence is not None:
        sequence_directory = Path(sequence)
        sequence_report = json.loads((sequence_directory / "results.json").read_text())
        current_digest = hashlib.sha256(report_bytes).hexdigest()
        if sequence_report["input_report_sha256"] != current_digest:
            raise ValueError("Sequence report does not match classical provenance")
        sequence_arrays = verified_arrays(sequence_directory, sequence_report, "predictions.npz")
        if not np.array_equal(sequence_arrays["evaluation_trial_ids"], trial_ids):
            raise ValueError("Sequence evaluation trial identities differ")
        limitations.extend(sequence_report.get("limitations", []))
        for values in sequence_report["results"]:
            name = values["model"] + "_seed_" + str(values["seed"])
            predictions[name] = sequence_arrays[name + "_prediction_m_s"].tolist()
            metrics[name] = values["mse_m2_s2"]
    target = arrays["velocity_m_s"][validation_rows]
    for prediction in predictions.values():
        if np.asarray(prediction).shape != target.shape:
            raise ValueError("Prediction dimensions differ from evaluation targets")
    counts = arrays["counts"][validation_rows]
    population_counts = counts.sum(axis=2)
    width_seconds = report["config"]["bin_width_seconds"]
    population_rates = population_counts / width_seconds
    return {
        "trial_ids": trial_ids.tolist(), "time_seconds": arrays["bin_right_seconds"][validation_rows].tolist(),
        "target": target.tolist(), "predictions": predictions, "metrics": metrics,
        "pca": arrays["pca_validation_latents"].tolist(),
        "population_counts": population_counts.tolist(), "population_rates": population_rates.tolist(),
        "bin_width_seconds": width_seconds, "heldin_units": len(arrays["unit_ids"]),
        "source": report["asset"], "limitations": limitations,
        "information_policy": report["information_policy"],
    }


HTML = r"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>CEREBRO research explorer</title>
<style>body{font:16px system-ui;margin:2rem auto;max-width:1100px;padding:0 1rem;color:#172b3a}select{padding:.4rem;margin:.4rem}svg{width:100%;height:240px;border:1px solid #ccd6de}pre{white-space:pre-wrap;font:14px system-ui}table{border-collapse:collapse}td,th{padding:.35rem .8rem;text-align:left;border-bottom:1px solid #ddd}.legend{color:#516473}</style>
<h1>CEREBRO research explorer</h1><p>Local empirical outputs. Source validation is exploratory evaluation; it is not an untouched test.</p>
<label>Trial <select id="trial"></select></label><label>Model <select id="model"></select></label>
<h2>Hand velocity</h2><p class="legend">Actual: blue; prediction: orange. Coordinates in m/s; horizontal axis is original bin-right timestamp in seconds.</p>
<h3>x velocity</h3><svg id="vx" role="img" aria-label="Actual and predicted x velocity"></svg>
<h3>y velocity</h3><svg id="vy" role="img" aria-label="Actual and predicted y velocity"></svg>
<h2>Training-fitted PCA trajectory</h2><label>Horizontal coordinate <select id="pcx"></select></label><label>Vertical coordinate <select id="pcy"></select></label><p>Latent coordinates of standardized counts; arbitrary score units, not anatomical axes. Blue line follows increasing time.</p><svg id="latent" role="img" aria-label="Selected PCA coordinates"></svg>
<h2>Neural activity</h2><p id="summary"></p><p>Blue: simultaneous population spike count per bin. Firing rate is count divided by bin duration, without smoothing.</p><svg id="activity" role="img" aria-label="Population spike counts"></svg>
<h2>Exploratory model comparison</h2><p>Mean squared error averages both velocity coordinates and complete bins across the same source-validation trials. Seeds are initialization repeats.</p><table><thead><tr><th>Model</th><th>MSE (m²/s²)</th></tr></thead><tbody id="metrics"></tbody></table>
<h2>Provenance and limitations</h2><pre id="source"></pre><pre id="limitations"></pre>
<section id="longitudinal-panel" hidden><h2>LINK channel transfer and calibration</h2><p>Same-bin finger position MSE in flexion units²; not Maze hand velocity. Horizontal axis: labeled calibration trials. Orange: selected method; blue: frozen source baseline.</p><label>Calibration method <select id="adaptation-method"></select></label><svg id="calibration" role="img" aria-label="Calibration budget comparison"></svg><h3>Session geometry</h3><pre id="shift"></pre><pre id="longitudinal-source"></pre></section>
<section id="transfer-panel" hidden><h2>Held-out session representation controls</h2><p>Two earlier LINK recordings pretrain; the third session supplies calibration and evaluation. MSE in flexion units². Seed ranges are not biological confidence intervals. No validated neural foundation model claim.</p><label>Ablation setting <select id="transfer-setting"></select></label><table><thead><tr><th>Control</th><th>Labels</th><th>Mean MSE</th><th>Seed range</th></tr></thead><tbody id="transfer-metrics"></tbody></table><h3>Source-session identity diagnostic</h3><pre id="identity"></pre><pre id="transfer-source"></pre></section>
<p id="availability">Unselected longitudinal/representation outputs are unavailable. Broad cross-subject generalization and biological closed-loop claims remain unvalidated. No simulated outputs are substituted.</p>
<script id="research-data" type="application/json">__DATA__</script>
<script>
const data=JSON.parse(document.getElementById('research-data').textContent);
const get=id=>document.getElementById(id);
function option(select,label,value){const item=document.createElement('option');item.textContent=label;item.value=value;select.append(item);}
data.trial_ids.forEach((id,index)=>option(get('trial'),String(id),index));
Object.keys(data.predictions).forEach(name=>option(get('model'),name,name));
for(let index=0;index<data.pca[0][0].length;index++){option(get('pcx'),'PC '+(index+1),index);option(get('pcy'),'PC '+(index+1),index);}
get('pcy').value=data.pca[0][0].length>1?'1':'0';
get('source').textContent=JSON.stringify(data.source,null,2)+'\n'+data.information_policy;
get('limitations').textContent=data.limitations.join('\n');
for(const [name,mse] of Object.entries(data.metrics)){const row=document.createElement('tr');for(const text of [name,mse.toFixed(6)]){const cell=document.createElement('td');cell.textContent=text;row.append(cell);}get('metrics').append(row);}
function plot(id,series){const svg=get(id);svg.replaceChildren();svg.setAttribute('viewBox','0 0 900 240');const xs=series.flatMap(s=>s.points.map(p=>p[0]));const ys=series.flatMap(s=>s.points.map(p=>p[1]));const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);const dx=xmax-xmin||1,dy=ymax-ymin||1;for(const s of series){const line=document.createElementNS('http://www.w3.org/2000/svg','polyline');const points=s.points.map(p=>(55+800*(p[0]-xmin)/dx)+','+(200-165*(p[1]-ymin)/dy)).join(' ');line.setAttribute('points',points);line.setAttribute('fill','none');line.setAttribute('stroke',s.color);line.setAttribute('stroke-width','2');svg.append(line);}for(const [x,y,text] of [[55,228,xmin.toFixed(3)],[800,228,xmax.toFixed(3)],[2,38,ymax.toFixed(3)],[2,200,ymin.toFixed(3)]]){const label=document.createElementNS('http://www.w3.org/2000/svg','text');label.setAttribute('x',x);label.setAttribute('y',y);label.setAttribute('font-size','12');label.textContent=text;svg.append(label);}}
function update(){const trial=Number(get('trial').value),model=get('model').value,times=data.time_seconds[trial];for(const [id,coordinate] of [['vx',0],['vy',1]]){plot(id,[{color:'#2274a5',points:times.map((t,i)=>[t,data.target[trial][i][coordinate]])},{color:'#d65a31',points:times.map((t,i)=>[t,data.predictions[model][trial][i][coordinate]])}]);}const pcx=Number(get('pcx').value),pcy=Number(get('pcy').value);plot('latent',[{color:'#2274a5',points:data.pca[trial].map(p=>[p[pcx],p[pcy]])}]);plot('activity',[{color:'#2274a5',points:times.map((t,i)=>[t,data.population_counts[trial][i]])}]);const total=data.population_counts[trial].reduce((a,b)=>a+b,0);const meanRate=data.population_rates[trial].reduce((a,b)=>a+b,0)/times.length;get('summary').textContent=(1000*data.bin_width_seconds)+' ms half-open bins; '+data.heldin_units+' held-in units. Trial '+data.trial_ids[trial]+': '+total+' retained spikes; mean population rate '+meanRate.toFixed(2)+' spikes/s. Counts and rates are distinct.';}
for(const id of ['trial','model','pcx','pcy'])get(id).addEventListener('change',update);update();
const longitudinal=data.additional.longitudinal;
if(longitudinal){get('longitudinal-panel').hidden=false;for(const family of Object.keys(longitudinal.curves))option(get('adaptation-method'),family,family);get('shift').textContent=JSON.stringify(longitudinal.geometry,null,2)+'\nIn-sample CCA is exploratory; contacts are not neurons.';get('longitudinal-source').textContent=JSON.stringify({source:longitudinal.source,target:longitudinal.target},null,2)+'\n'+longitudinal.information_policy+'\n'+longitudinal.limitations.join('\n');function updateCalibration(){const points=longitudinal.curves[get('adaptation-method').value];if(points.length){const baseline=points.map(point=>[point[0],longitudinal.frozen_mse]);plot('calibration',[{color:'#d65a31',points:points},{color:'#2274a5',points:baseline}]);}}get('adaptation-method').addEventListener('change',updateCalibration);updateCalibration();}
const transfer=data.additional.transfer;
if(transfer){get('transfer-panel').hidden=false;const settings=[...new Set(transfer.rows.map(row=>row.setting))];settings.forEach(name=>option(get('transfer-setting'),name,name));get('transfer-source').textContent=JSON.stringify(transfer.manifests,null,2)+'\n'+transfer.access_rules+'\n'+transfer.limitations.join('\n');function updateTransfer(){const setting=get('transfer-setting').value;get('transfer-metrics').replaceChildren();for(const metric of transfer.rows.filter(row=>row.setting===setting)){const row=document.createElement('tr');const cells=[metric.control,String(metric.budget),metric.mean.toFixed(6),metric.seed_range.map(value=>value.toFixed(6)).join('–')];for(const value of cells){const cell=document.createElement('td');cell.textContent=value;row.append(cell);}get('transfer-metrics').append(row);}const identity=transfer.identity.filter(row=>row.setting===setting);get('identity').textContent=JSON.stringify(identity.map(row=>({encoder:row.encoder,seed:row.seed,accuracy:row.accuracy,chance:row.balanced_chance_accuracy})),null,2)+'\nAbove-chance date identification indicates retained session information; seeds are not independent subjects.';}get('transfer-setting').addEventListener('change',updateTransfer);updateTransfer();}
</script></html>"""


def additional_results(longitudinal=None, transfer=None):
    """Read verified summaries; keep different targets and units separate."""
    result = {}
    if longitudinal is not None:
        root = Path(longitudinal)
        report = json.loads((root / 'results.json').read_text())
        verified_arrays(root, report, 'arrays.npz')
        curves = {}
        for family in ('direct_recalibration', 'source_plus_residual', 'condition_anchor_alignment'):
            points = []
            for budget in report['config']['calibration_budgets']:
                name = family + '_' + str(budget)
                if name in report['metrics']:
                    points.append([budget, report['metrics'][name]['mean_trial_mse_flexion2']])
            curves[family] = points
        baseline = report['metrics']['frozen_source']['mean_trial_mse_flexion2']
        result['longitudinal'] = {
            'curves': curves, 'frozen_mse': baseline, 'geometry': report['geometry'],
            'source': report['source'], 'target': report['target'],
            'information_policy': report['information_policy'], 'limitations': report['limitations'],
        }
    if transfer is not None:
        root = Path(transfer)
        report = json.loads((root / 'results.json').read_text())
        verified_arrays(root, report, 'predictions.npz')
        grouped = {}
        for row in report['results']:
            key = (row['setting'], row['control'], row['target_label_budget'])
            grouped.setdefault(key, []).append(row['mse_native_position_squared'])
        rows = []
        for (setting, control, budget), losses in sorted(grouped.items()):
            rows.append({
                'setting': setting, 'control': control, 'budget': budget,
                'mean': float(np.mean(losses)), 'seed_range': [min(losses), max(losses)],
            })
        result['transfer'] = {
            'rows': rows, 'identity': report['session_identity_diagnostics'],
            'manifests': report['manifests'], 'access_rules': report['access_rules'],
            'limitations': report['limitations'],
        }
    return result


def generate(classical="data/processed/classical_05", sequence=None, output="data/processed/explorer.html",
             longitudinal=None, transfer=None):
    data = explorer_data(classical, sequence)
    data['additional'] = additional_results(longitudinal, transfer)
    encoded = json.dumps(data, allow_nan=False)
    safe_json = encoded.replace("<", "\\u003c")
    document = HTML.replace("__DATA__", safe_json)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--classical", default="data/processed/classical_05")
    parser.add_argument("--sequence")
    parser.add_argument("--output", default="data/processed/explorer.html")
    parser.add_argument('--longitudinal')
    parser.add_argument('--transfer')
    args = parser.parse_args()
    print(generate(args.classical, args.sequence, args.output, args.longitudinal, args.transfer))


if __name__ == "__main__":
    main()
