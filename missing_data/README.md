# Missing Data

This folder includes code used for the estimates in the "Missing Data" section of the "Missing Data, Speculative Reading" article.

*NOTE: most of the Jupyter notebook files were originally created and run on Google Colab. Several of these notebooks are too large for GitHub's preview; it may render output blocks as empty when they are not.*

## Contents

### Notebooks to Reproduce Our Analysis

- [ScoMissingMembershipActivities.ipynb](ScoMissingMembershipActivities.ipynb) This notebook includes estimates missing membership activities and code to generate figures 1-3 for our paper.
- [ScoMissingMembers.ipyb](ScoMissingMembers.ipynb) This notebook includes estimates missing members and code to generate figures 4-6 for our paper.
- [Sco_missing_borrowing_activity.ipynb](Sco_missing_borrowing_activity.ipynb) This notebook estimates minimum missing borrowing activity based on subscriptions and contains code to generate figure 8 for our paper.

### Archived Notebooks

- [Sco_prophet_missingdata_weekly.ipynb](Sco_prophet_missingdata_weekly.ipynb) — calculates logbook gaps; uses Prophet to generate estimates for missing membership events, missing members
- [ScoBorrowingCapacity_v1_1data.ipynb](ScoBorrowingCapacity_v1_1data.ipynb) — borrowing capacity analysis; used as basis for estimating missing borrowing activity
- [Sco_missing_books.ipynb](Sco_missing_books.ipynb) — estimate missing books using Copia
- [Sco_bookcatalog_books_estimate.ipynb](Sco_bookcatalog_books_estimate.ipynb) — analyze books from catalog of acquisitions 1933—1940 and estimate missing books
