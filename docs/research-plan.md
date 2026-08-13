# Master's Capstone Research Plan

## Working title

**An Explainable Deep Learning-Based Decision-Support System for Wound Image Classification: Comparative Evaluation of Convolutional Neural Network Architectures**

## Main research problem

Determine whether selected deep-learning architectures can classify predefined wound-image categories with useful and reproducible performance, while providing calibrated uncertainty and interpretable visual evidence.

## Candidate research questions

1. How do EfficientNet-B0, ResNet and MobileNet compare on the same held-out wound-image test set?
2. Which model provides the strongest macro F1 while maintaining practical inference latency?
3. How well calibrated are model confidence estimates?
4. Can an abstention/uncertainty threshold reduce high-confidence classification errors?
5. Do Grad-CAM visualizations correspond to clinically/research-relevant image regions according to expert review?

## Dependent variables

- accuracy;
- macro precision;
- macro recall;
- macro F1;
- per-class precision/recall/F1;
- confusion matrix;
- inference latency;
- calibration error, if included;
- abstention coverage/risk, if included.

## Experimental safeguards

- Keep a held-out test set untouched until final evaluation.
- Prefer patient-level or source-grouped splits when multiple images may come from the same patient/source.
- Record random seeds.
- Record model/configuration versions.
- Avoid choosing the winning model based on test-set performance repeatedly.
- Report class counts and imbalance.
- Do not fabricate or hand-edit model metrics.

## Dataset governance

Before collecting images, document:
- source;
- usage/license rights;
- consent status;
- de-identification procedure;
- inclusion/exclusion criteria;
- labeling protocol;
- expert qualification;
- disagreement resolution;
- image quality rules;
- retention/deletion policy.

## Minimum software demonstration

- authentication;
- image upload;
- AI inference;
- top-class and probability distribution;
- uncertainty/abstention handling;
- prediction history;
- model version tracking;
- expert review record;
- research model comparison dashboard.

## Future work

- object detection;
- segmentation;
- calibrated wound measurements with scale reference;
- longitudinal healing analysis;
- mobile acquisition quality guidance;
- prospective validation.
