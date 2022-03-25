# Missing Data

This folder includes code used for the estimates in the "Missing Data" section of the "Missing Data, Speculative Reading" article.

*NOTE: most of the jupyter notebook files were originally created and run on Google Colab. Several of these notebooks are too large for GitHub's preview; it may render output blocks as empty when they are not.*

## Contents

- [Sco_prophet_missingdata_weekly.ipynb](Sco_prophet_missingdata_weekly.ipynb) — calculates logbook gaps; uses Prophet to generate estimates for missing membership events, missing members
- [ScoBorrowingCapacity_v1_1data.ipynb](ScoBorrowingCapacity_v1_1data.ipynb) — borrowing capacity analysis; used as basis for estimating missing borrowing activity
- [Sco_missing_borrowing_activity.ipynb](Sco_missing_borrowing_activity.ipynb) — estimate minimum missing borrowing activity based on subscriptions
- [Sco_missing_books.ipynb](Sco_missing_books.ipynb) — estimate missing books using Copia
- [Sco_bookcatalog_books_estimate.ipynb](Sco_bookcatalog_books_estimate.ipynb) — analyze books from catalog of acquisitions 1933—1940 and estimate missing books