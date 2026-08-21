# Model Risk Assessment

## Executive Conclusion

The AI regulatory-change component is suitable for controlled further development, but it is not ready for autonomous compliance decision-making. Testing across 12 predefined scenarios shows strong performance on explicit threshold, timing, retention, and reporting changes, while weaker performance appears in nuanced interpretation, cross-domain control mapping, impact assessment, and human-review escalation.

## Testing Results

The framework evaluates whether the AI correctly classifies additions, modifications, removals, and no-change cases; maps each change to the appropriate control; assigns an impact level; and identifies when human review is needed. The dashboard reports overall accuracy, false-positive rate, missed-change rate, control-mapping accuracy, and human-review accuracy.

Three scenarios demonstrate material model risk. In T07, the AI recognized a privacy-related vendor-sharing change but mapped it only to Third-Party Risk Management, rated the impact too low, and failed to require human review. This could lead to incomplete privacy, contract, and data-governance remediation.

In T08, a clarification with no substantive obligation change was incorrectly treated as a regulatory modification. This false positive could create unnecessary policy updates and retraining. Repeated false positives may also cause alert fatigue and reduce trust in the monitoring process.

In T12, the AI recognized removal of a sanctions escalation exception but mapped the change to general AML Transaction Monitoring rather than Sanctions Screening / Escalation and assigned a lower impact level. A control-mapping error in sanctions could delay changes to escalation procedures, service levels, and quality assurance, creating significant compliance and reputational risk.

## Key Risks

The main risks are interpretation error, incorrect control mapping, false positives, insufficient escalation, and overreliance on fluent AI explanations. Source-document quality, prompt changes, and model-version changes may also alter performance over time.

## Recommended Controls

High-impact changes, ambiguous language, sanctions, privacy, consumer protection, capital, and model-risk cases should require human review. The organization should maintain versioned prompts, model versions, test datasets, source citations, reviewer decisions, and audit logs. Regression testing should be repeated after material model or prompt changes.

The test library should be expanded with real, independently reviewed regulatory examples. Acceptance thresholds should be formally defined, with especially low tolerance for missed material changes and incorrect control mapping.

## Recommendation

The AI is ready for controlled further development, but not for autonomous production use. Further development should continue with mandatory human-in-the-loop review, stronger control mapping, regression testing, auditability, and a larger validated test set before production readiness is reconsidered.
