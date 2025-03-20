import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import numpy as np
import threading
import time
import pandas as pd
import data_fetcher  # Import the separate data module
# Constants for frequency-to-distance conversion
SPEED_OF_LIGHT = 3e8  # Example: Speed of wave in meters/second (adjust as needed)
BANDWIDTH = 250e6
CHIRP_DURATION = 0.02

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = dbc.Container([
    html.H1("Ductenna Live Viewer", className="text-center mt-3"),

    # Device Connection Controls
    dbc.Row([
        dbc.Col(dbc.Button("Connect", id="connect-button", color="success", className="m-2"), width="auto"),
        dbc.Col(dbc.Button("Disconnect", id="disconnect-button", color="danger", className="m-2"), width="auto"),
        dbc.Col(html.Div("Status: Disconnected", id="device-status", className="m-2 text-danger"), width="auto")
    ], justify="center"),

    # Buttons Row
    dbc.Row([
        dbc.Col(dbc.Button("Pause/Resume", id="pause-button", color="primary", className="m-2"), width="auto"),
        dbc.Col(dbc.Button("Download CSV", id="download-button", color="secondary", className="m-2"), width="auto"),
        dcc.Download(id="download-dataframe-csv"),
    ], justify="center"),

    # Peak Frequency & Distance Display
    dbc.Row([
        dbc.Col(html.H4("Peak Frequency (Hz): "), width="auto"),
        dbc.Col(html.Div(id="peak-freq", className="h4 text-primary"), width="auto"),
        dbc.Col(html.H4("Calculated Distance (m): "), width="auto"),
        dbc.Col(html.Div(id="peak-distance", className="h4 text-primary"), width="auto"),
    ], justify="center", className="mt-4"),

    # Averaging Number and Heat Map Size Inputs
    dbc.Row([
        dbc.Col([
            dbc.Label("Averaging Number"),
            dcc.Input(id="averaging-number", type="number", value=10, min=1, step=1, className="m-2")
        ], width="auto"),
        dbc.Col([
            dbc.Label("Heat Map Size"),
            dcc.Input(id="heat-map-size", type="number", value=10, min=1, step=1, className="m-2")
        ], width="auto"),
    ], justify="center", className="mt-4"),

    # Time-domain plot
    dcc.Graph(id='time-domain-plot', config={"scrollZoom": True}),

    # Frequency-domain plot
    dcc.Graph(id='fft-plot', config={"scrollZoom": True}),

    # Heat map plot
    dcc.Graph(id='heat-map-plot', config={"scrollZoom": True}),

    # Hidden divs for storing state
    dcc.Store(id="pause-state", data={"paused": False}),
    dcc.Store(id="device-connection", data={"connected": False}),

    # Interval component to refresh graphs and peak frequency display
    dcc.Interval(id='interval-component', interval=500, n_intervals=0)
], fluid=True)

# Callback to handle device connection
@app.callback(
    [Output("device-connection", "data"), Output("device-status", "children"), Output("device-status", "className")],
    [Input("connect-button", "n_clicks"), Input("disconnect-button", "n_clicks")],
    [State("device-connection", "data")]
)
def manage_device_connection(connect_clicks, disconnect_clicks, connection_data):
    ctx_trigger = dash.ctx.triggered_id  # Identify which button was clicked
    if ctx_trigger == "connect-button":
        if data_fetcher.connect_device():
            return {"connected": True}, "Status: Connected", "m-2 text-success"
    elif ctx_trigger == "disconnect-button":
        data_fetcher.disconnect_device()
        return {"connected": False}, "Status: Disconnected", "m-2 text-danger"
    return connection_data, "Status: Disconnected" if not connection_data["connected"] else "Status: Connected", "m-2 text-danger" if not connection_data["connected"] else "m-2 text-success"

# Callback to update graphs
@app.callback(
    [Output('time-domain-plot', 'figure'), Output('fft-plot', 'figure'), Output('heat-map-plot', 'figure')],
    [Input('interval-component', 'n_intervals')],
    [State('time-domain-plot', 'relayoutData'), State('fft-plot', 'relayoutData'),
     State('pause-state', 'data'), State('device-connection', 'data'),
     State('averaging-number', 'value'), State('heat-map-size', 'value')]
)
def update_graphs(n, time_relayout, fft_relayout, pause_data, connection_data, averaging_number, heat_map_size):
    if pause_data["paused"] or not connection_data["connected"]:
        raise dash.exceptions.PreventUpdate  # Stop updating if paused or disconnected

    # Update latest_data with the new averaging number and heat map size
    data_fetcher.set_averaging_number(averaging_number)
    data_fetcher.set_heat_map_size(heat_map_size)

    t, ch1, ch2, fft_freqs, fft_vals, ffts = data_fetcher.get_latest_data()

    # Time-domain plot
    time_fig = go.Figure()
    time_fig.add_trace(go.Scatter(x=t, y=ch1, mode='lines', name='Channel 1'))
    time_fig.add_trace(go.Scatter(x=t, y=ch2, mode='lines', name='Channel 2'))
    time_fig.update_layout(title="Time-Domain Signal", xaxis_title="Time (s)", yaxis_title="Voltage (V)")

    # FFT plot
    fft_fig = go.Figure()
    distances = data_fetcher.to_distance(np.array(fft_freqs))
    fft_fig.add_trace(go.Scatter(x=distances, y=fft_vals, mode='lines', name='FFT Magnitude'))
    fft_fig.update_layout(title="Frequency Spectrum", xaxis_title="Distance (m)", yaxis_title="Magnitude")

    # Heat map plot
    heat_map_fig = go.Figure(data=go.Heatmap(z=ffts,x = distances, y = np.arange(len(ffts)), colorscale='Viridis'))
    heat_map_fig.update_layout(title="Distance Heat Map", xaxis_title="Distance (m)", yaxis_title="Time (s)")
    # make y_axis taller
    heat_map_fig.update_layout(height=600)

    return time_fig, fft_fig, heat_map_fig

@app.callback(
    [Output("peak-freq", "children"), Output("peak-distance", "children")],
    [Input("interval-component", "n_intervals")],
    [State("device-connection", "data"), State("pause-state", "data")]
)
def update_peak_values(n, connection_data, pause_data):
    if not connection_data["connected"] or pause_data["paused"]:
        raise dash.exceptions.PreventUpdate  # Stop updates when disconnected or paused

    peak_freq, peak_distance = data_fetcher.get_peak_data()
    return f"{peak_freq:.2f} Hz", f"{peak_distance:.2f} m"

# Callback to toggle pause/resume
@app.callback(
    Output('pause-state', 'data'),
    [Input('pause-button', 'n_clicks')],
    [State('pause-state', 'data')]
)
def toggle_pause(n_clicks, pause_data):
    if n_clicks is None:
        return pause_data
    pause_data["paused"] = not pause_data["paused"]
    return pause_data

# Callback to download CSV
@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input("download-button", "n_clicks")],
    prevent_initial_call=True
)
def download_csv(n_clicks):
    return data_fetcher.download_csv()

# Run the Dash app
if __name__ == '__main__':
    app.run(debug=True, port=8090)
