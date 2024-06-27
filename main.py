import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from data_process import process_data
from get_data import fetch_data_from_api
import traceback
import os

# Initialize the Dash app
app = dash.Dash(__name__)

# API endpoint
api_url = "https://mongodb-api-hmeu.onrender.com"

# Header
header = html.Div([
    html.Img(src="assets/logo.png", style={'height':'90px', 'width':'auto', 'float':'left'}),
    html.Div([
        html.H1("Water Monitoring Unit", style={'text-align':'center', 'color':'#010738'}),
        html.H3("Suman Nagar", style={'text-align':'center', 'color':'#010738'}),
    ], style={'text-align': 'center', 'flex-grow':'1'}),
    html.Img(src="assets/itc.png", style={'height':'90px', 'width':'auto', 'float':'right'}),
    html.Img(src="assets/eyenetAqua.png", style={'height':'90px', 'width':'auto', 'float':'right'}),
], style={'display':'flex', 'justify-content':'space-between', 'align-items':'center', 'background-color':'#f5f5f5', 'padding':'2px'})

# Footer
footer = html.Footer([
    html.Div([

        html.P('Dashboard - Powered by ICCW  ', style={'textAlign': 'center', 'fontSize': '12px'}),
        html.P('Technology Implementation Partner - EyeNet Aqua', style={'textAlign': 'center', 'fontSize': '12px'}),
       ], style={'padding': '10px', 'backgroundColor': '#f0f0f0', 'marginTop': '20px'})
])

# Layout of the dashboard
app.layout = html.Div([
    header,
    html.Div(id='error-message'),
    html.Div(id='latest-values', style={'margin': '20px 0', 'textAlign': 'center'}),
    
    # Grid layout for charts
    html.Div([
        html.Div([
            dcc.Graph(id='ph-graph'),
            dcc.Graph(id='tds-graph'),
        ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'}),
        
        html.Div([
            dcc.Graph(id='frc-graph'),
            dcc.Graph(id='pressure-graph'),
        ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'}),
        
        html.Div([
            dcc.Graph(id='flow-graph'),
        ], style={'width': '50%', 'margin': 'auto'}),
    ], style={'display': 'flex', 'flexDirection': 'column', 'gap': '20px'}),
    
    footer,
    dcc.Interval(
        id='interval-component',
        interval=60000,  # in milliseconds (1 minute)
        n_intervals=0
    )
], style={'fontFamily': 'Arial, sans-serif', 'margin': '0 auto', 'maxWidth': '1200px'})

@app.callback(
    [Output('error-message', 'children'),
     Output('latest-values', 'children'),
     Output('ph-graph', 'figure'),
     Output('tds-graph', 'figure'),
     Output('frc-graph', 'figure'),
     Output('pressure-graph', 'figure'),
     Output('flow-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    try:
        data = fetch_data_from_api(api_url)
        df = process_data(data)
        
        if df.empty:
            error_message = html.Div("No data available. Please check the API connection.", style={'color': 'red'})
            empty_figure = go.Figure().add_annotation(x=2, y=2, text="No data available", showarrow=False)
            empty_values = html.Div("No data available")
            return (error_message, empty_values) + (empty_figure,) * 5

        # Create figures
        figures = {}
        params = ['pH', 'TDS', 'FRC', 'pressure', 'flow']
        for param in params:
            fig = go.Figure()
            if f'source_{param}' in df.columns:
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df[f'source_{param}'], mode='lines+markers', line=dict(color='green')))
            fig.update_layout(
                title=f'Source {param} over Time', 
                xaxis_title='Time', 
                yaxis_title=param,
                height=400,
                width=550
            )
            figures[param] = fig

        # Get latest values
        latest = df.iloc[-1]
        latest_values = html.Div([
            html.H3('Latest Values:'),
            html.Div([
                html.Div([
                    html.P(f"{param}: {latest.get(f'source_{param}', 'N/A')}", 
                           style={'margin': '5px', 'padding': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px'})
                    for param in params
                ], style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap'})
            ])
        ])

        return (html.Div(), latest_values) + tuple(figures[param] for param in params)
    
    except Exception as e:
        print(traceback.format_exc())  # This will print the full traceback
        error_message = html.Div(f"An error occurred: {str(e)}", style={'color': 'red'})
        empty_figure = go.Figure().add_annotation(x=2, y=2, text="Error occurred", showarrow=False)
        empty_values = html.Div("Error occurred")
        return (error_message, empty_values) + (empty_figure,) * 5

# Run the app

if __name__ == '__main__':
    # Get port and debug mode from environment variables
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'

    # Run the app
    app.run_server(host='0.0.0.0', port=port, debug=debug)
