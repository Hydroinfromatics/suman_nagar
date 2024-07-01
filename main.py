import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from data_process import process_data
from get_data import fetch_data_from_api
import traceback
import os
import pandas as pd
from datetime import datetime, timedelta
import leafmap.foliumap as leafmap
import geopandas as gpd

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

DROPDOWN_CONTAINER_STYLE = {
    'display': 'flex',
    'justifyContent': 'space-between',
    'alignItems': 'center',
    'marginBottom': '20px'
}

DROPDOWN_STYLE = {
    'width': '200px'
}

COLUMNS = ["source_pH", "source_TDS", "source_FRC", "source_pressure", "source_flow"]
COLORS = {'accent': '#e74c3c'}

# Y-axis ranges for each parameter
Y_RANGES = {
    "source_pH": [6, 9],
    "source_TDS": [0, 500],
    "source_FRC": [0,0.1],
    "source_pressure": [0,2],
    "source_flow": [0, 20]
}

# Time duration options
TIME_DURATIONS = {
    '1 Hour': timedelta(hours=1),
    '3 Hours': timedelta(hours=3),
    '6 Hours': timedelta(hours=6),
    '12 Hours': timedelta(hours=12),
    '24 Hours': timedelta(hours=24),
    '3 Days': timedelta(days=3),
    '1 Week': timedelta(weeks=1)
}

# Paths to your GeoJSON files
#geojson_path1 = r"Dadapur.geojson"
geojson_path2 = r"SumanNagar.geojson"

# Read the GeoJSON files
#gdf1 = gpd.read_file(geojson_path1)
gdf2 = gpd.read_file(geojson_path2)

# Create the leafmap Map
def create_map():
    m = leafmap.Map(center=[gdf2.geometry.centroid.y.mean(), gdf2.geometry.centroid.x.mean()], zoom=11)

    # Add the first GeoJSON layer (points)
    m.add_gdf(
        gdf2,
        layer_name="Dadupur",
        zoom_to_layer=False,
        info_mode='on_click',
        style_function=lambda feature: {
            'fillColor': 'blue',
            'color': 'black',
            'weight': 2,
            'fillOpacity': 0.7
        }
    )

    # Add layer control
    m.add_layer_control()

    return m.to_html()

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
                html.Div([
                    html.Div([
                        html.P("Select Parameter:", style={'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id="dist_column",
                            options=COLUMNS,
                            value="source_flow",
                            clearable=False,
                            style=DROPDOWN_STYLE
                        )
                    ], style={'flex': 1, 'marginRight': '10px'}),
                    html.Div([
                        html.P("Select Time Duration:", style={'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id="time_duration",
                            options=[{'label': k, 'value': k} for k in TIME_DURATIONS.keys()],
                            value='24 Hours',
                            clearable=False,
                            style=DROPDOWN_STYLE
                        )
                    ], style={'flex': 1})
                ], style=DROPDOWN_CONTAINER_STYLE),
                dcc.Graph(id="graph", style={'height': '600px'})
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            # Right column for map
            html.Div([
                html.H3("Dadupur, Haridwar Map", style={'textAlign': 'center'}),
                html.Iframe(srcDoc=create_map(), style=MAP_STYLE)
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%'})
        ], style={'display': 'flex', 'justifyContent': 'space-between'}),
        
        # Historical data section
        html.Div([
            html.H3("Historical Data", style={'textAlign': 'center', 'marginTop': '20px'}),
            html.Div([
                html.Label("Select Date Range:"),
                dcc.DatePickerRange(
                    id='date-picker-range',
                    start_date=datetime.now().date() - timedelta(days=7),
                    end_date=datetime.now().date(),
                    display_format='YYYY-MM-DD'
                ),
                html.Button('View Data', id='view-data-button', n_clicks=0, style={'marginLeft': '10px'})
            ], style={'marginBottom': '20px'}),
            dash_table.DataTable(
                id='historical-data-table',
                columns=[{"name": i, "id": i} for i in COLUMNS + ['timestamp']],
                page_size=10,
                style_table={'overflowX': 'auto'}
            ),
            html.Button('Download CSV', id='download-csv-button', n_clicks=0, style={'marginTop': '10px'}),
            dcc.Download(id="download-dataframe-csv"),
        ]),
        
        dcc.Interval(id='interval-component', interval=60000, n_intervals=0),
        dcc.Store(id='historical-data-store')
    ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '0 20px'}),
    footer
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f9f9f9'})

@app.callback(
    [Output('error-message', 'children')] +
    [Output(f'source-{param.lower()}', 'children') for param in ['pH', 'TDS', 'FRC', 'pressure', 'flow']] +
    [Output('graph', 'figure')],
    [Input('interval-component', 'n_intervals'),
     Input('dist_column', 'value'),
     Input('time_duration', 'value')]
)
def update_dashboard(n, selected_column, selected_duration):
    try:
        data = fetch_data_from_api(API_URL)
        df = process_data(data)
        
        if df.empty:
            error_message = "No data available. Please check the API connection."
            empty_values = "N/A"
            empty_figure = go.Figure().add_annotation(x=2, y=2, text="No data available", showarrow=False)
            return [error_message] + [empty_values] * 5 + [empty_figure]

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Filter data based on selected duration
        end_time = df['timestamp'].max()
        start_time = end_time - TIME_DURATIONS[selected_duration]
        df_filtered = df[(df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)]

        # Create figure for selected column
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_filtered['timestamp'], y=df_filtered[selected_column], mode='lines+markers', line=dict(color='green')))
        
        # Get y-axis range for the selected column
        y_min, y_max = Y_RANGES.get(selected_column, [None, None])
        
        fig.update_layout(
            title=f'{selected_column} over the last {selected_duration}',
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

@app.callback(
    Output('historical-data-store', 'data'),
    [Input('view-data-button', 'n_clicks')],
    [State('date-picker-range', 'start_date'),
     State('date-picker-range', 'end_date')]
)
def fetch_historical_data(n_clicks, start_date, end_date):
    if n_clicks > 0:
        try:
            # Fetch all data from the API
            data = fetch_data_from_api(API_URL)
            df = process_data(data)
            
            # Filter data based on the selected date range
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            mask = (df['timestamp'].dt.date >= pd.to_datetime(start_date).date()) & \
                   (df['timestamp'].dt.date <= pd.to_datetime(end_date).date())
            filtered_df = df.loc[mask]
            
            return filtered_df.to_dict('records')
        except Exception as e:
            print(traceback.format_exc())
            return []
    return []

@app.callback(
    Output('historical-data-table', 'data'),
    [Input('historical-data-store', 'data')]
)
def update_table(data):
    if data:
        return data
    return []

@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input("download-csv-button", "n_clicks")],
    [State('historical-data-store', 'data')]
)
def download_csv(n_clicks, data):
    if n_clicks > 0 and data:
        df = pd.DataFrame(data)
        return dcc.send_data_frame(df.to_csv, "historical_data.csv", index=False)

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run_server(host='0.0.0.0', port=port, debug=debug)
