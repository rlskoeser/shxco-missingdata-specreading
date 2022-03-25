# Speculative Reading

This folder includes code used for the member analysis and recommendations in the "Speculative Reading" section of the "Missing Data, Speculative Reading" article.

*NOTE: most of the jupyter notebook files were originally created and run on Google Colab. Several of these notebooks are too large for GitHub's preview; it may render output blocks as empty when they are not.*

## Contents

- [SCo_lenskit_eval.ipynb](SCo_lenskit_eval.ipynb) — LensKit evaluation of various algorithms on S&co borrowing data
- [identify_partial_borrowers.py](identify_partial_borrowers.py) — script to identify "partial borrowers" (members with incomplete borrowing histories), and the subscription periods with no documented borrowing (resulting data files are in the data directory of this repository)
- [Sco_partialborrowers_info.ipynb] — analyze the known borrowing behavior of partial borrowers, including Hemingway, and generate raincloud plots
- [lenskit_model_scores_stability.ipynb](lenskit_model_scores_stability.ipynb)
- [Interpret_Output_Results.ipynb](Interpret_Output_Results.ipynb)