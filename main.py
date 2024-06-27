import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from data_process import process_data
from get_data import fetch_data_from_api
import traceback
import os
import folium
from folium.plugins import MarkerCluster

# Initialize the Dash app
app = dash.Dash(__name__)

# API endpoint
API_URL = "https://mongodb-api-hmeu.onrender.com"

# Styles
HEADER_STYLE = {
    'width': '100%',
    'background-color': '#f5f5f5',
    'padding': '10px 0',
    'box-shadow': '0 2px 5px rgba(0,0,0,0.1)'
}

HEADER_CONTENT_STYLE = {
    'display': 'flex',
    'justify-content': 'space-between',
    'align-items': 'center',
    'max-width': '1200px',
    'margin': '0 auto',
    'padding': '0 20px'
}

MAP_STYLE = {
    'width': '100%',
    'height': '600px',
    'border': '1px solid #ddd',
    'border-radius': '5px',
}

FOOTER_STYLE = {
    'width': '100%',
    'background-color': '#f0f0f0',
    'padding': '20px 0',
    'margin-top': '20px'
}

FOOTER_CONTENT_STYLE = {
    'max-width': '1200px',
    'margin': '0 auto',
    'padding': '0 20px',
    'text-align': 'center'
}

COLUMNS = ["source_pH", "source_TDS", "source_FRC", "source_pressure", "source_flow"]
COLORS = {'accent': '#e74c3c'}

# Y-axis ranges for each parameter
Y_RANGES = {
    "source_pH": [0, 14],
    "source_TDS": [0, 1000],
    "source_FRC": [0, 5],
    "source_pressure": [0, 100],
    "source_flow": [0, 2]
}

# Create the Folium map
def create_map():
    # Updated coordinates for Suman Nagar, Haridwar
    suman_nagar_coords = [29.9456, 78.1645]  # Note: These are approximate coordinates, please verify
    m = folium.Map(location=suman_nagar_coords, zoom_start=14)
    folium.Marker(
        suman_nagar_coords,
        popup="Suman Nagar, Haridwar",
        tooltip="Suman Nagar"
    ).add_to(m)
    map_html = m.get_root().render()
    return map_html

# Header
header = html.Div([
    html.Div([
        html.Img(src="assets/logo.png", style={'height': '80px', 'width': 'auto'}),
        html.Div([
            html.H1("Water Monitoring Unit", style={'text-align': 'center', 'color': '#010738', 'margin': '0'}),
            html.H3("Suman Nagar", style={'text-align': 'center', 'color': '#010738', 'margin': '8px 0 0 0'}),
        ]),
        html.Div([
            html.Img(src="assets/itc.png", style={'height': '80px', 'width': 'auto', 'marginRight': '10px'}),
            html.Img(src="assets/EyeNet Aqua.png", style={'height': '90px', 'width': 'auto'}),
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], style=HEADER_CONTENT_STYLE)
], style=HEADER_STYLE)

# Footer
footer = html.Footer([
    html.Div([
        html.P('Dashboard - Powered by ICCW', style={'fontSize': '12px', 'margin': '5px 0'}),
        html.P('Technology Implementation Partner - EyeNet Aqua', style={'fontSize': '12px', 'margin': '5px 0'}),
    ], style=FOOTER_CONTENT_STYLE)
], style=FOOTER_STYLE)

# Layout of the dashboard
app.layout = html.Div([
    header,
    html.Div([
        html.Div(id='error-message', style={'color': COLORS['accent'], 'textAlign': 'center', 'margin': '10px 0'}),
        html.Div([
            html.Div(id=f'source-{param.lower()}', className='value-box')
            for param in ['pH', 'TDS', 'FRC', 'pressure', 'flow']
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'margin': '20px 0'}),
        html.Div([
            # Left column for chart
            html.Div([
                html.P("Select Column:"),
                dcc.Dropdown(id="dist_column", options=COLUMNS, value="source_pH", clearable=False),
                dcc.Graph(id="graph", style={'height': '600px'})
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            # Right column for map
            html.Div([
                html.H3("Suman Nagar, Haridwar Map", style={'textAlign': 'center'}),
                html.Iframe(srcDoc=create_map(), style=MAP_STYLE)
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%'})
        ], style={'display': 'flex', 'justifyContent': 'space-between'}),
        dcc.Interval(id='interval-component', interval=60000, n_intervals=0)
    ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '0 20px'}),
    footer
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f9f9f9'})

@app.callback(
    [Output('error-message', 'children')] +
    [Output(f'source-{param.lower()}', 'children') for param in ['pH', 'TDS', 'FRC', 'pressure', 'flow']] +
    [Output('graph', 'figure')],
    [Input('interval-component', 'n_intervals'),
     Input('dist_column', 'value')]
)
def update_dashboard(n, selected_column):
    try:
        data = fetch_data_from_api(API_URL)
        df = process_data(data)
        
        if df.empty:
            error_message = "No data available. Please check the API connection."
            empty_values = "N/A"
            empty_figure = go.Figure().add_annotation(x=2, y=2, text="No data available", showarrow=False)
            return [error_message] + [empty_values] * 5 + [empty_figure]

        # Limit to last 1 day data points
        df = df.tail(180)

        # Create figure for selected column
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df[selected_column], mode='lines+markers', line=dict(color='green')))
        
        # Get y-axis range for the selected column
        y_min, y_max = Y_RANGES.get(selected_column, [None, None])
        
        fig.update_layout(
            title=f'{selected_column} over Time',
            xaxis_title='Time',
            yaxis_title=selected_column,
            yaxis=dict(range=[y_min, y_max]),
            height=600,
            margin=dict(l=50, r=50, t=50, b=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=14)
        )

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

        return [None] + value_boxes + [fig]
    
    except Exception as e:
        print(traceback.format_exc())
        error_message = f"An error occurred: {str(e)}"
        empty_values = "Error"
        empty_figure = go.Figure().add_annotation(x=2, y=2, text="Error occurred", showarrow=False)
        return [error_message] + [empty_values] * 5 + [empty_figure]

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run_server(host='0.0.0.0', port=port, debug=debug)
