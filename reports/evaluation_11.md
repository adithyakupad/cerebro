# Common trial-level evaluation

Stored empirical loss summaries; no models were trained or selected.

- MC_Maze resamples 25 whole trials assuming independent curated-session trials
- LINK uses moving blocks of five chronological target trials as sensitivity analysis
- Seeds are averaged within each biological trial, not treated as new biological samples
- Percentile bands are not calibrated population confidence intervals
- No test-winner selection, p-values, significance or multiplicity-adjusted claims
- Within-session m²/s² and LINK flexion² are distinct outcomes and are never pooled
- Paired change is method minus reference; negative values mean lower observed loss

Initialization-seed ranges describe optimization variation separately from trial uncertainty. Single-fit methods have a degenerate seed range.

| Experiment / method | Units | Mean loss | Trial percentile band | Paired change | Paired band | Seed mean range |
|---|---|---:|---|---:|---|---|
| classical_05 / fa_ridge | m²/s² | 0.037343 | [0.033308, 0.041435] | -0.000982 | [-0.001560, -0.000400] | [0.037343, 0.037343] |
| classical_05 / go_time_template | m²/s² | 0.037487 | [0.033423, 0.042068] | -0.000837 | [-0.002366, 0.000715] | [0.037487, 0.037487] |
| classical_05 / kalman | m²/s² | 0.031314 | [0.028434, 0.034061] | -0.007011 | [-0.009899, -0.004432] | [0.031314, 0.031314] |
| classical_05 / linear | m²/s² | 0.035457 | [0.032353, 0.038576] | -0.002868 | [-0.004580, -0.001066] | [0.035457, 0.035457] |
| classical_05 / mean | m²/s² | 0.038325 | [0.033941, 0.042766] | 0.000000 | [0.000000, 0.000000] | [0.038325, 0.038325] |
| classical_05 / pca_ridge | m²/s² | 0.036226 | [0.032595, 0.040011] | -0.002099 | [-0.003139, -0.001051] | [0.036226, 0.036226] |
| classical_05 / ridge | m²/s² | 0.035421 | [0.032312, 0.038543] | -0.002903 | [-0.004587, -0.001128] | [0.035421, 0.035421] |
| sequence_06 / {'model': 'gru'} | m²/s² | 0.036672 | [0.032943, 0.040680] | -0.001653 | [-0.002651, -0.000609] | [0.036492, 0.036841] |
| sequence_06 / {'model': 'lstm'} | m²/s² | 0.036637 | [0.032627, 0.040596] | -0.001688 | [-0.002352, -0.000972] | [0.036592, 0.036721] |
| sequence_06 / {'model': 'mlp'} | m²/s² | 0.037380 | [0.033251, 0.041517] | -0.000945 | [-0.001717, -0.000224] | [0.036648, 0.038237] |
| sequence_06 / {'model': 'state_space'} | m²/s² | 0.034582 | [0.030718, 0.038650] | -0.003743 | [-0.004788, -0.002643] | [0.034082, 0.034940] |
| sequence_06 / {'model': 'temporal_cnn'} | m²/s² | 0.031052 | [0.027990, 0.033965] | -0.007273 | [-0.009432, -0.005013] | [0.030568, 0.031781] |
| sequence_06 / {'model': 'transformer'} | m²/s² | 0.035947 | [0.032356, 0.039810] | -0.002377 | [-0.003654, -0.000982] | [0.035316, 0.036289] |
| representation_07 / {'control': 'pretrained_finetuned', 'label_budget_trials': 5} | m²/s² | 0.043498 | [0.038982, 0.048022] | 0.005173 | [0.002548, 0.007945] | [0.042499, 0.044103] |
| representation_07 / {'control': 'pretrained_finetuned', 'label_budget_trials': 15} | m²/s² | 0.040875 | [0.036510, 0.045391] | 0.002550 | [0.001657, 0.003462] | [0.040760, 0.040949] |
| representation_07 / {'control': 'pretrained_finetuned', 'label_budget_trials': 75} | m²/s² | 0.040215 | [0.035950, 0.044657] | 0.001890 | [0.001092, 0.002761] | [0.040027, 0.040421] |
| representation_07 / {'control': 'pretrained_frozen_ridge', 'label_budget_trials': 5} | m²/s² | 0.046657 | [0.042220, 0.051273] | 0.008332 | [0.004896, 0.011654] | [0.045067, 0.047756] |
| representation_07 / {'control': 'pretrained_frozen_ridge', 'label_budget_trials': 15} | m²/s² | 0.040075 | [0.035816, 0.044106] | 0.001751 | [0.000052, 0.003529] | [0.039205, 0.040579] |
| representation_07 / {'control': 'pretrained_frozen_ridge', 'label_budget_trials': 75} | m²/s² | 0.036119 | [0.032587, 0.039651] | -0.002206 | [-0.003539, -0.000749] | [0.035824, 0.036508] |
| representation_07 / {'control': 'random_frozen_ridge', 'label_budget_trials': 5} | m²/s² | 0.046531 | [0.042064, 0.051163] | 0.008207 | [0.004785, 0.011541] | [0.045260, 0.047338] |
| representation_07 / {'control': 'random_frozen_ridge', 'label_budget_trials': 15} | m²/s² | 0.040061 | [0.035872, 0.044092] | 0.001736 | [0.000021, 0.003487] | [0.039171, 0.040637] |
| representation_07 / {'control': 'random_frozen_ridge', 'label_budget_trials': 75} | m²/s² | 0.036135 | [0.032617, 0.039686] | -0.002190 | [-0.003519, -0.000748] | [0.035789, 0.036563] |
| representation_07 / {'control': 'supervised_only', 'label_budget_trials': 5} | m²/s² | 0.043612 | [0.039096, 0.048133] | 0.005287 | [0.002672, 0.008041] | [0.042461, 0.044300] |
| representation_07 / {'control': 'supervised_only', 'label_budget_trials': 15} | m²/s² | 0.040997 | [0.036610, 0.045531] | 0.002673 | [0.001809, 0.003554] | [0.040840, 0.041167] |
| representation_07 / {'control': 'supervised_only', 'label_budget_trials': 75} | m²/s² | 0.040333 | [0.036060, 0.044790] | 0.002008 | [0.001220, 0.002837] | [0.040097, 0.040625] |
| longitudinal_08 / condition_anchor_alignment_50 | flexion² | 0.027087 | [0.024128, 0.029907] | 0.000121 | [-0.000694, 0.000835] | [0.027087, 0.027087] |
| longitudinal_08 / condition_anchor_alignment_75 | flexion² | 0.027047 | [0.024094, 0.029850] | 0.000081 | [-0.000714, 0.000770] | [0.027047, 0.027047] |
| longitudinal_08 / direct_recalibration_1 | flexion² | 0.028788 | [0.025747, 0.031944] | 0.001822 | [0.000810, 0.002846] | [0.028788, 0.028788] |
| longitudinal_08 / direct_recalibration_15 | flexion² | 0.037069 | [0.033605, 0.040487] | 0.010103 | [0.007973, 0.012173] | [0.037069, 0.037069] |
| longitudinal_08 / direct_recalibration_5 | flexion² | 0.044923 | [0.040824, 0.048659] | 0.017957 | [0.014987, 0.020484] | [0.044923, 0.044923] |
| longitudinal_08 / direct_recalibration_50 | flexion² | 0.029907 | [0.027030, 0.032189] | 0.002941 | [0.001419, 0.004214] | [0.029907, 0.029907] |
| longitudinal_08 / direct_recalibration_75 | flexion² | 0.027764 | [0.025067, 0.030061] | 0.000797 | [-0.000306, 0.001715] | [0.027764, 0.027764] |
| longitudinal_08 / frozen_source | flexion² | 0.026966 | [0.024473, 0.029374] | 0.000000 | [0.000000, 0.000000] | [0.026966, 0.026966] |
| longitudinal_08 / source_mean | flexion² | 0.027084 | [0.024123, 0.029904] | 0.000118 | [-0.000696, 0.000830] | [0.027084, 0.027084] |
| longitudinal_08 / source_plus_residual_1 | flexion² | 0.028187 | [0.025599, 0.030866] | 0.001221 | [0.000423, 0.001947] | [0.028187, 0.028187] |
| longitudinal_08 / source_plus_residual_15 | flexion² | 0.037017 | [0.033694, 0.040147] | 0.010051 | [0.008075, 0.012027] | [0.037017, 0.037017] |
| longitudinal_08 / source_plus_residual_5 | flexion² | 0.043963 | [0.040161, 0.047332] | 0.016997 | [0.014227, 0.019400] | [0.043963, 0.043963] |
| longitudinal_08 / source_plus_residual_50 | flexion² | 0.030215 | [0.027351, 0.032466] | 0.003249 | [0.001696, 0.004541] | [0.030215, 0.030215] |
| longitudinal_08 / source_plus_residual_75 | flexion² | 0.027909 | [0.025233, 0.030152] | 0.000943 | [-0.000167, 0.001870] | [0.027909, 0.027909] |
| longitudinal_08 / unlabeled_marginal_normalization | flexion² | 0.026383 | [0.023758, 0.028773] | -0.000583 | [-0.001455, 0.000099] | [0.026383, 0.026383] |
| representation_09 / {'setting': 'compute_budget', 'control': 'pretrained_finetuned', 'target_label_budget': 5} | flexion² | 0.034733 | [0.031388, 0.038076] | -0.000006 | [-0.000011, -0.000003] | [0.034470, 0.034928] |
| representation_09 / {'setting': 'compute_budget', 'control': 'pretrained_finetuned', 'target_label_budget': 15} | flexion² | 0.024477 | [0.022124, 0.026908] | -0.000019 | [-0.000025, -0.000014] | [0.024396, 0.024634] |
| representation_09 / {'setting': 'compute_budget', 'control': 'pretrained_finetuned', 'target_label_budget': 75} | flexion² | 0.022064 | [0.019838, 0.024362] | -0.000021 | [-0.000026, -0.000016] | [0.021922, 0.022262] |
| representation_09 / {'setting': 'compute_budget', 'control': 'pretrained_frozen_ridge', 'target_label_budget': 5} | flexion² | 0.039401 | [0.036174, 0.042603] | 0.000016 | [-0.000003, 0.000036] | [0.038236, 0.040786] |
| representation_09 / {'setting': 'compute_budget', 'control': 'pretrained_frozen_ridge', 'target_label_budget': 15} | flexion² | 0.029706 | [0.027380, 0.032029] | -0.000020 | [-0.000034, -0.000007] | [0.029516, 0.030024] |
| representation_09 / {'setting': 'compute_budget', 'control': 'pretrained_frozen_ridge', 'target_label_budget': 75} | flexion² | 0.021276 | [0.019193, 0.023510] | -0.000003 | [-0.000009, 0.000002] | [0.021164, 0.021405] |
| representation_09 / {'setting': 'compute_budget', 'control': 'pretrained_zero_shot', 'target_label_budget': 0} | flexion² | 0.021188 | [0.019076, 0.023448] | 0.000008 | [0.000002, 0.000013] | [0.020929, 0.021328] |
| representation_09 / {'setting': 'compute_budget', 'control': 'random_frozen_ridge', 'target_label_budget': 5} | flexion² | 0.039385 | [0.036152, 0.042566] | — | — | [0.038240, 0.040707] |
| representation_09 / {'setting': 'compute_budget', 'control': 'random_frozen_ridge', 'target_label_budget': 15} | flexion² | 0.029727 | [0.027402, 0.032048] | — | — | [0.029476, 0.030111] |
| representation_09 / {'setting': 'compute_budget', 'control': 'random_frozen_ridge', 'target_label_budget': 75} | flexion² | 0.021279 | [0.019198, 0.023516] | — | — | [0.021187, 0.021398] |
| representation_09 / {'setting': 'compute_budget', 'control': 'random_supervised_only', 'target_label_budget': 5} | flexion² | 0.034740 | [0.031394, 0.038082] | — | — | [0.034443, 0.035010] |
| representation_09 / {'setting': 'compute_budget', 'control': 'random_supervised_only', 'target_label_budget': 15} | flexion² | 0.024497 | [0.022143, 0.026928] | — | — | [0.024392, 0.024620] |
| representation_09 / {'setting': 'compute_budget', 'control': 'random_supervised_only', 'target_label_budget': 75} | flexion² | 0.022085 | [0.019861, 0.024382] | — | — | [0.021984, 0.022273] |
| representation_09 / {'setting': 'compute_budget', 'control': 'random_zero_shot', 'target_label_budget': 0} | flexion² | 0.021180 | [0.019065, 0.023445] | — | — | [0.020923, 0.021323] |
| representation_09 / {'setting': 'data_budget', 'control': 'pretrained_finetuned', 'target_label_budget': 5} | flexion² | 0.034717 | [0.031374, 0.038058] | 0.000012 | [0.000002, 0.000021] | [0.034615, 0.034812] |
| representation_09 / {'setting': 'data_budget', 'control': 'pretrained_finetuned', 'target_label_budget': 15} | flexion² | 0.024450 | [0.022091, 0.026881] | -0.000023 | [-0.000037, -0.000006] | [0.024279, 0.024544] |
| representation_09 / {'setting': 'data_budget', 'control': 'pretrained_finetuned', 'target_label_budget': 75} | flexion² | 0.022046 | [0.019819, 0.024351] | -0.000036 | [-0.000046, -0.000025] | [0.021844, 0.022278] |
| representation_09 / {'setting': 'data_budget', 'control': 'pretrained_frozen_ridge', 'target_label_budget': 5} | flexion² | 0.039600 | [0.036335, 0.042747] | 0.000085 | [0.000043, 0.000129] | [0.038075, 0.041185] |
| representation_09 / {'setting': 'data_budget', 'control': 'pretrained_frozen_ridge', 'target_label_budget': 15} | flexion² | 0.029672 | [0.027355, 0.032016] | -0.000127 | [-0.000160, -0.000092] | [0.029462, 0.029995] |
| representation_09 / {'setting': 'data_budget', 'control': 'pretrained_frozen_ridge', 'target_label_budget': 75} | flexion² | 0.021283 | [0.019203, 0.023518] | 0.000012 | [-0.000001, 0.000025] | [0.021140, 0.021442] |
| representation_09 / {'setting': 'data_budget', 'control': 'pretrained_zero_shot', 'target_label_budget': 0} | flexion² | 0.021213 | [0.019111, 0.023447] | 0.000019 | [0.000006, 0.000032] | [0.020950, 0.021364] |
| representation_09 / {'setting': 'data_budget', 'control': 'random_frozen_ridge', 'target_label_budget': 5} | flexion² | 0.039515 | [0.036243, 0.042632] | — | — | [0.038089, 0.040961] |
| representation_09 / {'setting': 'data_budget', 'control': 'random_frozen_ridge', 'target_label_budget': 15} | flexion² | 0.029799 | [0.027486, 0.032139] | — | — | [0.029517, 0.030239] |
| representation_09 / {'setting': 'data_budget', 'control': 'random_frozen_ridge', 'target_label_budget': 75} | flexion² | 0.021271 | [0.019196, 0.023509] | — | — | [0.021177, 0.021413] |
| representation_09 / {'setting': 'data_budget', 'control': 'random_supervised_only', 'target_label_budget': 5} | flexion² | 0.034706 | [0.031364, 0.038043] | — | — | [0.034523, 0.034992] |
| representation_09 / {'setting': 'data_budget', 'control': 'random_supervised_only', 'target_label_budget': 15} | flexion² | 0.024472 | [0.022115, 0.026901] | — | — | [0.024454, 0.024489] |
| representation_09 / {'setting': 'data_budget', 'control': 'random_supervised_only', 'target_label_budget': 75} | flexion² | 0.022082 | [0.019859, 0.024384] | — | — | [0.021977, 0.022284] |
| representation_09 / {'setting': 'data_budget', 'control': 'random_zero_shot', 'target_label_budget': 0} | flexion² | 0.021194 | [0.019082, 0.023443] | — | — | [0.020920, 0.021355] |
| representation_09 / {'setting': 'model_size', 'control': 'pretrained_finetuned', 'target_label_budget': 5} | flexion² | 0.035334 | [0.032091, 0.038690] | -0.000002 | [-0.000012, 0.000008] | [0.033408, 0.037207] |
| representation_09 / {'setting': 'model_size', 'control': 'pretrained_finetuned', 'target_label_budget': 15} | flexion² | 0.026019 | [0.023631, 0.028392] | -0.000077 | [-0.000090, -0.000064] | [0.024604, 0.027323] |
| representation_09 / {'setting': 'model_size', 'control': 'pretrained_finetuned', 'target_label_budget': 75} | flexion² | 0.023426 | [0.021183, 0.025782] | -0.000089 | [-0.000098, -0.000078] | [0.023125, 0.023752] |
| representation_09 / {'setting': 'model_size', 'control': 'pretrained_frozen_ridge', 'target_label_budget': 5} | flexion² | 0.035679 | [0.032566, 0.038789] | -0.000102 | [-0.000127, -0.000076] | [0.033996, 0.037352] |
| representation_09 / {'setting': 'model_size', 'control': 'pretrained_frozen_ridge', 'target_label_budget': 15} | flexion² | 0.027296 | [0.024940, 0.029674] | -0.000030 | [-0.000051, -0.000006] | [0.025607, 0.028492] |
| representation_09 / {'setting': 'model_size', 'control': 'pretrained_frozen_ridge', 'target_label_budget': 75} | flexion² | 0.021498 | [0.019318, 0.023845] | -0.000011 | [-0.000020, -0.000002] | [0.021388, 0.021671] |
| representation_09 / {'setting': 'model_size', 'control': 'pretrained_zero_shot', 'target_label_budget': 0} | flexion² | 0.021424 | [0.019209, 0.023864] | 0.000007 | [-0.000002, 0.000016] | [0.021024, 0.021896] |
| representation_09 / {'setting': 'model_size', 'control': 'random_frozen_ridge', 'target_label_budget': 5} | flexion² | 0.035781 | [0.032681, 0.038881] | — | — | [0.034141, 0.037467] |
| representation_09 / {'setting': 'model_size', 'control': 'random_frozen_ridge', 'target_label_budget': 15} | flexion² | 0.027326 | [0.024983, 0.029687] | — | — | [0.025553, 0.028427] |
| representation_09 / {'setting': 'model_size', 'control': 'random_frozen_ridge', 'target_label_budget': 75} | flexion² | 0.021509 | [0.019327, 0.023851] | — | — | [0.021384, 0.021708] |
| representation_09 / {'setting': 'model_size', 'control': 'random_supervised_only', 'target_label_budget': 5} | flexion² | 0.035336 | [0.032104, 0.038692] | — | — | [0.033280, 0.037203] |
| representation_09 / {'setting': 'model_size', 'control': 'random_supervised_only', 'target_label_budget': 15} | flexion² | 0.026096 | [0.023704, 0.028472] | — | — | [0.024644, 0.027359] |
| representation_09 / {'setting': 'model_size', 'control': 'random_supervised_only', 'target_label_budget': 75} | flexion² | 0.023515 | [0.021266, 0.025868] | — | — | [0.023219, 0.023808] |
| representation_09 / {'setting': 'model_size', 'control': 'random_zero_shot', 'target_label_budget': 0} | flexion² | 0.021417 | [0.019195, 0.023864] | — | — | [0.021023, 0.021881] |
| representation_09 / {'setting': 'reference', 'control': 'pretrained_finetuned', 'target_label_budget': 5} | flexion² | 0.034716 | [0.031372, 0.038062] | -0.000023 | [-0.000032, -0.000014] | [0.034509, 0.034836] |
| representation_09 / {'setting': 'reference', 'control': 'pretrained_finetuned', 'target_label_budget': 15} | flexion² | 0.024449 | [0.022094, 0.026882] | -0.000047 | [-0.000062, -0.000032] | [0.024285, 0.024660] |
| representation_09 / {'setting': 'reference', 'control': 'pretrained_finetuned', 'target_label_budget': 75} | flexion² | 0.022034 | [0.019809, 0.024337] | -0.000051 | [-0.000063, -0.000040] | [0.021837, 0.022245] |
| representation_09 / {'setting': 'reference', 'control': 'pretrained_frozen_ridge', 'target_label_budget': 5} | flexion² | 0.039425 | [0.036191, 0.042622] | 0.000040 | [-0.000005, 0.000087] | [0.038230, 0.040859] |
| representation_09 / {'setting': 'reference', 'control': 'pretrained_frozen_ridge', 'target_label_budget': 15} | flexion² | 0.029655 | [0.027322, 0.031985] | -0.000071 | [-0.000102, -0.000040] | [0.029529, 0.029890] |
| representation_09 / {'setting': 'reference', 'control': 'pretrained_frozen_ridge', 'target_label_budget': 75} | flexion² | 0.021274 | [0.019189, 0.023505] | -0.000005 | [-0.000019, 0.000008] | [0.021135, 0.021415] |
| representation_09 / {'setting': 'reference', 'control': 'pretrained_zero_shot', 'target_label_budget': 0} | flexion² | 0.021197 | [0.019087, 0.023451] | 0.000017 | [0.000002, 0.000029] | [0.020941, 0.021333] |
| representation_09 / {'setting': 'reference', 'control': 'random_frozen_ridge', 'target_label_budget': 5} | flexion² | 0.039385 | [0.036152, 0.042566] | — | — | [0.038240, 0.040707] |
| representation_09 / {'setting': 'reference', 'control': 'random_frozen_ridge', 'target_label_budget': 15} | flexion² | 0.029727 | [0.027402, 0.032048] | — | — | [0.029476, 0.030111] |
| representation_09 / {'setting': 'reference', 'control': 'random_frozen_ridge', 'target_label_budget': 75} | flexion² | 0.021279 | [0.019198, 0.023516] | — | — | [0.021187, 0.021398] |
| representation_09 / {'setting': 'reference', 'control': 'random_supervised_only', 'target_label_budget': 5} | flexion² | 0.034740 | [0.031394, 0.038082] | — | — | [0.034443, 0.035010] |
| representation_09 / {'setting': 'reference', 'control': 'random_supervised_only', 'target_label_budget': 15} | flexion² | 0.024497 | [0.022143, 0.026928] | — | — | [0.024392, 0.024620] |
| representation_09 / {'setting': 'reference', 'control': 'random_supervised_only', 'target_label_budget': 75} | flexion² | 0.022085 | [0.019861, 0.024382] | — | — | [0.021984, 0.022273] |
| representation_09 / {'setting': 'reference', 'control': 'random_zero_shot', 'target_label_budget': 0} | flexion² | 0.021180 | [0.019065, 0.023445] | — | — | [0.020923, 0.021323] |

Paired references: MC_Maze training mean; LINK08 frozen source; LINK09 matched setting/budget random control for each pretrained method.

Input report hashes and complete trial identities are recorded in `evaluation_11.json`.
Reproduce: `python -m cerebro.evaluation`.
