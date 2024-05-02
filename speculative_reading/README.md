# Speculative Reading

This folder includes code used for the member analysis and recommendations in the "Speculative Reading" section of the "Missing Data, Speculative Reading" article.

*NOTE: most of the jupyter notebook files were originally created and run on Google Colab. Several of these notebooks are too large for GitHub's preview; it may render output blocks as empty when they are not.*

## Contents

- [load_datasets.py](load_datasets.py) — script to load the S&co borrowing data and other datasets used in the analysis, with some additional functions for data processing
- [LenskitRecommendations.ipynb](LenskitRecommendations.ipynb) — LensKit evaluation of various algorithms on S&co borrowing data
- [identify_partial_borrowers.py](identify_partial_borrowers.py) — script to identify "partial borrowers" (members with incomplete borrowing histories), and the subscription periods with no documented borrowing (resulting data files are in the data directory of this repository)
- [PartialBorrowers.ipynb](PartialBorrowers.ipynb) — analyze the known borrowing behavior of partial borrowers, including Hemingway
- [HemingwayBorrowing.ipynb](HemingwayBorrowing.ipynb) — analyze Hemingway's borrowing behavior and generate raincloud plots
- [CollaborativeFilteringRecommendations.ipynb](CollaborativeFilteringRecommendations.ipynb) — generate collaborative filtering recommendations for partial borrowers
- [CombinedRecommendations.ipynb](CombinedRecommendations.ipynb) — combine collaborative filtering recommendations with lenskit and other recommendations for partial borrowers. Generates figures 13 and 14 in the article.


## Archived Notebooks

- [final_borrowers_table.R](archived_notebooks/final_borrowers_table.R) - Original code to generate figure 13 that is now partially implemented in CombinedRecommendations.ipynb using the recently ported `great-tables` library. Some of the functionality is not quite finished in this new library, so results are not identical to the original figure using the notebook, though you can use this R script to generate the exact table.
- [SCo_lenskit_eval.ipynb](archived_notebooks/SCo_lenskit_eval.ipynb) - Original code to generate the LensKit evaluation that is now implemented in LensKitRecommendations.ipynb. This notebook is not fully functional as it was originally run on Google Colab and the data files are not included in this repository. The LensKitRecommendations.ipynb notebook is the updated version of this notebook that can be run locally with the data files included in this repository.

Additional related work that did not make it into the article can be found in [Appendix: Speculative Reading](../appendix/speculative_reading/)