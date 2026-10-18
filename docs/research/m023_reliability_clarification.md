# Pre-execution reliability metric clarification

This clarification is committed before Workstream A execution. It changes no data partition, model, threshold or temporal-dynamics criterion from protocol `a2861a2`.

The primary relative improvement is `1 - equal_date_mean(model_risk_MSE) / equal_date_mean(control_risk_MSE)`. Each held-out date contributes the mean over its20 uniform allocations; every date has equal weight. This is a ratio of aggregate equal-date errors, not the average of three date-wise percentage reductions. All per-date values are separately reported and must individually improve for promotion.

The two-class balanced-accuracy gate uses pooled allocations with equal date weight because every date has20 primary allocations. Single-class fold balanced accuracy remains undefined; if the pooled outcomes contain only one class, promotion fails. The command-free allocation procedure still receives B selected command labels only when computing the coverage diagnostic, as recorded in the original information-access table.
