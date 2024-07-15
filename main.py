import os
from flask import Flask, request, render_template, redirect, url_for
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from branca.colormap import LinearColormap
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

UNITS = {
    "pH": "",
    "TDS": "ppm",
    "FRC": "ppm",
    "pressure": "bar",
    "flow": "kL per 10 min"
}

# Initialize Flask
server = Flask(__name__)
server.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

# Initialize Dash
app = dash.Dash(__name__, server=server, url_base_pathname='/dashboard/')

# Load GeoJSON data
@lru_cache(maxsize=None)
def load_geojson():
    geojson_path = "SumanNagar.geojson"
    return gpd.read_file(geojson_path)

# Load and process Excel data
@lru_cache(maxsize=None)
def load_excel_data():
    df = pd.read_excel('BOTH_WQ.xlsx', sheet_name="Suman_Nagar")
    return gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude), crs="EPSG:4326"
    )

gdf = load_geojson()
excel_gdf = load_excel_data()

def create_map():
    # Convert to EPSG:4326 once
    excel_gdf_4326 = excel_gdf.to_crs(epsg=4326)
    
    # Calculate map center
    map_center = [excel_gdf_4326.geometry.y.mean(), excel_gdf_4326.geometry.x.mean()]
    m = folium.Map(location=map_center, zoom_start=14)
    
    # Create colormap
    colormap_tds = LinearColormap(
        colors=['green', 'yellow', 'red'],
        vmin=excel_gdf_4326['Total Dissolved Solids (TDS)'].min(),
        vmax=excel_gdf_4326['Total Dissolved Solids (TDS)'].max(),
        caption='Total Dissolved Solids (TDS)'
    )
    
    # Create marker cluster
    marker_cluster_tds = MarkerCluster(name="TDS Data").add_to(m)
    
    # Function to create popup content
    def create_popup_content(row):
        return f"""
        Village: {row['Village']}<br>
        pH: {row['pH']}<br>
        TDS: {row['Total Dissolved Solids (TDS)']} mg/L<br>
        FRC: {row['Free Residual Chlorine (FRC)']} mg/L<br>
        Altitude: {row['Altitude']} m<br>
        Pressure: {row['Pressure']} (bar)<br>
        Tap Flow Rate: {row['Tap Flow Rate']} (m3)<br>
        """
    
    # Add markers for each point
    for idx, row in excel_gdf_4326.iterrows():
        # Determine the fill color based on the TDS value
        fill_color = colormap_tds(row['Total Dissolved Solids (TDS)'])
        
        # TDS marker (now a small dot)
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=3,  # Small radius for dot-like appearance
            popup=folium.Popup(create_popup_content(row), max_width=300),
            tooltip=row['Village'],
            color=fill_color,
            fillColor=fill_color,
            fillOpacity=1,
            weight=2
        ).add_to(marker_cluster_tds)
    
    # Add Dadupur GeoJSON
    folium.GeoJson(
        gdf,
        name="Dadupur",
        style_function=lambda feature: {
            'fillColor': 'blue',
            'color': 'black',
            'weight': 2,
            'fillOpacity': 0.1
        },
        tooltip=folium.GeoJsonTooltip(fields=['Name'], aliases=['Name: '])
    ).add_to(m)
    
    # Add layer control and colormap to the map
    folium.LayerControl().add_to(m)
    colormap_tds.add_to(m)  # This line adds the legend to the map
    
    return m

# Flask routes
@server.route('/')
def home():
    return render_template('login.html')

@server.route('/login', methods=['POST'])
def login():
    if request.form.get('username') == 'JJM_Haridwar' and request.form.get('password') == 'suman_nagar':
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
                html.Img(src="/static/itc_logo.png", style={'height': '80px', 'width': 'auto', 'marginRight': '10px'}),
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
    ], style={'width': '100%', 'backgroundColor': '#f9f9f9', 'padding': '20px 0', 'marginTop': '20px', 'boxShadow': '0 -2px 5px rgba(0,0,0,0.1)'})

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
                     'fontWeight': 'bold',
                     'fontSize': '30px',
                     'color': 'black',
                     'textAlign': 'center',
                     'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                     'border': '1px solid #7ec1fd',
                     'borderRadius': '10px'
                 }),
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.P("Select Parameter:", style={'marginBottom': '5px'}),
                        dcc.Dropdown(id="dist_column", options=COLUMNS, value="source_pH", clearable=False, style={'width': '200px'})
                    ], style={'flex': 1, 'marginRight': '10px'}),
                    html.Div([
                        html.P("Select Time Duration:", style={'marginBottom': '5px'}),
                        dcc.Dropdown(id="time_duration", options=[{'label': k, 'value': k} for k in TIME_DURATIONS.keys()],
                                     value='3 Days', clearable=False, style={'width': '200px'})
                    ], style={'flex': 1})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '20px'}),
                dcc.Graph(id="graph", style={'height': '600px'})
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            html.Div([
                html.H3("Suman Nagar, Haridwar Map", style={'textAlign': 'center'}),
                html.Iframe(id='map-iframe', srcDoc=create_map().get_root().render(), 
                            style={'width': '100%', 'height': '600px', 'border': '1px solid #ddd', 'borderRadius': '5px'})
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
            title=f'{selected_column} Vs {selected_duration}',
            xaxis_title='Time (hrs)', 
            yaxis_title=f'{selected_column} ({UNITS[selected_column.split("_")[1]]})', 
            yaxis=dict(range=[y_min, y_max]),
            height=600, 
            margin=dict(l=50, r=50, t=50, b=50),
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(size=14)
        )

        latest = df.iloc[-1]
        value_boxes = [html.Div([
            html.Div(f"Source {param}", style={'fontSize': '18px', 'marginBottom': '5px'}),
            html.Div(f"{latest.get(f'source_{param}', 'N/A')}  {UNITS[param]}", style={'fontSize': '18px'})
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
