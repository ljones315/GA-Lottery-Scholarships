import dash
import os
from dash import dcc, html, callback, Input, Output
import plotly.express as px
import pandas as pd
from lottery_hope import get_data

# load dict from the pickle file
if not os.path.exists('./data'):
    get_data()
df = pd.read_pickle('./data')
filtered_df = df[df["County"] != 'CLARKE']
filtered_df = filtered_df[filtered_df["County"] != 'OCONEE']

fig = px.scatter(
    df,
    x='County',
    y='Ratio',
    color='Income',
    hover_name='County',
    hover_data={'Ratio': True, 'Income': True},
    color_continuous_scale='Viridis',
    size_max=50,
    title='HOPE/Lottery Ratio by County with Median Income'
)


fig_2 = px.scatter(
    filtered_df,
    x='County',
    y='Ratio',
    color='Income',
    hover_name='County',
    hover_data={'Ratio': True, 'Income': True},
    color_continuous_scale='Viridis',
    size_max=50,
    title='HOPE/Lottery Ratio by County with Median Income'
)

fig.update_layout(
    xaxis_title='County',
    yaxis_title='HOPE Money / Lottery Sales Ratio',
    xaxis_tickangle=45,
    template='plotly_white',
    font=dict(family="Open Sans, sans-serif"),
)

fig_2.update_layout(
    xaxis_title='County',
    yaxis_title='HOPE Money / Lottery Sales Ratio',
    xaxis_tickangle=45,
    template='plotly_white',
    font=dict(family="Open Sans, sans-serif"),
)


fig.update_traces(marker=dict(size=20))

# y <= 1 is the threshold where a county spends more on lottery than they recieve in funding
fig.add_shape(
    type="line",
    x0=-0.5,
    y0=1,
    x1=len(df['County'])-0.5,
    y1=1,
    line=dict(
        color="red",
        width=2,
        dash="solid"
    )
)

fig_2.update_traces(marker=dict(size=20))
fig_2.add_shape(
    type="line",
    x0=-0.5,
    y0=1,
    x1=len(df['County'])-0.5,
    y1=1,
    line=dict(
        color="red",
        width=2,
        dash="solid"
    )
)

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Lottery Sales and HOPE Scholarships", style={'font-family': 'Open Sans, sans-serif'}),
    html.H3("Assessing the wealth of Georgia counties and their ratio of lottery spending to scholarship funding.",
            style={'font-family': 'Open Sans, sans-serif'}),
    dcc.Checklist(["Remove Outliers (makes it easier to read)"], id="toggle"),
    dcc.Graph(
        id='scatter-plot',
        figure=fig,
        style={'height': '90vh'},
        config={'responsive': True}
    ),
    html.Div([
        html.H2("Some notes:"),
        html.Ul([
            html.Li("A higher ratio means that the county takes in a lot more money in scholarship funding than it spends on lottery."),
            html.Li("""Counties that fall below the red line are spending (relatively) more on lotto tickets than they're recieving in scholarship funds. 
                    The available data gives us \"retailer commissions\" rather than raw sales data, so it's not necessarily a 1:1 of spending to funding. 
                    The key thing is comparing this ratio of scholarship / lottery among counties!"""),
            html.Li("""Notice that the two BIG outliers are Clarke and Oconee, the counties surrounding Athens.
                    This makes sense - UGA is a huge school with majority in-state students, all of whom have good high school stats.
                    Many of them probably change their permanent address when they go to college,
                    and college students probably aren't buying a ton of lotto tickets.
                    A similar (yet smaller) effect is shown in Bulloch county, home to Georgia Southern."""),
            html.Li("""Right behind those UGA counties, though, is Fayette!
                    Fayette also has the 3rd highest avg income (behind Forsyth and Oconee).
                    Interesting to see, though not the most surprising, since Fayette has one of the best school systems in GA
                    right alongside Forsyth and Oconee county schools."""),
            html.Li(f"Interesting to me about Fayette's education and income is that it's very high *on average*. Many cities in GA have higher income than any city in FayCo, and the best of our schools are barely inside the top 20.")
        ])
    ], style={'font-family': 'Open Sans, sans-serif'})
])


@callback(
    Output(component_id='scatter-plot', component_property='figure'),
    Input(component_id='toggle', component_property='value')
)
def toggle_outliers(toggle_val):
    if not toggle_val:
        return fig
    else:
        return fig_2


if __name__ == '__main__':
    app.run_server(debug=True)
