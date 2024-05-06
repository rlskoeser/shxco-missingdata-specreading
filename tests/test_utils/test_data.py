from unittest.mock import patch
from datetime import datetime

import pandas as pd
import pytest

from utils import missing_data_processing


def test_paths():
    # confirm that data paths resolve
    assert missing_data_processing.DATA_DIR.exists()
    assert missing_data_processing.SOURCE_DATA_DIR.exists()

    for path in missing_data_processing.CSV_PATHS.values():
        assert path.exists()


def test_short_id():
    assert (
        missing_data_processing.short_id(
            "https://shakespeareandco.princeton.edu/members/alajouanine/"
        )
        == "alajouanine"
    )

    assert missing_data_processing.short_id(None) is None


def test_load_initial_data():
    data = missing_data_processing.load_initial_data()
    assert all([isinstance(df, pd.DataFrame) for df in data])
    assert all([not df.empty for df in data])


@patch("utils.missing_data_processing.pd")
@patch("utils.missing_data_processing.preprocess_events_data")
@patch("utils.missing_data_processing.preprocess_shxco_data")
def test_get_preprocessed_data(mock_preprocess_shxco, mock_preprocess_events, mock_pd):
    # no datasets specified: should return all
    data = missing_data_processing.get_preprocessed_data()
    for dataset in missing_data_processing.CSV_PATHS.keys():
        assert dataset in data
    assert mock_pd.read_csv.call_count == 4
    mock_preprocess_events.assert_called()
    mock_preprocess_shxco.assert_called()

    # reset mocks
    for m in [mock_preprocess_shxco, mock_preprocess_events, mock_pd]:
        m.reset_mock()

    # test loading selected datasets
    data = missing_data_processing.get_preprocessed_data("books", "borrow_overrides")
    assert len(data.keys()) == 2
    assert "books" in data
    assert "borrow_overrides" in data
    mock_preprocess_events.assert_not_called()
    mock_preprocess_shxco.assert_called()

    # test unknown dataset
    with pytest.raises(ValueError):
        missing_data_processing.get_preprocessed_data("foo", "bar")


def test_get_logbook_events():
    data = missing_data_processing.get_preprocessed_data("events")
    logbook_df = missing_data_processing.get_logbook_events(data["events"])
    # check new column has been added and is correct time
    assert "logbook_date" in logbook_df.columns
    assert logbook_df.logbook_date.dtype == "datetime64[ns]"
    assert len(logbook_df[logbook_df.logbook_date.isna()]) == 0  # all values set

    # check changed types
    assert logbook_df.start_date.dtype == "datetime64[ns]"
    assert logbook_df.subscription_purchase_date.dtype == "datetime64[ns]"
