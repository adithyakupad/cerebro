/** Rebuild from repository root with bundled runtime paths in RUNTIME_NODE_MODULES,
 * RUNTIME_PYTHON and PRESENTATIONS_SKILL_DIR. No additional packages required. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
const root = process.cwd();
const modules = process.env.RUNTIME_NODE_MODULES;
const skill = process.env.PRESENTATIONS_SKILL_DIR;
const python = process.env.RUNTIME_PYTHON;
if (!modules || !skill || !python) throw new Error('Set bundled runtime environment paths listed in this source header');
const require = createRequire(path.join(modules, 'package.json'));
const { Presentation, PresentationFile } = await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const { finalizePresentation, applyPresentationChartFont } = await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const build = path.join(root,'data/processed/m023_presentation_build');
await fs.mkdir(build,{recursive:true});
const read = async relative => JSON.parse(await fs.readFile(path.join(root,relative),'utf8'));
const reliability = await read('data/processed/m023_reliability/results.json');
const dynamics = await read('reports/m023_dynamics.json');
const budget = reliability.evaluation.budgets['15'];
const gate = dynamics.temporal_gate;
const deck = Presentation.create({slideSize:{width:1280,height:720}});
const ink='#172C42', blue='#176D9B', grey='#526371';
function text(slide,content,left,top,width,height,size=25,bold=false,color=ink) {
 const shape=slide.shapes.add({geometry:'textbox',position:{left,top,width,height},fill:'none',line:{fill:'none',width:0}});
 shape.text=content;shape.text.style={typeface:'Arial',fontSize:size,bold,color};return shape;
}
function slide(title,source) {
 const s=deck.slides.add();s.background.fill='#FFFFFF';
 text(s,title,64,42,1152,92,40,true);
 text(s,`CEREBRO Mission 023     ${deck.slides.items.length}/10`,64,674,1152,25,16,false,grey);
 s.speakerNotes.text=`Sources: ${source}\nDataset attribution: Temmar and colleagues (2025), LINK, DANDI001201 version0.251023.2336, https://doi.org/10.48324/dandi.001201/0.251023.2336, CC-BY-4.0. Offline computational research, one biological animal. No clinical or biological closed-loop validation.`;
 return s;
}
function paragraphs(s,items,start=166,size=27,gap=100) {
 items.forEach((item,i)=>text(s,item,66,start+i*gap,1135,gap-12,size));
}
function chart(s,categories,values,title,unit,left=65,top=190,width=760,height=355) {
 const c=s.charts.add('bar',{position:{left,top,width,height},title,categories,
 series:[{name:unit,values:values.map(value => Number(value.toFixed(8))),fill:blue}],hasLegend:false,
 titleTextStyle:{typeface:'Arial',fontSize:23},
 barOptions:{direction:'column',grouping:'clustered'},
 xAxis:{textStyle:{typeface:'Arial',fontSize:20}},
 yAxis:{textStyle:{typeface:'Arial',fontSize:18},title:{text:unit,textStyle:{typeface:'Arial',fontSize:19}},numberFormatCode:'0.00'},
 dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{typeface:'Arial',fontSize:20}}});
 applyPresentationChartFont(c,{fontFamily:'Arial'});return c;
}
let s=slide('Predicting adaptation harm in neural decoders','docs/research/m023_protocol.md; reports/m022_calibration_mechanisms.md');
text(s,'Reliability diagnostics and interpretable population dynamics',67,205,1100,140,44,true);
text(s,'A prospective development study with preserved negative findings',67,395,1100,75,30,false,blue);
text(s,'LINK finger-flexion recordings, one macaque',67,510,1100,70,26);
s=slide('Authentic data and a limited generalization unit','docs/datasets/m023_native_eligibility.json; configs/m023_protocol.json');
paragraphs(s,['96 electrode-contact threshold-crossing features with nominal 20 ms bins','Two normalized finger-flexion targets, synchronized native timestamps','Jan 27 source. Jan 30, Feb 4 and Feb 5 development dates','Three later dates pass native eligibility and remain unscored'],156,27,92);
text(s,'LINK: DANDI 001201 v0.251023.2336   doi:10.48324/dandi.001201/0.251023.2336   CC-BY-4.0',65,570,1150,65,18,false,grey);
s=slide('Competing explanations and a falsifiable null','docs/research/m023_protocol.md; src/cerebro/reliability.py');
paragraphs(s,['H1  Calibration task coverage predicts adaptation harm','H2  Estimator variability predicts harm','H3  Neural marginal shift predicts harm','H4  Decoder disagreement predicts harm'],151,27,78);
text(s,'Null: diagnostics fail to beat prespecified simple controls across dates',66,513,1140,95,30,true,blue);
s=slide('Interpretable models and explicit estimands','src/cerebro/reliability.py; src/cerebro/research_dynamics.py; src/cerebro/population.py');
paragraphs(s,['Adaptation outcome: direct MSE − frozen-source MSE, equal weight per trial','Risk model: ridge prediction of that difference using calibration-only features','Population model: PCA or FA observation coordinates with linear latent AR(1)','Forecast score: neural MSE in source-standardized count coordinates'],155,26,105);
text(s,'PCA axes and latent dynamics describe observations. They do not identify causal circuitry.',67,595,1130,45,23,false,grey);
s=slide('Session-aware design and information restrictions','docs/research/m023_protocol.md; configs/m023_protocol.json; docs/research/m023_reliability_clarification.md');
paragraphs(s,['Source training: first 300 Jan 27 trials. All source transforms fit there','Development: only the historically permitted first 75 trials per date','Calibration pool: first 45 trials. Pseudo-evaluation: following 30 trials','Reliability folds hold out one whole development date. Budgets: 5, 15, 30'],151,26,97);
text(s,'Repeated calibration subsets are not new sessions or animals',65,570,1150,55,30,true,blue);
s=slide('Reliability diagnostics fail the development gate','data/processed/m023_reliability/results.json; docs/research/m023_protocol.md');
chart(s,['Combined','Constant','Label only'],['combined','constant','label_only'].map(k=>budget.models[k].risk_mse_flexion4*1e6),'Primary budget: 15 labeled trials','Risk MSE × 10⁻⁶ flexion⁴',65,165,750,380);
text(s,`Balanced accuracy\nCombined  ${(budget.models.combined.pooled_session_weighted_balanced_accuracy*100).toFixed(1)}%\nLabel only  ${(budget.models.label_only.pooled_session_weighted_balanced_accuracy*100).toFixed(2)}%\nMajority  50.0%`,860,210,340,260,26);
text(s,'Combined risk prediction beats constant by 9.46%, but loses to label-only control and fails the all-date uncertainty gate',65,565,1140,80,27,true);
s=slide('Latent forecasts improve on persistence, but miss the gate','reports/m023_dynamics.json; src/cerebro/research_dynamics.py');
chart(s,['Persistence','Source mean','Permuted AR'],gate.comparisons.map(c=>c.equal_date_mean_relative_improvement*100),'Source PCA6, one native-bin forecast','Relative neural MSE reduction (%)',65,165,755,380);
text(s,'5% practical threshold\nrequired against every\nprespecified control',855,235,350,150,28,true);
text(s,'Gains over source mean and time-permuted fitting remain below 5%. No temporal model passes promotion.',65,565,1140,80,28,true);
s=slide('Negative controls constrain the interpretation','data/processed/m023_reliability/results.json; reports/m023_dynamics.json; docs/datasets/m023_native_eligibility.md');
paragraphs(s,['Permuted combined-risk labels retain 67.5% balanced accuracy. Classification alone is insufficient evidence','Label-only predictors challenge a neural-specific reliability interpretation','Condition and dimensionality controls address task mixture and projection choice','Three eligible later sessions remain unscored under the frozen null rules'],151,25,106);
s=slide('A bounded contribution with explicit limitations','docs/research/m023_protocol.md; reports/m023_dynamics.json; reports/m022_calibration_mechanisms.md');
paragraphs(s,['Calibration-only diagnostics do not yet establish reliable prospective harm prediction','Simple temporal structure improves some forecasts without meeting practical promotion criteria','One monkey and three inspected development dates limit biological generalization','Contact mapping does not establish neuron identity. Observational association does not identify physiology'],153,26,107);
s=slide('Next evidence and reproducible research decisions','docs/research/m023_protocol.md; docs/research/m023_interview_pack.md; docs/datasets/m023_native_eligibility.json');
paragraphs(s,['A revised hypothesis requires a new committed protocol before new outcomes','Independent validation must freeze the model and use eligible untouched sessions','New subjects and acquisition-quality metadata would strengthen biological inference','Code, provenance, negative controls and exact reproductions support external review'],155,27,106);
text(s,'No online BCI, subject invariance or neural foundation-model claim follows',65,594,1150,50,25,true,blue);
for (const [i,current] of deck.slides.items.entries()) {
 const png=await deck.export({slide:current,format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
const final=process.env.M023_PRESENTATION_OUTPUT
 ? path.resolve(process.env.M023_PRESENTATION_OUTPUT)
 : path.join(root,'reports/m023_research_presentation.pptx');
await fs.mkdir(path.dirname(final),{recursive:true});
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:python,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
 explicitTotalSlideCount:10,requiredNativeChartOwnerSlides:[6,7],requiredNativeTableOwnerSlides:[],
 materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
 receiptPath:path.join(build,`${path.basename(final)}.validation.json`)});
console.log(final);
