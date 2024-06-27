import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
from data_process import process_data
from get_data import fetch_data_from_api
import traceback
import os

# Initialize the Dash app
app = dash.Dash(__name__)

# API endpoint
api_url = "https://mongodb-api-hmeu.onrender.com"

# Styles
HEADER_STYLE = {
    'display': 'flex',
    'justify-content': 'space-between',
    'align-items': 'center',
    'background-color': '#f5f5f5',
    'padding': '10px',
    'box-shadow': '0 2px 5px rgba(0,0,0,0.1)'
}

VALUE_BOX_STYLE = {
    'display': 'inline-block',
    'margin': '10px',
    'padding': '15px',
    'width': '18%',
    'height': '120px',
    'background-color': 'white',
    'font-weight': 'bold',
    'font-size': '16px',
    'border-radius': '10px',
    'box-shadow': '0 2px 5px rgba(0,0,0,0.1)',
    'text-align': 'center'
}

CHART_STYLE = {
    'margin': '20px 0',
    'padding': '20px',
    'background-color': 'white',
    'border-radius': '10px',
    'box-shadow': '0 2px 5px rgba(0,0,0,0.1)'
}

# Header
header = html.Div([
    html.Img(src="assets/logo.png", style={'height':'80px', 'width':'auto'}),
    html.Div([
        html.H1("Water Monitoring Unit", style={'text-align':'center', 'color':'#010738', 'margin': '0'}),
        html.H3("Suman Nagar", style={'text-align':'center', 'color':'#010738', 'margin': '8px 0 0 0'}),
    ]),
    html.Img(src="assets/itc.png", style={'height':'80px', 'width':'auto','float':'right'}),
    html.Img(src="assets/EyeNet Aqua.png", style={'height':'90px', 'width':'auto', 'float':'right'}),
], style=HEADER_STYLE)

# Footer
footer = html.Footer([
    html.Div([
        html.P('Dashboard - Powered by ICCW  ', style={'textAlign': 'center', 'fontSize': '12px'}),
        html.P('Technology Implementation Partner - EyeNet Aqua', style={'textAlign': 'center', 'fontSize': '12px'}),
    ], style={'padding': '10px', 'backgroundColor': '#f0f0f0', 'marginTop': '20px'})
])
#style'
COLORS = {
    'accent':'#e74c3c'
}
# Layout of the dashboard
app.layout = html.Div([
    header,
    html.Div(id='error-message', style={'color': COLORS['accent'], 'textAlign': 'center', 'margin': '10px 0'}),
    html.Div([
        html.Div(id='source-ph', className='value-box'),
        html.Div(id='source-tds', className='value-box'),
        html.Div(id='source-frc', className='value-box'),
        html.Div(id='source-pressure', className='value-box'),
        html.Div(id='source-flow', className='value-box'),
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'margin': '20px 0'}),
    
    html.Div([
        dcc.Graph(id='ph-graph', style=CHART_STYLE),
        dcc.Graph(id='tds-graph', style=CHART_STYLE),
        dcc.Graph(id='frc-graph', style=CHART_STYLE),
        dcc.Graph(id='pressure-graph', style=CHART_STYLE),
        dcc.Graph(id='flow-graph', style=CHART_STYLE),
    ]),
    
    footer,
    dcc.Interval(id='interval-component', interval=60000, n_intervals=0)
], style={'fontFamily': 'Arial, sans-serif', 'margin': '0 auto', 'maxWidth': '1200px', 'backgroundColor': '#f9f9f9'})

@app.callback(
    [Output('error-message', 'children'),
     Output('source-ph', 'children'),
     Output('source-tds', 'children'),
     Output('source-frc', 'children'),
     Output('source-pressure', 'children'),
     Output('source-flow', 'children'),
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
            error_message = "No data available. Please check the API connection."
            empty_figure = go.Figure().add_annotation(x=2, y=2, text="No data available", showarrow=False)
            empty_values = "N/A"
            return (error_message,) + (empty_values,) * 5 + (empty_figure,) * 5

        # Limit to last 1 day data points
        df = df.tail(180)

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
                margin=dict(l=50, r=50, t=50, b=50),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(size=14)
            )
            figures[param] = fig

        # Get latest values
        latest = df.iloc[-1]
        value_boxes = []
        for param in ['pH', 'TDS', 'FRC', 'pressure', 'flow']:
            value = latest.get(f'source_{param}', 'N/A')
            value_box = html.Div([
                html.Div(f"Source {param}", style={'fontSize': '14px', 'marginBottom': '5px'}),
                html.Div(f"{value}", style={'fontSize': '24px'})
            ])
            value_boxes.append(value_box)

        return (None,) + tuple(value_boxes) + tuple(figures[param] for param in params)
    
    except Exception as e:
        print(traceback.format_exc())  # This will print the full traceback
        error_message = f"An error occurred: {str(e)}"
        empty_figure = go.Figure().add_annotation(x=2, y=2, text="Error occurred", showarrow=False)
        empty_values = "Error"
        return (error_message,) + (empty_values,) * 5 + (empty_figure,) * 5

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run_server(host='0.0.0.0', port=port, debug=debug)
