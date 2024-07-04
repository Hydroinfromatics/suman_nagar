import os
from flask import Flask, request, render_template, redirect, url_for
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta
import leafmap.foliumap as leafmap
import geopandas as gpd
from functools import lru_cache

# Import custom modules
from data_process import process_data
from get_data import fetch_data_from_api

# Configuration
API_URL = "https://mongodb-api-hmeu.onrender.com"
COLUMNS = ["source_pH", "source_TDS", "source_FRC", "source_pressure", "source_flow"]
Y_RANGES = {
    "source_pH": [7, 10],
    "source_TDS": [0, 500],
    "source_FRC": [0, 0.050],
    "source_pressure": [0, 2],
    "source_flow": [0, 15]
}
TIME_DURATIONS = {
    '1 Hour': timedelta(hours=1),
    '3 Hours': timedelta(hours=3),
    '6 Hours': timedelta(hours=6),
    '12 Hours': timedelta(hours=12),
    '24 Hours': timedelta(hours=24),
    '3 Days': timedelta(days=3),
    '1 Week': timedelta(weeks=1)
}

# Initialize Flask
server = Flask(__name__)
server.config['SECRET_KEY'] = os.urandom(24)

# Initialize Dash
app = dash.Dash(__name__, server=server, url_base_pathname='/dashboard/')

# Load GeoJSON data
@lru_cache(maxsize=None)
def load_geojson():
    geojson_path = "SumanNagar.geojson"
    return gpd.read_file(geojson_path)

gdf = load_geojson()

# Create map
def create_map():
    m = leafmap.Map(center=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom=11)
    m.add_gdf(
        gdf,
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
    m.add_layer_control()
    return m.to_html()

# Flask routes
@server.route('/')
def home():
    return render_template('login.html')

@server.route('/login', methods=['POST'])
def login():
    if request.form.get('username') == 'JJM_Haridwar' and request.form.get('password') == 'dadupur':
        return redirect(url_for('dash_app'))
    return "Invalid credentials. Please try again."

@server.route('/dashboard/')
def dash_app():
    return app.index()

# Dash layout components
def create_header():
    return html.Div([
        html.Div([
            html.Img(src="/static/logo.png", style={'height': '80px', 'width': 'auto'}),
            html.Div([
                html.H1("Water Monitoring Unit", style={'text-align': 'center', 'color': '#010738', 'margin': '0'}),
                html.H3("Suman Nagar", style={'text-align': 'center', 'color': '#010738', 'margin': '8px 0 0 0'}),
            ]),
            html.Div([
                html.Img(src="/static/itc.png", style={'height': '80px', 'width': 'auto', 'marginRight': '10px'}),
                html.Img(src="/static/EyeNet Aqua.png", style={'height': '90px', 'width': 'auto'}),
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'maxWidth': '1200px', 'margin': '0 auto', 'padding': '0 20px'})
    ], style={'width': '100%', 'backgroundColor': '#f5f5f5', 'padding': '10px 0', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'})
def create_footer():
    return html.Footer([
        html.Div([
            html.P('Dashboard - Powered by ICCW', style={'fontSize': '12px', 'margin': '5px 0'}),
            html.P('Technology Implementation Partner - EyeNet Aqua', style={'fontSize': '12px', 'margin': '5px 0'}),
        ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '0 20px', 'textAlign': 'center'})
    ], style={'width': '100%', 'backgroundColor': '#f0f0f0', 'padding': '20px 0', 'marginTop': '20px'})

# Dash layout
app.layout = html.Div([
    create_header(),
    html.Div([
        html.Div(id='error-message', style={'color': '#e74c3c', 'textAlign': 'center', 'margin': '10px 0'}),
        html.Div([html.Div(id=f'source-{param.lower()}', className='value-box') for param in ['pH', 'TDS', 'FRC', 'pressure', 'flow']],
                 style={
        'display': 'flex',
        'flexWrap': 'wrap',
        'justifyContent': 'space-around',
        'alignItems': 'center',
        'margin': '20px 0',
        'padding': '20px',
        'backgroundColor': '#ffffff',
        'border': '2px solid #333',
        'borderRadius': '10px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.P("Select Parameter:", style={'marginBottom': '5px'}),
                        dcc.Dropdown(id="dist_column", options=COLUMNS, value="source_flow", clearable=False, style={'width': '200px'})
                    ], style={'flex': 1, 'marginRight': '10px'}),
                    html.Div([
                        html.P("Select Time Duration:", style={'marginBottom': '5px'}),
                        dcc.Dropdown(id="time_duration", options=[{'label': k, 'value': k} for k in TIME_DURATIONS.keys()],
                                     value='24 Hours', clearable=False, style={'width': '200px'})
                    ], style={'flex': 1})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '20px'}),
                dcc.Graph(id="graph", style={'height': '600px'})
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            html.Div([
                html.H3("Suman Nagar, Haridwar Map", style={'textAlign': 'center'}),
                html.Iframe(srcDoc=create_map(), style={'width': '100%', 'height': '600px', 'border': '1px solid #ddd', 'borderRadius': '5px'})
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%'})
        ], style={'display': 'flex', 'justifyContent': 'space-between'}),
        html.Div([
            html.H3("Historical Data", style={'textAlign': 'center', 'marginTop': '20px'}),
            html.Div([
                html.Label("Select Date Range:"),
                dcc.DatePickerRange(id='date-picker-range', start_date=datetime.now().date() - timedelta(days=7),
                                    end_date=datetime.now().date(), display_format='YYYY-MM-DD'),
                html.Button('View Data', id='view-data-button', n_clicks=0, style={'marginLeft': '10px'})
            ], style={'marginBottom': '20px'}),
            dash_table.DataTable(id='historical-data-table', columns=[{"name": i, "id": i} for i in COLUMNS + ['timestamp']],
                                 page_size=10, style_table={'overflowX': 'auto'}),
            html.Button('Download CSV', id='download-csv-button', n_clicks=0, style={'marginTop': '10px'}),
            dcc.Download(id="download-dataframe-csv"),
        ]),
        dcc.Interval(id='interval-component', interval=60000, n_intervals=0),
        dcc.Store(id='historical-data-store')
    ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '0 20px'}),
    create_footer()
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f9f9f9'})

# Dash callbacks
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
            return ["No data available. Please check the API connection."] + ["N/A"] * 5 + [go.Figure()]

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        end_time = df['timestamp'].max()
        start_time = end_time - TIME_DURATIONS[selected_duration]
        df_filtered = df[(df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_filtered['timestamp'], y=df_filtered[selected_column], mode='lines+markers', line=dict(color='green')))
        
        y_min, y_max = Y_RANGES.get(selected_column, [None, None])
        
        fig.update_layout(
            title=f'{selected_column} over the last {selected_duration}',
            xaxis_title='Time', yaxis_title=selected_column, yaxis=dict(range=[y_min, y_max]),
            height=600, margin=dict(l=50, r=50, t=50, b=50),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=14)
        )

        latest = df.iloc[-1]
        value_boxes = [html.Div([
            html.Div(f"Source {param}", style={'fontSize': '14px', 'marginBottom': '5px'}),
            html.Div(f"{latest.get(f'source_{param}', 'N/A')}", style={'fontSize': '24px'})
        ]) for param in ['pH', 'TDS', 'FRC', 'pressure', 'flow']]

        return [None] + value_boxes + [fig]
    
    except Exception as e:
        return [f"An error occurred: {str(e)}"] + ["Error"] * 5 + [go.Figure()]

@app.callback(
    Output('historical-data-store', 'data'),
    [Input('view-data-button', 'n_clicks')],
    [State('date-picker-range', 'start_date'),
     State('date-picker-range', 'end_date')]
)
def fetch_historical_data(n_clicks, start_date, end_date):
    if n_clicks > 0:
        try:
            data = fetch_data_from_api(API_URL)
            df = process_data(data)
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            mask = (df['timestamp'].dt.date >= pd.to_datetime(start_date).date()) & \
                   (df['timestamp'].dt.date <= pd.to_datetime(end_date).date())
            filtered_df = df.loc[mask]
            
            return filtered_df.to_dict('records')
        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            return []
    return []

@app.callback(
    Output('historical-data-table', 'data'),
    [Input('historical-data-store', 'data')]
)
def update_table(data):
    return data or []

@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input("download-csv-button", "n_clicks")],
    [State('historical-data-store', 'data')]
)
def download_csv(n_clicks, data):
    if n_clicks > 0 and data:
        df = pd.DataFrame(data)
        return dcc.send_data_frame(df.to_csv, "historical_data.csv", index=False)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    server.run(host='0.0.0.0', port=port, debug=debug)