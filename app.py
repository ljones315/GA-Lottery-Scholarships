import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import dash
from dash import dcc, html

from lottery_hope import get_data


DATA_PATH = "./data"


def load_data():
    if not os.path.exists(DATA_PATH):
        get_data()
    df = pd.read_pickle(DATA_PATH)
    filtered_df = df[~df["County"].isin(["CLARKE", "OCONEE"])]
    return df, filtered_df


def make_toggle_figure(df: pd.DataFrame, filtered_df: pd.DataFrame) -> go.Figure:
    # Build the "all counties" plot via Plotly Express for nicer defaults,
    # then convert to go.Figure so we can add JS buttons (updatemenus).
    base = px.scatter(
        df,
        x="County",
        y="Ratio",
        color="Income",
        hover_name="County",
        hover_data={"Ratio": True, "Income": True},
        color_continuous_scale="Viridis",
        size_max=50,
        title="HOPE/Lottery Ratio by County with Median Income",
    )
    fig = go.Figure(base)

    # Add a SECOND trace for the filtered dataset using the same styling.
    # Use the same continuous colorscale; Plotly will keep a consistent coloraxis.
    filtered_trace = px.scatter(
        filtered_df,
        x="County",
        y="Ratio",
        color="Income",
        hover_name="County",
        hover_data={"Ratio": True, "Income": True},
        color_continuous_scale="Viridis",
    ).data[0]
    filtered_trace.visible = False
    fig.add_trace(filtered_trace)

    # Common styling
    fig.update_layout(
        xaxis_title="County",
        yaxis_title="HOPE Money / Lottery Sales Ratio",
        xaxis_tickangle=45,
        template="plotly_white",
        font=dict(family="Open Sans, sans-serif"),
        margin=dict(t=120),
    )
    fig.update_traces(marker=dict(size=20))

    # Add TWO threshold lines (y=1), one per dataset, and toggle their visibility
    # so the red line always spans the currently-visible x categories.
    fig.add_shape(
        type="line",
        x0=-0.5,
        y0=1,
        x1=len(df["County"]) - 0.5,
        y1=1,
        line=dict(color="red", width=2),
        name="threshold_all",
    )
    fig.add_shape(
        type="line",
        x0=-0.5,
        y0=1,
        x1=len(filtered_df["County"]) - 0.5,
        y1=1,
        line=dict(color="red", width=2),
        name="threshold_filtered",
        visible=False,
    )

    # Buttons: toggle which trace (and which threshold line) is visible
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.0,
                y=1.18,
                buttons=[
                    dict(
                        label="Show All Counties",
                        method="update",
                        args=[
                            {"visible": [True, False]},  # trace 0 on, trace 1 off
                            {
                                "shapes[0].visible": True,   # all threshold line
                                "shapes[1].visible": False,  # filtered threshold line
                                # keep category order consistent with the active dataset
                                "xaxis": {
                                    "categoryorder": "array",
                                    "categoryarray": list(df["County"]),
                                },
                            },
                        ],
                    ),
                    dict(
                        label="Remove Outliers",
                        method="update",
                        args=[
                            {"visible": [False, True]},  # trace 0 off, trace 1 on
                            {
                                "shapes[0].visible": False,
                                "shapes[1].visible": True,
                                "xaxis": {
                                    "categoryorder": "array",
                                    "categoryarray": list(filtered_df["County"]),
                                },
                            },
                        ],
                    ),
                ],
            )
        ]
    )

    return fig


def export_html(fig: go.Figure, out_path: str = "hope_lottery_toggle.html"):
    fig.write_html(
        out_path,
        include_plotlyjs=True,  # embeds plotly.js => fully offline
        full_html=True,
    )
    print(f"Wrote interactive HTML: {out_path}")


# --- Build the figure once (works for BOTH export and Dash display) ---
df, filtered_df = load_data()
fig = make_toggle_figure(df, filtered_df)

# Export the offline interactive HTML (no Dash server needed to view)
export_html(fig, "hope_lottery_toggle.html")

# --- Optional: still run Dash to view it as a web app ---
app = dash.Dash(__name__)
app.layout = html.Div(
    [
        html.H1("Lottery Sales and HOPE Scholarships", style={"font-family": "Open Sans, sans-serif"}),
        html.H3(
            "Assessing the wealth of Georgia counties and their ratio of lottery spending to scholarship funding.",
            style={"font-family": "Open Sans, sans-serif"},
        ),
        dcc.Graph(
            id="scatter-plot",
            figure=fig,  # the figure already contains the toggle buttons
            style={"height": "90vh"},
            config={"responsive": True},
        ),
        html.Div(
            [
                html.H2("Some notes:"),
                html.Ul(
                    [
                        html.Li("Use the buttons above the chart to toggle outliers."),
                        html.Li("You can hover over the points to see their labels and values!"),
                        html.Li(
                            "A higher ratio means that the county takes in a lot more money in scholarship funding "
                            "than it spends on lottery."
                        ),
                        html.Li(
                            "Counties below the red line are spending (relatively) more on lotto tickets than they're "
                            "receiving in scholarship funds. The available data gives us retailer commissions rather "
                            "than raw sales data, so it’s not necessarily a 1:1 of spending to funding. The key thing "
                            "is comparing this ratio among counties."
                        ),
                        html.Li(
                            "The two big outliers are Clarke and Oconee (around Athens). This makes sense due to UGA’s "
                            "size and demographics. A similar smaller effect appears in Bulloch (Georgia Southern)."
                        ),
                        html.Li(
                            "Behind those UGA counties is Fayette, which also has high average income. Not too "
                            "surprising given its school system performance."
                        ),
                    ]
                ),
            ],
            style={"font-family": "Open Sans, sans-serif"},
        ),
    ]
)

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
