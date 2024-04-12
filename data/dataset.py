import os.path
import pandas as pd
from typing import Tuple

# Specify the path to the data directory
DATA_DIR = os.path.dirname(__file__)
SOURCE_DATA_DIR = os.path.join(DATA_DIR, "source-data")

def get_csv_path(filename: str) -> str:
    """
    Return the path to a CSV file in the source-data directory.

    Parameters:
    filename (str): The name of the CSV file.

    Returns:
    str: The path to the CSV file.
    """
    return os.path.join(SOURCE_DATA_DIR, filename)

def get_short_id(uri: str) -> str:
    """
    Extract the short id from a URI.

    Parameters:
    uri (str): The URI from which to extract the id.

    Returns:
    str: The extracted id.
    """
    return uri.split("/")[-2] if pd.notna(uri) else None

def load_csv_as_df(csv_url: str) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame and add an 'id' column.

    Parameters:
    csv_url (str): The URL of the CSV file to load.

    Returns:
    pd.DataFrame: The loaded DataFrame.
    """
    df = pd.read_csv(csv_url)
    df["id"] = df.uri.apply(get_short_id)
    return df

csv_urls_v1_1 = {
    "members": get_csv_path("SCoData_members_v1.1_2021-01.csv"),
    "books": get_csv_path("SCoData_books_v1.1_2021-01.csv"),
    "events": get_csv_path("SCoData_events_v1.1_2021-01.csv"),
}

csv_urls = {
    "members": get_csv_path("SCoData_members_v1.2_2022-01.csv"),
    "books": get_csv_path("SCoData_books_v1.2_2022-01.csv"),
    "events": get_csv_path("SCoData_events_v1.2_2022-01.csv"),
}

def get_shxco_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load the members, books, and events data into pandas DataFrames.

    Returns:
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: The loaded DataFrames.
    """
    members_df = load_csv_as_df(csv_urls["members"])
    books_df = load_csv_as_df(csv_urls["books"])
    events_df = load_csv_as_df(csv_urls["events"])

    members_df["member_id"] = members_df.id
    books_df["book_id"] = books_df.id

    events_df[["first_member_uri", "second_member_uri"]] = events_df.member_uris.str.split(";", expand=True)
    events_df = events_df[events_df.second_member_uri.isna()]
    events_df["member_id"] = events_df.first_member_uri.apply(get_short_id)

    return (members_df, books_df, events_df)