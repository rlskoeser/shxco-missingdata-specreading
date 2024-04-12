# Standard library imports
from datetime import timedelta, date
import math
import warnings
from typing import List

# Related third party imports
import altair as alt
import pandas as pd
from prophet import Prophet

# Disable max rows for altair
alt.data_transformers.disable_max_rows()

# Ignore warnings
warnings.filterwarnings('ignore')


def plot_gap_areas(logbook_gaps: List, chart_height: int, newmember_subscriptions_by_week: pd.DataFrame, include_line: bool = False) -> alt.Chart:
    """Plot the gap areas.

    Args:
        logbook_gaps (List): The logbook gaps.
        chart_height (int): The chart height.
        newmember_subscriptions_by_week (pd.DataFrame): The new member subscriptions by week.
        include_line (bool): Whether to include the line.
    
    Returns:
        alt.Chart: The gap areas."""
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

def prepare_data_for_prophet(weekly_subscriptions: pd.DataFrame, gap_start_date: date, post1932_date: date) -> pd.DataFrame:
    """Prepare data for Prophet.
    
    Args:
        weekly_subscriptions (pd.DataFrame): The weekly subscriptions.
        gap_start_date (date): The gap start date.
        post1932_date (date): The post 1932 date.
    
    Returns:
        pd.DataFrame: The data for Prophet."""
    # Filter data based on gap start date and post1932 condition
    data_before_gap = weekly_subscriptions[weekly_subscriptions.date < gap_start_date]
    if gap_start_date.year >= 1936:
        data_before_gap = data_before_gap[data_before_gap.date >= post1932_date]
    # Rename columns for Prophet
    return data_before_gap.rename(columns={'date': 'ds', 'total': 'y'})

def forecast_gap_with_prophet(data_before_gap: pd.DataFrame, gap_duration: dict, time_duration: date, use_weekly_growth_cap:bool=False, growth_cap:bool=None, model_weekly:bool=True, model_monthly:bool=False, model_daily:bool=False) -> pd.DataFrame:
    """Forecast gap with Prophet.

    Args:
        data_before_gap (pd.DataFrame): The data before gap.
        gap_duration (dict): The gap duration.
        use_weekly_growth_cap (bool): Whether to use weekly growth cap.
        growth_cap (bool): The growth cap.

    Returns:
        pd.DataFrame: The forecasted gap with Prophet."""
    # Initialize Prophet and fit data
    if use_weekly_growth_cap:
        prophet_model = Prophet(growth='logistic', weekly_seasonality=True)
        data_before_gap['floor'] = 0
        data_before_gap['cap'] = growth_cap
    else:
        if model_daily:
            prophet_model = Prophet(daily_seasonality=True)
        else:
            prophet_model = Prophet()
    prophet_model.fit(data_before_gap)
    
    # Calculate forecast period in weeks and add extra buffer
    if model_weekly:
        forecast_duration = math.ceil(gap_duration['days'] / 7) + 7
        future_subscriptions = prophet_model.make_future_dataframe(periods=forecast_duration, freq='W')
    if model_monthly:
        forecast_duration = math.ceil(gap_duration['days'] / 30) + 2
        future_subscriptions = prophet_model.make_future_dataframe(periods=forecast_duration, freq='MS')
    if model_daily:
        forecast_duration = gap_duration['days']
        future_subscriptions = prophet_model.make_future_dataframe(periods=forecast_duration, freq='D')
    # Perform forecasting
    if use_weekly_growth_cap:
        future_subscriptions['floor'] = 0
        future_subscriptions['cap'] = growth_cap
    forecasted_subscriptions = prophet_model.predict(future_subscriptions)
    
    # Filter forecast for the gap duration with an additional one-week buffer
    forecast_near_gap = forecasted_subscriptions[(forecasted_subscriptions.ds > (gap_duration['start'] - time_duration)) & (forecasted_subscriptions.ds < (gap_duration['end'] + time_duration))]
    return forecasted_subscriptions, forecast_near_gap

def forecast_missing_subscriptions(weekly_subscriptions: pd.DataFrame, logbook_gaps: List, post1932_date: date, model_weekly:bool=True, model_monthly:bool=False, model_daily:bool=False, train_all_data:bool=False, return_prophet_model:bool=False, return_all_gap_forecasts:bool=False, use_weekly_growth_cap:bool=False, use_total_growth_cap:bool=False) -> pd.DataFrame:
    """Forecast missing subscriptions.

    Args:
        weekly_subscriptions (pd.DataFrame): The weekly subscriptions.
        logbook_gaps (List): The logbook gaps.
        post1932_date (date): The post 1932 date.
        model_weekly (bool): Whether to model weekly.
        model_monthly (bool): Whether to model monthly.
        model_daily (bool): Whether to model daily.
        train_all_data (bool): Whether to train all data.
        return_prophet_model (bool): Whether to return the Prophet model.
        return_all_gap_forecasts (bool): Whether to return all gap forecasts.
        use_weekly_growth_cap (bool): Whether to use weekly growth cap.
        use_total_growth_cap (bool): Whether to use total growth cap.
    
    Returns:
        pd.DataFrame: The missing subscriptions forecast."""
    
    time_duration = timedelta(days=30 * 6) if model_monthly else timedelta(days=7)

    growth_cap = weekly_subscriptions.total.max() if use_weekly_growth_cap else None
    if train_all_data:
        prophet_model = Prophet(weekly_seasonality=True, growth='logistic') if use_total_growth_cap else Prophet(weekly_seasonality=True)
        if use_total_growth_cap:
            weekly_subscriptions['floor'] = 0
            weekly_subscriptions['cap'] = growth_cap
        prophet_model.fit(weekly_subscriptions.rename(columns={'date': 'ds', 'total': 'y'}))
    
    all_forecasts = []
    all_gap_forecasts = []

    for gap in logbook_gaps:
        gap_start_date = gap['start']

        data_before_gap = prepare_data_for_prophet(weekly_subscriptions, gap_start_date, post1932_date)
        forecasted_subscriptions, forecasted_near_gap = forecast_gap_with_prophet(data_before_gap, gap, time_duration, use_weekly_growth_cap, growth_cap, model_weekly, model_monthly, model_daily)
        
        # Optional: Display or process forecast_near_gap as needed
        # display(forecast_near_gap.head())

        if return_all_gap_forecasts:
            all_gap_forecasts.append(forecasted_near_gap)

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
    elif return_all_gap_forecasts:
        return pd.concat(all_gap_forecasts)
    else:
        return pd.concat(all_forecasts)

def plot_newsubs_weekly_forecast(forecast_df: pd.DataFrame, gap_areas: alt.Chart, logbook_gaps: List, chart_height: int, post1932: date, newmember_subscriptions_by_week: pd.DataFrame, show_model:bool=False, separate_model_decades:bool=False) -> alt.Chart:
    """Plot the new subscriptions weekly forecast.

    Args:
        forecast_df (pd.DataFrame): The forecast dataframe.
        gap_areas (alt.Chart): The gap areas.
        logbook_gaps (List): The logbook gaps.
        chart_height (int): The chart height.
        post1932 (date): The post 1932 date.
        newmember_subscriptions_by_week (pd.DataFrame): The new member subscriptions by week.
        show_model (bool): Whether to show the model.
        separate_model_decades (bool): Whether to separate the model decades.
    
    Returns:
        alt.Chart: The new subscriptions weekly forecast."""
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

    for _, gap in enumerate(logbook_gaps):
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
