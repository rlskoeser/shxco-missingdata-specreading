# Data for Speculative Reading Analysis

This folder contains data files used in the analysis of the "Speculative Reading" section of the "Missing Data, Speculative Reading" article. 

## Contents

### Lenskit Results

This folder holds csv files containing the results of the Lenskit analysis. The files are named with the following experiment names:

- `with_periodicals` or `without_periodicals` to indicate whether the model includes periodicals.
- `comparison_model_runs` are the results of the comparison model runs to validate the lenskit model.
- `sampled` indicates selecting the top recommendations from the model.
- `full` indicates selecting all recommendations from the model.
- `aggregated` are combined results from all runs of the model.
- `popularity` are the top popularity results.

### Collaborative Filtering Results

This folder holds csv files containing the results of the collaborative filtering analysis. The files are named with the following experiment names:

- `with_periodicals` or `without_periodicals` to indicate whether the model includes periodicals.
- `full` indicates selecting all recommendations from the model.
- `top200` indicates selecting the top 200 recommendations from the model.
- `aggregate` are combined results from all runs of the model.
- `circulation limited` are the results when we limit to the circulation window.