import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import requests
from datetime import datetime
from data_process import process_data
from get_data import fetch_data_from_api

# Initialize the Dash app
app = dash.Dash(__name__)

# API endpoint
api_url = "https://mongodb-api-hmeu.onrender.com"


# Define header content
header = html.Div([
    html.Div([
               html.Img(src="assets/logo.png", style={'height':'90px', 'width':'auto', 'float':'left'}),
               html.Img(src="assets/itc.png", style={'height':'90px', 'width':'auto', 'float':'right'}),
       html.Div([
            html.H1("Water Monitoring Unit", style={'text-align':'center', 'color':'#010738'}),
            html.H3("Dadpur", style={'text-align':'center', 'color':'#010738'}),
        ], style={'text-align': 'center', 'flex-grow':'1'}),
    ], className='header-container'),
], className='header', style={'display':'flex', 'justify-content':'space-between', 'align-items':'center', 'background-color':'#f5f5f5', 'padding':'2px'})

# Define footer content
footer = html.Footer([
    html.Div([
        html.P('Water Quality Dashboard - Powered by Dash', style={'textAlign': 'center', 'fontSize': '12px'}),
    ], style={'padding': '10px', 'backgroundColor': '#f0f0f0', 'marginTop': '20px'})
])

# Layout of the dashboard
app.layout = html.Div([
    
    header,
    html.Div(id='error-message'),
    dcc.Graph(id='ph-graph'),
    dcc.Graph(id='tds-graph'),
    dcc.Graph(id='frc-graph'),
    dcc.Graph(id='pressure-graph'),
    dcc.Graph(id='flow-graph'),
    html.Div(id='latest-values'),
    footer,
    dcc.Interval(
        id='interval-component',
        interval=60000,  # in milliseconds (1 minute)
        n_intervals=0
    )
])

@app.callback(
    [Output('error-message', 'children'),
     Output('ph-graph', 'figure'),
     Output('tds-graph', 'figure'),
     Output('frc-graph', 'figure'),
     Output('pressure-graph', 'figure'),
     Output('flow-graph', 'figure'),
     Output('latest-values', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n):
    data = fetch_data_from_api(api_url)  # Pass api_url to the function
    df = process_data(data)

    if df.empty:
        error_message = html.Div("No data available. Please check the API connection.", style={'color': 'red'})
        empty_figure = go.Figure().add_annotation(x=2, y=2, text="No data available", showarrow=False)
        empty_values = html.Div("No data available")
        return (error_message,) + (empty_figure,) * 5 + (empty_values,)

    # Create figures
    figures = {}
    params = ['pH', 'TDS', 'FRC', 'pressure', 'flow']
    for param in params:
        fig = go.Figure()
        if f'source_{param}' in df.columns:
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df[f'source_{param}'], mode='lines+markers',line=dict(color='green')))
        fig.update_layout(title=f'Source {param} over Time', xaxis_title='Time', yaxis_title=param)
        figures[param] = fig

    # Get latest values
    latest = df.iloc[-1]
    latest_values = html.Div([
        html.H3('Latest Values:'),
        *[html.P(f"{param}: {latest.get(f'source_{param}', 'N/A')}") for param in params]
    ])

    return (html.Div(),) + tuple(figures[param] for param in params) + (latest_values,)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)