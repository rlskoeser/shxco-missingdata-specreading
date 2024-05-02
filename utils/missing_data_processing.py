# Standard library imports
from datetime import timedelta, datetime, date
import warnings
from typing import Tuple, List, Dict, Union
from pathlib import Path

# Related third party imports
import altair as alt
import pandas as pd
from pandas.api.types import CategoricalDtype
import requests

# Disable max rows for altair
alt.data_transformers.disable_max_rows()

# Ignore warnings
warnings.filterwarnings("ignore")

# determine path to data dir relative to this file
DATA_DIR = (Path(__file__).parent.parent / "data").resolve()
SOURCE_DATA_DIR = (DATA_DIR / "source_data").resolve()

# NOTE: relative paths won't work in colab unless
# we make this code installable; can we detect and use github url?
# https://raw.githubusercontent.com/rlskoeser/shxco-missingdata-specreading/main/data/


# Ppaths to the CSV files. The 'members', 'books', and 'events' data
# are the official published versions and are available locally.
# The 'borrow_overrides' data is project-specific and is also available locally.

CSV_PATHS = {
    "members": SOURCE_DATA_DIR / "SCoData_members_v1.2_2022-01.csv",
    "books": SOURCE_DATA_DIR / "SCoData_books_v1.2_2022-01.csv",
    "events": SOURCE_DATA_DIR / "SCoData_events_v1.2_2022-01.csv",
    "borrow_overrides": DATA_DIR / "long_borrow_overrides.csv",
}


def load_initial_data() -> (
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]
):
    """
    Load datasets from CSV files.

    This function loads the data from the CSV files stored in the
    'SOURCE_DATA_DIR' and 'DATA_DIR' directories. The data includes
    information about members, books, and events. The 'events' data is
    returned as a pandas DataFrame.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]: A tuple containing the 'events', 'members', 'books', and 'borrow_overrides' DataFrames.
    """
    # Load the data from the corresponding CSV file.
    # The 'low_memory' parameter is set to False to prevent low memory warnings.
    events_df = pd.read_csv(CSV_PATHS["events"], low_memory=False)
    members_df = pd.read_csv(CSV_PATHS["members"], low_memory=False)
    books_df = pd.read_csv(CSV_PATHS["books"], low_memory=False)
    borrow_overrides_df = pd.read_csv(CSV_PATHS["borrow_overrides"], low_memory=False)

    # Return the data
    return events_df, members_df, books_df, borrow_overrides_df


def get_preprocessed_data(*datasets) -> Dict[str, pd.DataFrame]:
    """
    Load datasets from CSV files as pandas DataFrame and apply common
    preprocessing.

    Takes an optional list of datasets to load, which should be
    any of 'events', 'members', 'books', and 'borrow_overrides'.
    If not specified, all datasets are loaded.

    'SOURCE_DATA_DIR' and 'DATA_DIR' directories. The data includes
    information about members, books, and events. The 'events' data is
    returned as a pandas DataFrame.

    Returns:
        Dict[String, pd.DataFrame]: A dictionary with the requested DataFrames
    """
    if not len(datasets):
        datasets = CSV_PATHS.keys()
    else:
        # check for any unknown dataset names
        unknowns = [d for d in datasets if d not in CSV_PATHS]
        if len(unknowns):
            raise ValueError(
                f"Unknown dataset: {', '.join([str(u) for u in unknowns])}"
            )

    data = {}
    for dataset in datasets:
        data[dataset] = pd.read_csv(CSV_PATHS[dataset], low_memory=False)

    # preprocess any of these that are present
    if "events" in datasets:
        data["events"] = preprocess_events_data(data["events"])
    if "books" in datasets:
        data["books"] = preprocess_books_data(data["books"])

    return data


def short_id(uri):
    """Generate short IDs for members and items based on S&co URI.
    The short ID is the last non-slash part of the URI."""
    return uri.rstrip("/").split("/")[-1] if pd.notna(uri) else None


def preprocess_events_data(events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pre-processing for events data.

    This function processes the 'events' data by splitting multiple members
    for shared accounts and generating short IDs equivalent to those in
    the 'member' and 'book' DataFrames.

    Args:
        events_df (pd.DataFrame): The initial 'events' DataFrame.

    Returns:
        pd.DataFrame: The processed 'events' DataFrame.
    """
    # Split the 'member_uris' column into 'first_member_uri' and
    # 'second_member_uri' columns. This is done to handle shared
    # accounts where multiple members are associated with a single account.
    events_df[
        ["first_member_uri", "second_member_uri"]
    ] = events_df.member_uris.str.split(";", expand=True)

    # Generate short IDs for members and items.
    events_df["member_id"] = events_df.first_member_uri.apply(short_id)
    events_df["item_id"] = events_df.item_uri.apply(short_id)

    # Return the processed 'events' DataFrame.
    return events_df


def preprocess_books_data(books_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pre-processing for book data.

    This function processes the 'books' data by generating short-form IDs
    from the longer project URIs.

    Args:
        books_df (pd.DataFrame): The initial 'books' DataFrame.

    Returns:
        pd.DataFrame: The processed 'books' DataFrame.
    """
    # Generate short IDs from item URIs
    books_df["id"] = books_df.uri.apply(short_id)

    # Return the processed 'books' DataFrame.
    return books_df


def generate_logbooks_events(events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate logbook events from the events dataframe.

    This function filters the 'events_df' DataFrame to include only logbook events.
    It then selects relevant columns and creates a new column 'logbook_date' that contains the subscription purchase date if available, otherwise the start date.

    Args:
        events_df (pd.DataFrame): The initial 'events' DataFrame.

    Returns:
        pd.DataFrame: The logbook events DataFrame.
    """
    # Filter the 'events_df' DataFrame to include only logbook events.
    # Select relevant columns for further processing.
    logbook_events_df = events_df[events_df.source_type.str.contains("Logbook")][
        [
            "event_type",
            "start_date",
            "end_date",
            "subscription_purchase_date",
            "member_uris",
            "member_names",
            "subscription_duration",
            "subscription_duration_days",
            "subscription_volumes",
            "subscription_category",
            "source_type",
        ]
    ]

    # Convert the 'start_date' and 'subscription_purchase_date' columns to datetime format.
    logbook_events_df["start_date"] = pd.to_datetime(logbook_events_df["start_date"])
    logbook_events_df["subscription_purchase_date"] = pd.to_datetime(
        logbook_events_df["subscription_purchase_date"]
    )

    # Create a new column 'logbook_date' that contains the subscription purchase date if available, otherwise the start date.
    logbook_events_df["logbook_date"] = logbook_events_df.apply(
        lambda row: row.subscription_purchase_date
        if pd.notna(row.subscription_purchase_date)
        else row.start_date,
        axis=1,
    )

    # Return the logbook events DataFrame.
    return logbook_events_df


def earliest_date(row: pd.Series) -> date:
    """
    Get the earliest date from the row.

    This function takes a row of data and returns the earliest date among the 'start_date', 'subscription_purchase_date', and 'end_date' columns. If these columns contain NaN values, they are ignored. If all these columns are NaN, the function returns None.

    Args:
        row (pd.Series): A row of data. Expected to have 'start_date', 'subscription_purchase_date',
        and 'end_date' columns.

    Returns:
        datetime.date: The earliest date among the 'start_date', 'subscription_purchase_date',
        and 'end_date' columns. Returns None if all these columns are NaN.
    """
    # Create a list of dates from the 'start_date', 'subscription_purchase_date', and 'end_date' columns. Ignore NaN values.
    dates = [
        val
        for val in [row.start_date, row.subscription_purchase_date, row.end_date]
        if not pd.isna(val)
    ]

    # If the list of dates is not empty, return the earliest date. Otherwise, return None.
    if dates:
        return min(dates)


def generate_membership_events(events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate membership events from the events dataframe.

    This function filters the 'events_df' DataFrame to include only membership events,
    which are defined as events of type 'Renewal', 'Subscription', 'Reimbursement', 'Supplement', or 'Separate Payment'.
    It then creates a new column 'earliest_date' that contains the earliest date among the 'start_date',
    'subscription_purchase_date', and 'end_date' columns for each event.
    Finally, it creates a new column 'date' that contains the 'earliest_date' values converted to datetime format.

    Args:
        events_df (pd.DataFrame): The initial 'events' DataFrame.

    Returns:
        pd.DataFrame: The membership events DataFrame.
    """
    # Filter the 'events_df' DataFrame to include only membership events.
    membership_events = events_df[
        events_df.event_type.isin(
            [
                "Renewal",
                "Subscription",
                "Reimbursement",
                "Supplement",
                "Separate Payment",
            ]
        )
    ]

    # Create a new column 'earliest_date' that contains the earliest date among the 'start_date', 'subscription_purchase_date', and 'end_date' columns for each event.
    membership_events["earliest_date"] = membership_events.apply(earliest_date, axis=1)

    # Create a new column 'date' that contains the 'earliest_date' values converted to datetime format.
    membership_events["date"] = pd.to_datetime(
        membership_events["earliest_date"], errors="coerce"
    )

    # Return the membership events DataFrame.
    return membership_events


def print_gaps(gaps: List[Dict[str, Union[datetime, int]]], gap_type: str):
    """
    Print the identified gaps in the logbooks.

    This function takes a list of gaps and a gap type, and prints each gap. Each gap is a dictionary with 'start', 'end', and 'days' keys representing the start date, end date, and duration of the gap. The gap type is a string that describes the type of gaps ("large" or "small").

    Args:
        gaps (List[Dict[str, Union[datetime, int]]]): The list of gaps. Each gap is a dictionary
        with 'start', 'end', and 'days' keys representing the start date, end date, and duration of the gap.
        gap_type (str): The type of gaps ("large" or "small").
    """
    # Print the number of gaps and the gap type.
    print(f"\nThe {len(gaps)} {gap_type} gaps in the logbooks")

    # Iterate over the gaps.
    for gap in gaps:
        # Print the start date, end date, and duration of the gap.
        print(
            f"\t{gap['start'].strftime('%B %d %Y')} to {gap['end'].strftime('%B %d %Y')} ({gap['days']} days)"
        )


def exclude_gap_events(
    events_df: pd.DataFrame, gaps: List[Dict[str, Union[datetime, int]]]
) -> pd.DataFrame:
    """
    Exclude events occurring during the identified gaps.

    This function takes a DataFrame of events and a list of gaps, and returns a new DataFrame  that excludes any events occurring during the gaps. Each gap is a dictionary with 'start' and 'end' keys representing the start and end dates of the gap.

    Args:
        events_df (pd.DataFrame): The DataFrame of events. Expected to have a 'logbook_date' column.
        gaps (List[Dict[str, Union[datetime, int]]]): The list of gaps. Each gap is a dictionary
        with 'start' and 'end' keys representing the start and end dates of the gap.

    Returns:
        pd.DataFrame: A new DataFrame that excludes any events occurring during the gaps.
    """
    # Create a copy of the events DataFrame to avoid modifying the original DataFrame.
    events_nogaps_df = events_df.copy()

    # Iterate over the gaps.
    for gap in gaps:
        # Get the start and end dates of the gap.
        gap_start = gap["start"]
        gap_end = gap["end"]

        # Exclude events that occur during the gap. This is done by keeping only the events that occur before the start of the gap or after the end of the gap.
        events_nogaps_df = events_nogaps_df[
            ~(
                (events_nogaps_df.logbook_date >= gap_start)
                & (events_nogaps_df.logbook_date <= gap_end)
            )
        ]

    # Return the DataFrame that excludes any events occurring during the gaps.
    return events_nogaps_df


def generate_logbook_gaps(
    logbook_events_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate logbook gaps from the logbook events dataframe.

    This function identifies gaps in the logbook events, defined as periods between logbook dates
    where no events are recorded. Gaps shorter than 15 days are ignored. The function returns two
    dataframes: one for the identified gaps and one for the weekly count of logbook events excluding
    the gaps.

    Args:
        logbook_events_df (pd.DataFrame): The logbook events dataframe.

    Returns:
        pd.DataFrame: The logbook gaps dataframe.
        pd.DataFrame: The logbooks weekly count dataframe.
    """
    # Load the logbook dates from a JSON file and sort them by 'startDate'.
    logbook_dates = pd.read_json(DATA_DIR / "logbook-dates.json").sort_values(
        "startDate"
    )

    # Define the minimum gap duration to consider.
    MIN_GAP_DAYS = 15

    # Initialize lists to store the identified gaps and skipped gaps.
    logbook_gaps = []
    skipped_gaps = []

    # Define a timedelta of one day for date calculations.
    oneday = timedelta(days=1)

    # Iterate over the logbook dates to identify gaps.
    for i in range(len(logbook_dates) - 1):
        # Define the start and end of the gap as the end of the current logbook date and the start of the next one.
        gap_start = pd.to_datetime(logbook_dates.iloc[i]["endDate"]) + oneday
        gap_end = pd.to_datetime(logbook_dates.iloc[i + 1]["startDate"]) - oneday

        # Calculate the duration of the gap in days.
        gap_duration = (gap_end - gap_start).days

        # Store the gap if its duration is greater than the minimum gap duration.
        if gap_duration > MIN_GAP_DAYS:
            logbook_gaps.append(
                {"start": gap_start, "end": gap_end, "days": gap_duration}
            )
        elif gap_duration > 0:  # Ignore 0 and -1 duration "gaps"!
            skipped_gaps.append(
                {"start": gap_start, "end": gap_end, "days": gap_duration}
            )

    # Print the identified gaps and skipped gaps.
    print_gaps(logbook_gaps, "large")
    print_gaps(skipped_gaps, "small")

    # Filter the logbook events to exclude those occurring during the identified gaps.
    logbook_events_nogaps = exclude_gap_events(logbook_events_df, logbook_gaps)

    # Calculate the weekly count of logbook events excluding the gaps.
    logbooks_weekly_count = (
        logbook_events_nogaps.groupby([pd.Grouper(key="logbook_date", freq="W")])[
            "event_type"
        ]
        .count()
        .reset_index()
    )
    logbooks_weekly_count.rename(columns={"event_type": "total"}, inplace=True)

    # Convert the list of gaps to a DataFrame and add a 'gap_label' column.
    logbook_gaps_df = pd.DataFrame(logbook_gaps)
    logbook_gaps_df["gap_label"] = logbook_gaps_df.apply(
        lambda row: "%s to %s (%d days)"
        % (row.start.date().isoformat(), row.end.date().isoformat(), row.days),
        axis=1,
    )

    return logbook_gaps_df, logbooks_weekly_count, logbook_gaps, logbook_events_nogaps


def generate_member_events(
    events_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate member events from the events dataframe.

    This function processes the 'events_df' DataFrame to generate member events and calculate the yearly count of new members. It first processes the events data and identifies the earliest known date for each event. It then filters the events to
    include only those that occurred before 1942 and groups them by member ID to get the first event for each member. Finally, it calculates the yearly count of new members and sorts the member events by date and event type.

    Args:
        events_df (pd.DataFrame): The events dataframe.

    Returns:
        pd.DataFrame: The member events dataframe.
        pd.DataFrame: The new member yearly count dataframe.
    """
    # Process the events data.
    events_df = process_events_data(events_df)

    # Create a copy of the events DataFrame and identify the earliest known date for each event.
    member_dates = events_df.copy()
    member_dates["earliest_date"] = member_dates.apply(earliest_date, axis=1)

    # Convert the 'earliest_date' column to datetime format.
    member_dates["date"] = pd.to_datetime(
        member_dates["earliest_date"], errors="coerce"
    )

    # Filter the events to include only those with known dates and that occurred before 1942.
    members_added = member_dates[
        ["event_type", "member_id", "date", "source_type"]
    ].dropna(subset=["date"])
    members_added = members_added[members_added["date"] < datetime(1942, 1, 1)]

    # Group the events by member ID and get the first event for each member.
    members_grouped = members_added[["member_id", "date"]].groupby("member_id")
    members_first_dates = members_grouped.first().reset_index()

    # Calculate the yearly count of new members.
    newmember_yearly_count = (
        members_first_dates.groupby([pd.Grouper(key="date", freq="Y")])["member_id"]
        .count()
        .reset_index()
    )
    newmember_yearly_count.rename(columns={"member_id": "total"}, inplace=True)

    # Define the order of event types.
    event_type = CategoricalDtype(
        categories=[
            "Subscription",
            "Renewal",
            "Separate Payment",
            "Borrow",
            "Purchase",
            "Supplement",
            "Request",
            "Gift",
            "Crossed out",
            "Reimbursement",
        ],
        ordered=True,
    )

    # Copy the member events DataFrame and convert the 'event_type' column to the defined categorical type.
    member_events = members_added.copy()
    member_events["event_type"] = member_events.event_type.astype(event_type)

    # Sort the member events by date and event type.
    member_events = member_events.sort_values(by=["date", "event_type"])

    return member_events, newmember_yearly_count, members_first_dates


def generate_newmember_subscriptions(member_events, logbook_gaps):
    """
    Generate new member subscriptions from the member events dataframe.

    This function filters the 'member_events' DataFrame to include only logbook events of type 'Subscription' or 'Renewal', and groups them by member ID to get the first event for each member. It then excludes any events occurring during the identified gaps in the logbooks. Finally, it calculates the yearly and weekly counts of new member subscriptions.

    Args:
        member_events (pd.DataFrame): The member events dataframe.
        logbook_gaps (List[Dict[str, Union[datetime, int]]]): The list of logbook gaps.

    Returns:
        pd.DataFrame: The yearly count of new member subscriptions.
        pd.DataFrame: The weekly count of new member subscriptions.
    """
    # Filter the 'member_events' DataFrame to include only logbook events of type 'Subscription' or 'Renewal'.
    # Group by member ID to get the first event for each member.
    subscription_first_events = (
        member_events[
            member_events.source_type.str.contains("Logbook")
            & member_events.event_type.isin(["Subscription", "Renewal"])
        ]
        .groupby("member_id")
        .first()
        .reset_index()
    )

    # Exclude any events occurring during the identified gaps in the logbooks.
    subscription_first_events_nogaps = subscription_first_events.copy()
    for _, gap in enumerate(logbook_gaps):
        gap_start = gap["start"]
        gap_end = gap["end"]
        subscription_first_events_nogaps = subscription_first_events_nogaps[
            ~(
                (subscription_first_events_nogaps.date >= gap_start)
                & (subscription_first_events_nogaps.date <= gap_end)
            )
        ]

    # Calculate the yearly count of new member subscriptions.
    newmember_subscriptions_by_year = (
        subscription_first_events_nogaps.groupby([pd.Grouper(key="date", freq="Y")])[
            "member_id"
        ]
        .count()
        .reset_index()
    )
    newmember_subscriptions_by_year.rename(columns={"member_id": "total"}, inplace=True)

    # Calculate the weekly count of new member subscriptions.
    newmember_subscriptions_by_week = (
        subscription_first_events_nogaps.groupby([pd.Grouper(key="date", freq="W")])[
            "member_id"
        ]
        .count()
        .reset_index()
    )
    newmember_subscriptions_by_week.rename(columns={"member_id": "total"}, inplace=True)

    return newmember_subscriptions_by_year, newmember_subscriptions_by_week
