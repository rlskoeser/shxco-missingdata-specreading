# Standard library imports
from datetime import timedelta, datetime, date
import warnings
from typing import Tuple

# Related third party imports
import altair as alt
import pandas as pd
from pandas.api.types import CategoricalDtype
import requests

# Disable max rows for altair
alt.data_transformers.disable_max_rows()

# Ignore warnings
warnings.filterwarnings('ignore')

# determine path to data dir relative to this file
DATA_DIR = Path(__file__).parent.parent / "data"
SOURCE_DATA_DIR = DATA_DIR / "source-data"

# NOTE: relative paths won't work in colab unless
# we make this code installable; can we detect and use github url?
# https://raw.githubusercontent.com/rlskoeser/shxco-missingdata-specreading/main/data/


def load_initial_data() -> pd.DataFrame:
    """Load the initial data from the CSV files.
    
    Returns:
        pd.DataFrame: The initial data."""
    # use v1.2 datasets; load from our repo for convenience
    csv_urls = {
        # official published versions available locally
        "members": SOURCE_DATA_DIR / "SCoData_members_v1.2_2022-01.csv",
        "books": SOURCE_DATA_DIR / "SCoData_books_v1.2_2022-01.csv",
        "events": SOURCE_DATA_DIR / "SCoData_events_v1.2_2022-01.csv",
        # project-specific data
        # NOTE: now moved to appendix/speculative_reading; likely only used there
        # "partial_borrowers": DATA_DIR / "partial_borrowers_collapsed.csv",
        "borrow_overrides": DATA_DIR / "long_borrow_overrides.csv",
    }

    # load events
    events_df = pd.read_csv(csv_urls['events'], low_memory=False)
    return events_df

def generate_logbooks_events(events_df: pd.DataFrame) -> pd.DataFrame:
    """Generate logbook events from the events dataframe.
    
    Args:
        events_df (pd.DataFrame): The events dataframe.
        
    Returns:
        pd.DataFrame: The logbook events dataframe."""
    # identify to logbook events

    logbook_events_df = events_df[events_df.source_type.str.contains('Logbook')][[
    'event_type', 'start_date', 'end_date', 'subscription_purchase_date',
    'member_uris', 'member_names',
    'subscription_duration', 'subscription_duration_days',
    'subscription_volumes', 'subscription_category',
    'source_type'
    ]]

    # May need to add format="mixed" depending on platform
    logbook_events_df['start_date'] = pd.to_datetime(logbook_events_df['start_date'])
    logbook_events_df['subscription_purchase_date'] = pd.to_datetime(logbook_events_df['subscription_purchase_date'])
    logbook_events_df['logbook_date'] = logbook_events_df.apply(lambda row: row.subscription_purchase_date if pd.notna(row.subscription_purchase_date) else row.start_date, axis=1)
    return logbook_events_df

def earliest_date(row: pd.Series) -> date:
    """Get the earliest date from the row.

    Args:
        row (pd.Series): The row.
        
    Returns:
        datetime.date: The earliest date."""
    # earliest date is the start date, subscription purchase date, or end date
    dates = [val for val in [row.start_date, row.subscription_purchase_date, row.end_date] if not pd.isna(val)]
    if dates:
        return min(dates)


def generate_membership_events(events_df: pd.DataFrame) -> pd.DataFrame:
    """Generate membership events from the events dataframe.
    
    Args:
        events_df (pd.DataFrame): The events dataframe.
        
    Returns:
        pd.DataFrame: The membership events dataframe."""
    membership_events = events_df[events_df.event_type.isin(['Renewal', 'Subscription', 'Reimbursement' ,'Supplement', 'Separate Payment'])]
    # nonlogbook_membership_events = membership_events[~membership_events.source_type.str.contains('Logbook')]
    membership_events['earliest_date'] = membership_events.apply(earliest_date, axis=1)
    membership_events['date'] = pd.to_datetime(membership_events['earliest_date'], errors='coerce')
    return membership_events


def generate_logbook_gaps(logbook_events_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate logbook gaps from the logbook events dataframe.

    Args:
        logbook_events_df (pd.DataFrame): The logbook events dataframe.
    
    Returns:
        pd.DataFrame: The logbook gaps dataframe.
        pd.DataFrame: The logbooks weekly count dataframe."""
    response = requests.get('https://raw.githubusercontent.com/rlskoeser/shxco-missingdata-specreading/main/data/logbook-dates.json')
    logbook_dates = response.json()

    # don't consider gaps shorter than 15 days
    min_gap_days = 15

    logbook_gaps = []
    skipped_gaps = []

    oneday = timedelta(days=1)


    for i in range(len(logbook_dates) - 1):
        # gaps are between the logbook dates, so gap start is end of the first
        # and gap end is the start of the next

        # gap start and end dates are now included in the range instead of bounds outside the range
        gap_start = pd.to_datetime(logbook_dates[i]['endDate']) + oneday
        gap_end = pd.to_datetime(logbook_dates[i+1]['startDate']) - oneday
        interval = { 'start': gap_start, 'end': gap_end, 'days': (gap_end - gap_start).days }

        if interval['days'] > min_gap_days:
            logbook_gaps.append(interval) 
        elif interval['days'] > 0:  # ignore 0 and -1 duration "gaps"!
            skipped_gaps.append(interval)


    print(f"The {len(logbook_gaps)} large gaps in the logbooks")
    for interval in logbook_gaps:
        print(f"\t{interval['start'].strftime('%B %d %Y')} to {interval['end'].strftime('%B %d %Y')} ({interval['days']} days)")

    print(f"\nThe {len(skipped_gaps)} small gaps in the logbooks that will be skipped")
    for interval in skipped_gaps:
        print(f"\t{interval['start'].strftime('%B %d %Y')} to {interval['end'].strftime('%B %d %Y')} ({interval['days']} day{'s' if interval['days'] != 1 else ''})")


    # get logbook event data *except* for during gaps
    # — v1.2 dataset has 9 stray events in these gaps; 8 misattributed to logbook source, one documented in a later logbook

    logbook_events_nogaps = logbook_events_df.copy()

    for i, gap in enumerate(logbook_gaps):
        gap_start = gap['start']
        gap_end = gap['end']
        logbook_events_nogaps = logbook_events_nogaps[~((logbook_events_nogaps.logbook_date >= gap_start) & (logbook_events_nogaps.logbook_date <= gap_end))]

    logbooks_weekly_count = logbook_events_nogaps.groupby([pd.Grouper(key='logbook_date', freq='W')])['event_type'].count().reset_index()
    logbooks_weekly_count.rename(columns={'event_type': 'total'}, inplace=True)

    logbook_gaps_df = pd.DataFrame(logbook_gaps)
    logbook_gaps_df['gap_label'] = logbook_gaps_df.apply(lambda row: '%s to %s (%d days)' % (row.start.date().isoformat(), row.end.date().isoformat(), row.days), axis=1)
    return logbook_gaps_df, logbooks_weekly_count, logbook_gaps, logbook_events_nogaps


def generate_member_events(events_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate member events from the events dataframe.

    Args:
        events_df (pd.DataFrame): The events dataframe.

    Returns:
        pd.DataFrame: The member events dataframe.
        pd.DataFrame: The new member yearly count dataframe."""
    # split multiple members for shared accounts in events
    events_df[
        ["first_member_uri", "second_member_uri"]
    ] = events_df.member_uris.str.split(";", expand=True)

    # working with the first member for now...
    # generate short ids equivalent to those in member and book dataframes
    events_df["member_id"] = events_df.first_member_uri.apply(
        lambda x: x.split("/")[-2]
    )
    events_df["item_id"] = events_df.item_uri.apply(
        lambda x: x.split("/")[-2] if pd.notna(x) else None
    )

    # looking at all the data, what is the first event for each member?
    member_dates = events_df.copy()

    # make sure each event has an earliest known date
    

    member_dates['earliest_date'] = member_dates.apply(earliest_date, axis=1)

    # convert earliest date to datetime; convert partially known dates to -01-01  for now
    member_dates['date'] = pd.to_datetime(member_dates['earliest_date'], errors='coerce')

    # limit to the fields we want, drop unknown dates
    members_added = member_dates[['event_type', 'member_id', 'date', 'source_type']].dropna(subset=['date'])

    members_added = members_added[members_added['date'] < datetime(1942, 1, 1)]

    # limit to member uri and date; then group by member and get the first date
    members_grouped = members_added[["member_id", "date"]].groupby("member_id")
    members_first_dates = members_grouped.first().reset_index()


    newmember_yearly_count = members_first_dates.groupby([pd.Grouper(key='date', freq='Y')])['member_id'].count().reset_index()
    newmember_yearly_count.rename(columns={'member_id': 'total'}, inplace=True)

    # group again but report on source and event type;
    # customize sorting to order so subscriptions will show up first


    # main order we care about is subscription first; other order matters less; reimbursement would be expected last
    event_type = CategoricalDtype(categories=["Subscription", "Renewal", "Separate Payment", "Borrow", "Purchase", "Supplement", "Request", "Gift", "Crossed out", "Reimbursement"], ordered=True)
    # copy member data frame, and convert event type to our new categorical type
    member_events = members_added.copy()

    member_events['event_type'] = member_events.event_type.astype(event_type)

    # sort by date, then sort by event type so if there are any same-day events,
    # subscription should always be first
    member_events = member_events.sort_values(by=['date', 'event_type'])

    # members_first_events = member_events.groupby("member_id").first().reset_index()
    return member_events, newmember_yearly_count, members_first_dates



def generate_newmember_subscriptions(member_events, logbook_gaps):
    # go back to member events, limit to logbooks AND by event type, then group and get first event for each member
    subscription_first_events = member_events[member_events.source_type.str.contains('Logbook') & member_events.event_type.isin(['Subscription', 'Renewal'])].groupby("member_id").first().reset_index()

    # exclude from gaps, just in case

    subscription_first_events_nogaps = subscription_first_events.copy()

    for _, gap in enumerate(logbook_gaps):
        gap_start = gap['start']
        gap_end = gap['end']
        subscription_first_events_nogaps = subscription_first_events_nogaps[~((subscription_first_events_nogaps.date >= gap_start) & (subscription_first_events_nogaps.date <= gap_end))]

    # get new member yearly count based only on subscriptions
    # newmember_subscriptions_by_year = subscription_first_events.groupby([pd.Grouper(key='date', freq='Y')])['member_id'].count().reset_index()

    newmember_subscriptions_by_year = subscription_first_events_nogaps.groupby([pd.Grouper(key='date', freq='Y')])['member_id'].count().reset_index()
    newmember_subscriptions_by_year.rename(columns={'member_id': 'total'}, inplace=True)

    # get new member monthly count based only on subscriptions, so we can forecast with prophet
    newmember_subscriptions_by_week = subscription_first_events_nogaps.groupby([pd.Grouper(key='date', freq='W')])['member_id'].count().reset_index()
    newmember_subscriptions_by_week.rename(columns={'member_id': 'total'}, inplace=True)
    return newmember_subscriptions_by_year, newmember_subscriptions_by_week
