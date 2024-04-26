import pandas as pd

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
