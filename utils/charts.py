import vl_convert as vlc
import altair as alt


# TODO: standard chart options for font, title layout, etc. could be set here


def save_altair_chart(chart, filename, scale_factor=1):
    """
    Save an Altair chart using vl-convert

    Parameters
    ----------
    chart : altair.Chart
        Altair chart to save
    filename : str
        The path to save the chart to
    scale_factor: int or float
        The factor to scale the image resolution by.
        E.g. A value of `2` means two times the default resolution.
    """
    with alt.data_transformers.enable(
        "default"
    ), alt.data_transformers.disable_max_rows():
        if filename.split(".")[-1] == "svg":
            with open(filename, "w") as f:
                f.write(vlc.vegalite_to_svg(chart.to_dict()))
        elif filename.split(".")[-1] == "png":
            with open(filename, "wb") as f:
                f.write(vlc.vegalite_to_png(chart.to_dict(), scale=scale_factor))
        else:
            raise ValueError("Only svg and png formats are supported")


def raincloud_plot(dataset, fieldname, field_label, tooltip=None):
    """Create a raincloud plot for the density of the specified field
    in the given dataset. Takes an optional tooltip for the strip plot.
    Returns an altair chart."""

    # create a density area plot of specified fieldname

    duration_density = (
        alt.Chart(dataset)
        .transform_density(
            fieldname,
            as_=[fieldname, "density"],
        )
        .mark_area(orient="vertical")
        .encode(
            x=alt.X(fieldname, title=None, axis=alt.X(labels=False, ticks=False)),
            y=alt.Y(
                "density:Q",
                # suppress labels and ticks because we're going to combine this
                title=None,
                axis=alt.Axis(labels=False, values=[0], grid=False, ticks=False),
            ),
        )
        .properties(height=100, width=800)
    )

    # Now create jitter plot of the same field
    # jittering / stripplot adapted from https://stackoverflow.com/a/71902446/9706217

    # optional behavior when tooltip is set
    opt_encode_args = {}
    selection_opts = []
    highlight_color = alt.value("#ff7f0e")
    default_color = alt.value("rgba(31, 119, 180, 0)")  # transparent
    if tooltip is not None:
        opt_encode_args["tooltip"] = tooltip
        # if tooltip is enabled, make selection easier:
        # define a single selection that chooses the nearest point
        nearest = alt.selection_single(on="mouseover", nearest=True)
        selection_opts.append(nearest)
        # add a stroke to outline; transparent if not seleted,  otherwise highlight
        opt_encode_args["stroke"] = alt.condition(
            ~nearest, default_color, highlight_color
        )

    stripplot = (
        alt.Chart(dataset)
        .mark_circle(size=50)
        .encode(
            x=alt.X(
                fieldname,
                title=field_label,
                axis=alt.Axis(labels=True),
            ),
            y=alt.Y("jitter:Q", title=None, axis=None),
            **opt_encode_args,
        )
        .transform_calculate(jitter="(random() / 200) - 0.0052")
        .properties(
            height=120,
            width=800,
        )
        .add_selection(*selection_opts)
    )

    # use vertical concat to combine the two plots together
    raincloud_plot = alt.vconcat(duration_density, stripplot).configure_concat(
        spacing=0
    )
    return raincloud_plot
