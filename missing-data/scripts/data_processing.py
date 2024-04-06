import pandas as pd
import requests
from datetime import timedelta, datetime, date
from datetimerange import DateTimeRange
import math
import warnings
warnings.filterwarnings('ignore')
import altair as alt
alt.data_transformers.disable_max_rows()

from prophet import Prophet


def load_initial_data():
    # use v1.2 datasets; load from our repo for convenience
    csv_urls = {
        # official published versions 
        'members': 'https://raw.githubusercontent.com/rlskoeser/shxco-missingdata-specreading/main/data/source-data/SCoData_members_v1.2_2022-01.csv',
        'books': 'https://raw.githubusercontent.com/rlskoeser/shxco-missingdata-specreading/main/data/source-data/SCoData_books_v1.2_2022-01.csv',
        'events': 'https://raw.githubusercontent.com/rlskoeser/shxco-missingdata-specreading/main/data/source-data/SCoData_events_v1.2_2022-01.csv',

        # project-specific data
        'partial_borrowers': 'https://raw.githubusercontent.com/rlskoeser/shxco-missingdata-specreading/main/data/partial_borrowers_collapsed.csv',
        'borrow_overrides': 'https://raw.githubusercontent.com/rlskoeser/shxco-missingdata-specreading/main/data/long_borrow_overrides.csv'
    }

    # load events
    events_df = pd.read_csv(csv_urls['events'], low_memory=False)
    return events_df

def generate_logbooks_events(events_df):
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


def earliest_date(row):
    # earliest date is the start date, subscription purchase date, or end date
    dates = [val for val in [row.start_date, row.subscription_purchase_date, row.end_date] if not pd.isna(val)]
    if dates:
        return min(dates)


def generate_membership_events(events_df):
    membership_events = events_df[events_df.event_type.isin(['Renewal', 'Subscription', 'Reimbursement' ,'Supplement', 'Separate Payment'])]
    nonlogbook_membership_events = membership_events[~membership_events.source_type.str.contains('Logbook')]
    membership_events['earliest_date'] = membership_events.apply(earliest_date, axis=1)
    membership_events['date'] = pd.to_datetime(membership_events['earliest_date'], errors='coerce')
    return membership_events



response = requests.get('https://raw.githubusercontent.com/rlskoeser/shxco-missingdata-specreading/main/data/logbook-dates.json')
logbook_dates = response.json()

# don't consider gaps shorter than 15 days
MIN_GAP_DAYS = 15

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

  if interval['days'] > MIN_GAP_DAYS:
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
from pandas.api.types import CategoricalDtype

# main order we care about is subscription first; other order matters less; reimbursement would be expected last
event_type = CategoricalDtype(categories=["Subscription", "Renewal", "Separate Payment", "Borrow", "Purchase", "Supplement", "Request", "Gift", "Crossed out", "Reimbursement"], ordered=True)
# copy member data frame, and convert event type to our new categorical type
member_events = members_added.copy()

member_events['event_type'] = member_events.event_type.astype(event_type)

# sort by date, then sort by event type so if there are any same-day events,
# subscription should always be first
member_events = member_events.sort_values(by=['date', 'event_type'])

members_first_events = member_events.groupby("member_id").first().reset_index()


def plot_gap_areas(logbook_gaps, chart_height, include_line=False):
    if include_line:
        base = alt.Chart(newmember_subscriptions_by_week).encode(
            alt.X('date:T', axis=alt.Axis(title='Duration of the Lending Library'))
        ).properties(
            width=1200,
            height=chart_height
        )


        line = base.mark_line(stroke='#5276A7').encode(
            alt.Y('total',
                axis=alt.Axis(title='Total', titleColor='#5276A7'))
        )

    gap_areas = None
    for gap in logbook_gaps:

        rect_df = pd.DataFrame({
            'x1': [pd.to_datetime(gap['start'])],
            'x2': [pd.to_datetime(gap['end'])],
        })
        area = alt.Chart(rect_df).mark_rect(opacity=0.3, color='gray').encode(
            x='x1', x2='x2',
            y=alt.value(0), y2=alt.value(chart_height)
        )

        if gap_areas is None:
            gap_areas = area 
        else:
            gap_areas += area
    return line + gap_areas if include_line else gap_areas

def prepare_data_for_prophet(weekly_subscriptions, gap_start_date, post1932_date):
    # Filter data based on gap start date and post1932 condition
    data_before_gap = weekly_subscriptions[weekly_subscriptions.date < gap_start_date]
    if gap_start_date.year >= 1936:
        data_before_gap = data_before_gap[data_before_gap.date >= post1932_date]
    # Rename columns for Prophet
    return data_before_gap.rename(columns={'date': 'ds', 'total': 'y'})

def forecast_gap_with_prophet(data_before_gap, gap_duration, one_week_duration, use_weekly_growth_cap=False, growth_cap=None):
    # Initialize Prophet and fit data
    if use_weekly_growth_cap:
        prophet_model = Prophet(growth='logistic', weekly_seasonality=True)
        data_before_gap['floor'] = 0
        data_before_gap['cap'] = growth_cap
    else:
        prophet_model = Prophet()
    prophet_model.fit(data_before_gap)
    
    # Calculate forecast period in weeks and add extra buffer
    forecast_duration = math.ceil(gap_duration['days'] / 7) + 7
    future_subscriptions = prophet_model.make_future_dataframe(periods=forecast_duration, freq='W')
    
    # Perform forecasting
    if use_weekly_growth_cap:
        future_subscriptions['floor'] = 0
        future_subscriptions['cap'] = growth_cap
    forecasted_subscriptions = prophet_model.predict(future_subscriptions)
    
    # Filter forecast for the gap duration with an additional one-week buffer
    forecast_near_gap = forecasted_subscriptions[(forecasted_subscriptions.ds > (gap_duration['start'] - one_week_duration)) & (forecasted_subscriptions.ds < (gap_duration['end'] + one_week_duration))]
    return forecasted_subscriptions

def forecast_missing_subscriptions(weekly_subscriptions, logbook_gaps, post1932_date, train_all_data=False, return_prophet_model=False, use_weekly_growth_cap=False, use_total_growth_cap=False):
    one_week_duration = timedelta(days=7)
    
    growth_cap = weekly_subscriptions.total.max() if use_weekly_growth_cap else None
    if train_all_data:
        prophet_model = Prophet(weekly_seasonality=True, growth='logistic') if use_total_growth_cap else Prophet(weekly_seasonality=True)
        if use_total_growth_cap:
            weekly_subscriptions['floor'] = 0
            weekly_subscriptions['cap'] = growth_cap
        prophet_model.fit(weekly_subscriptions.rename(columns={'date': 'ds', 'total': 'y'}))
    
    all_forecasts = []

    for gap in logbook_gaps:
        gap_start_date = gap['start']

        data_before_gap = prepare_data_for_prophet(weekly_subscriptions, gap_start_date, post1932_date)
        forecasted_subscriptions = forecast_gap_with_prophet(data_before_gap, gap, one_week_duration, use_weekly_growth_cap, growth_cap)
        
        # Optional: Display or process forecast_near_gap as needed
        # display(forecast_near_gap.head())

        if train_all_data:
            if use_total_growth_cap:
                forecasted_subscriptions['floor'] = 0
                forecasted_subscriptions['cap'] = growth_cap

            reforecasted_subscriptions = prophet_model.predict(forecasted_subscriptions)
            all_forecasts.append(reforecasted_subscriptions)
        else:
            all_forecasts.append(forecasted_subscriptions)

    # Combine all forecasts into a single DataFrame
    if return_prophet_model:
        return prophet_model, pd.concat(all_forecasts)
    else:
        return pd.concat(all_forecasts)

post1932_date = pd.to_datetime(date(1932, 9, 27))
# Assuming `weekly_subscriptions` and `logbook_gaps` are defined elsewhere
forecasted_subscriptions = forecast_missing_subscriptions(newmember_subscriptions_by_week, logbook_gaps, post1932_date)

def plot_newsubs_weekly_forecast(forecast_df, gap_areas, logbook_gaps, chart_height, post1932, show_model=False, separate_model_decades=False, newmember_subscriptions_by_week=newmember_subscriptions_by_week ):
    forecast_uniq = forecast_df.drop_duplicates(keep='first').reset_index(drop=True)
    known_df = newmember_subscriptions_by_week.copy()

    # Set base chart properties
    base = alt.Chart().encode(
        alt.X('date:T', axis=alt.Axis(title='Date'))
    ).properties(
        width=1200,
        height=chart_height  # Assuming `chart_height` is intended to be 600, adjust as needed
    )
    
    line_width = 1

    # label as documented information
    known_df['label'] = "Documented"
    label_colors = {"Documented": "#5276A7", "Forecast model - 1920s": "red", "Forecast model - 1930s": "purple", "Forecast": "orange", "Forecast model": "red"}

    if not show_model:
        keys_to_remove = ["Forecast model", "Forecast model - 1920s", "Forecast model - 1930s"]
    elif separate_model_decades:
        keys_to_remove = ["Forecast model"]
    else:
        keys_to_remove = ["Forecast model - 1920s", "Forecast model - 1930s"]

    for key in keys_to_remove:
        label_colors.pop(key, None)

    newmember_line = base.mark_line(strokeWidth=line_width).encode(
        alt.Y('total', axis=alt.Axis(title='total')),
        color=alt.Color('label:N', legend=alt.Legend(title=""), scale=alt.Scale(domain=list(label_colors.keys()), range=list(label_colors.values()))),
    ).properties(data=known_df)

    graph = newmember_line

    max_y = known_df.total.max()
    y_scale = alt.Scale(domain=(0, max_y + 5), clamp=True)

    if show_model:
        forecast_uniq['ds'] = pd.to_datetime(forecast_uniq['ds'])  # Ensure ds is datetime for comparison

        if separate_model_decades:
            forecast_uniq['label'] = forecast_uniq.apply(
                lambda x: "Forecast model - 1920s" if x.ds < post1932 else "Forecast model - 1930s", axis=1
            )

            forecast_line = base.mark_line(opacity=0.5, strokeWidth=line_width).encode(
                alt.X('ds:T'),
                alt.Y('yhat', scale=y_scale),
                color=alt.Color('label', scale=alt.Scale(domain=list(label_colors.keys()), range=list(label_colors.values())))
            ).properties(data=forecast_uniq)

            graph += forecast_line
        else:
            forecast_uniq['label'] = 'Forecast model'
            forecast_line = base.mark_line(opacity=0.5, strokeWidth=line_width).encode(
                alt.X('ds:T'), alt.Y('yhat', scale=y_scale),
                color=alt.Color("label", scale=alt.Scale(domain=list(label_colors.keys()), range=list(label_colors.values())))
            ).properties(data=forecast_uniq)

            graph += forecast_line    

    # Handle gaps
    onemonth = timedelta(days=30)

    for i, gap in enumerate(logbook_gaps):
        gap_start, gap_end = pd.to_datetime(gap['start']), pd.to_datetime(gap['end'])
        gap_forecast = forecast_uniq[(forecast_uniq.ds >= gap_start - onemonth) & (forecast_uniq.ds <= gap_end + onemonth)]


        gap_forecast['label'] = 'Forecast'
        line = base.mark_line(strokeWidth=line_width).encode(
            alt.X('ds:T'), alt.Y('yhat', scale=y_scale),
            color=alt.Color("label", scale=alt.Scale(domain=list(label_colors.keys()), range=list(label_colors.values())))
        ).properties(data=gap_forecast)

        graph += line

        # Create and combine areas for gaps
        area = base.mark_area(opacity=0.3).encode(
            alt.Y('yhat_lower', scale=y_scale),
            alt.Y2('yhat_upper'),
            alt.X('ds:T'),
            alt.Color("label", scale=alt.Scale(domain=list(label_colors.keys()), range=list(label_colors.values())))
        ).properties(data=gap_forecast)
        gap_areas += area

    return (graph + gap_areas).configure(font="Noto Serif")

