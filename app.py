import os
import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from lottery_hope import get_data

DATA_PATH = "./data"


def load_data():
    if not os.path.exists(DATA_PATH):
        get_data()
    df = pd.read_pickle(DATA_PATH)
    filtered_df = df[~df["County"].isin(["CLARKE", "OCONEE"])]
    return df, filtered_df


def make_toggle_figure(df: pd.DataFrame, filtered_df: pd.DataFrame) -> go.Figure:
    # Base trace (ALL counties) built with Plotly Express for nice defaults
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

    # Second trace (FILTERED counties) using same styling
    filtered_trace = px.scatter(
        filtered_df,
        x="County",
        y="Ratio",
        color="Income",
        hover_name="County",
        hover_data={"Ratio": True, "Income": True},
        color_continuous_scale="Viridis",
    ).data[0]
    filtered_trace.visible = True  # default: outliers hidden (filtered shown)
    fig.data[0].visible = False
    fig.add_trace(filtered_trace)

    # Common styling
    fig.update_layout(
        height=720,
        xaxis_title="County",
        yaxis_title="HOPE Money / Lottery Sales Ratio",
        xaxis_tickangle=45,
        template="plotly_white",
        font=dict(family="Open Sans, sans-serif"),
        margin=dict(t=70),
        # Default x-axis category ordering to match filtered view
        xaxis=dict(categoryorder="array", categoryarray=list(filtered_df["County"])),
    )
    fig.update_traces(marker=dict(size=20))

    # Two threshold lines (y=1): one sized for ALL, one for FILTERED; we toggle visibility in JS.
    fig.add_shape(
        type="line",
        x0=-0.5,
        y0=1,
        x1=len(df["County"]) - 0.5,
        y1=1,
        line=dict(color="red", width=2),
        visible=False,  # default hidden (since filtered is default)
    )
    fig.add_shape(
        type="line",
        x0=-0.5,
        y0=1,
        x1=len(filtered_df["County"]) - 0.5,
        y1=1,
        line=dict(color="red", width=2),
        visible=True,  # default shown
    )

    return fig


def export_ios_toggle_html(fig: go.Figure, df: pd.DataFrame, filtered_df: pd.DataFrame,
                           out_path: str = "hope_lottery_toggle.html"):
    # Export only the Plotly div and embed plotly.js so it runs on GitHub Pages / offline.
    plot_div = pio.to_html(
        fig,
        include_plotlyjs=True,   # fully offline; use "cdn" for smaller file (needs internet)
        full_html=False,
        div_id="plot",
    )

    # Embed category arrays directly into the JS as JSON
    full_cats = df["County"].tolist()
    filt_cats = filtered_df["County"].tolist()

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>HOPE/Lottery</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 24px;
      color: #0f172a;
      background: #ffffff;
    }}
    .header {{
      max-width: 1200px;
      margin: 0 auto 8px auto;
    }}
    .title {{
      font-size: 34px;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin: 0 0 16px 0;
    }}

    .controls {{
      display: flex;
      align-items: center;
      gap: 14px;
      margin: 8px 0 14px 0;
      user-select: none;
    }}
    .label {{
      font-size: 16px;
      font-weight: 600;
      color: #0f172a;
    }}
    .state {{
      font-size: 14px;
      color: #475569;
      padding: 4px 10px;
      border-radius: 999px;
      background: #f1f5f9;
      border: 1px solid #e2e8f0;
      min-width: 62px;
      text-align: center;
    }}

    /* iOS-style switch */
    .switch {{
      position: relative;
      display: inline-block;
      width: 52px;
      height: 32px;
    }}
    .switch input {{
      opacity: 0;
      width: 0;
      height: 0;
    }}
    .slider {{
      position: absolute;
      cursor: pointer;
      top: 0; left: 0; right: 0; bottom: 0;
      background-color: #cbd5e1;
      transition: .2s;
      border-radius: 999px;
      box-shadow: inset 0 0 0 1px rgba(15,23,42,0.08);
    }}
    .slider:before {{
      position: absolute;
      content: "";
      height: 26px;
      width: 26px;
      left: 3px;
      top: 3px;
      background-color: white;
      transition: .2s;
      border-radius: 999px;
      box-shadow: 0 2px 10px rgba(15,23,42,0.18);
    }}
    input:checked + .slider {{
      background-color: #22c55e;
    }}
    input:checked + .slider:before {{
      transform: translateX(20px);
    }}

    .card {{
      max-width: 1200px;
      margin: 0 auto;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 14px 14px 2px 14px;
      box-shadow: 0 8px 30px rgba(15,23,42,0.06);
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="title">HOPE/Lottery Ratio by County with Median Income</div>

    <div class="controls">
      <div class="label">Outliers</div>

      <label class="switch" aria-label="Toggle outliers">
        <input id="outlierToggle" type="checkbox" />
        <span class="slider"></span>
      </label>

      <div id="outlierState" class="state">Hidden</div>
    </div>
  </div>

  <div class="card">
    {plot_div}
  </div>

  <script>
    (function() {{
      const toggle = document.getElementById("outlierToggle");
      const statePill = document.getElementById("outlierState");
      const plotId = "plot";

      // Category arrays for x-axis ordering
      const fullCats = {full_cats};
      const filtCats = {filt_cats};

      // Figure assumptions (from make_toggle_figure):
      // trace 0 = ALL counties
      // trace 1 = FILTERED counties
      // shapes[0] = threshold line for ALL
      // shapes[1] = threshold line for FILTERED

      function setOutliersShown(isShown) {{
        // If isShown = true: show ALL (trace0) + shape0
        // If isShown = false: show FILTERED (trace1) + shape1
        const vis = isShown ? [true, false] : [false, true];
        const cats = isShown ? fullCats : filtCats;

        Plotly.restyle(plotId, {{ visible: vis }});

        Plotly.relayout(plotId, {{
          "shapes[0].visible": isShown,
          "shapes[1].visible": !isShown,
          "xaxis.categoryorder": "array",
          "xaxis.categoryarray": cats
        }});

        statePill.textContent = isShown ? "Shown" : "Hidden";
      }}

      // Initialize: outliers hidden (filtered shown)
      toggle.checked = false;
      setOutliersShown(false);

      toggle.addEventListener("change", () => {{
        // checked means "show outliers"
        setOutliersShown(toggle.checked);
      }});
    }})();
  </script>
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print(f"Wrote iOS-toggle HTML: {out_path}")


# ---------- Build data + figure once ----------
df, filtered_df = load_data()
fig = make_toggle_figure(df, filtered_df)

# ---------- Export the standalone HTML with iOS-style switch ----------
export_ios_toggle_html(fig, df, filtered_df, "hope_lottery_toggle.html")

# ---------- Optional: Keep Dash app for local dev / hosting ----------
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
            figure=fig,  # toggle UI is only in exported HTML; this graph is plain
            style={"height": "90vh"},
            config={"responsive": True},
        ),
        html.Div(
            [
                html.H2("Some notes:"),
                html.Ul(
                    [
                        html.Li("Use the exported HTML to get the iOS-style outlier toggle."),
                        html.Li("You can hover over the points to see their labels and values!"),
                        html.Li(
                            "A higher ratio means that the county takes in a lot more money in scholarship funding "
                            "than it spends on lottery."
                        ),
                        html.Li(
                            "Counties below the red line are spending (relatively) more on lotto tickets than they're "
                            "receiving in scholarship funds. The data uses retailer commissions rather than raw sales, "
                            "so it's not a strict 1:1—focus on comparing the ratio among counties."
                        ),
                        html.Li(
                            "The two big outliers are Clarke and Oconee (UGA area). Similar smaller effect in Bulloch "
                            "(Georgia Southern)."
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
