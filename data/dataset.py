import itertools
import os.path

import numpy as np
import pandas as pd


# data directories are relative to this file
DATA_DIR = os.path.dirname(__file__)
# input data, i.e. S&co datasets
SOURCE_DATA_DIR = os.path.join(DATA_DIR, "source-data")


csv_urls_v1_1 = {
    # online version
    # 'members': 'https://dataspace.princeton.edu/bitstream/88435/dsp01b5644v608/2/SCoData_members_v1.1_2021-01.csv',
    # 'books': 'https://dataspace.princeton.edu/bitstream/88435/dsp016d570067j/2/SCoData_books_v1.1_2021-01.csv',
    # 'events': 'https://dataspace.princeton.edu/bitstream/88435/dsp012n49t475g/2/SCoData_events_v1.1_2021-01.csv'
    # local copy
    "members": os.path.join(SOURCE_DATA_DIR, "SCoData_members_v1.1_2021-01.csv"),
    "members": os.path.join(SOURCE_DATA_DIR, "SCoData_members_v1.1_2021-01.csv"),
    "books": os.path.join(SOURCE_DATA_DIR, "SCoData_books_v1.1_2021-01.csv"),
    "events": os.path.join(SOURCE_DATA_DIR, "SCoData_events_v1.1_2021-01.csv"),
}

csv_urls = {
    # online URLs TBD
    # local copy
    "members": os.path.join(SOURCE_DATA_DIR, "SCoData_members_v1.2_2022-01.csv"),
    "books": os.path.join(SOURCE_DATA_DIR, "SCoData_books_v1.2_2022-01.csv"),
    "events": os.path.join(SOURCE_DATA_DIR, "SCoData_events_v1.2_2022-01.csv"),
}


def get_shxco_data():
    # load S&co datasets and return as pandas dataframes
    # returns members, books, events

    members_df = pd.read_csv(csv_urls["members"])
    books_df = pd.read_csv(csv_urls["books"])
    events_df = pd.read_csv(csv_urls["events"])

    # datasets use URIs for identifiers; generate short-form versions
    # across all datasets for easier display/use

    # - generate short id from book uri
    books_df["id"] = books_df.uri.apply(lambda x: x.split("/")[-2])
    # - generate short form member id
    members_df["member_id"] = members_df.uri.apply(lambda x: x.split("/")[-2])

    # split multiple members for shared accounts in events
    events_df[
        ["first_member_uri", "second_member_uri"]
    ] = events_df.member_uris.str.split(";", expand=True)

    # remove events for organizations and shared accounts,
    # since they are unlikely to be helpful or predictive in our model
    # - remove shared accounts (any event with a second member uri)
    events_df = events_df[events_df.second_member_uri.isna()]

    # working with the first member for now...
    # generate short ids equivalent to those in member and book dataframes
    events_df["member_id"] = events_df.first_member_uri.apply(
        lambda x: x.split("/")[-2]
    )
    events_df["item_uri"] = events_df.item_uri.apply(
        lambda x: x.split("/")[-2] if pd.notna(x) else None
    )

    return (members_df, books_df, events_df)