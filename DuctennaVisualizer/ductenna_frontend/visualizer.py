import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import redis
import numpy as np
import json
import time

# Connect to Redis
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Dash App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Main Dashboard Layout
ranging_dashboard_layout = html.Div([
    html.H1("Ranging Dashboard", style={'textAlign': 'center'}),
    dcc.Graph( id="chirp-plot"),
    dcc.Graph(id="fft-plot"),
    dcc.Graph(id="cropped-fft-plot"),
    dcc.Graph(id="heatmap-plot"),

])

# New Page Layout
doppler_dashboard_layout = html.Div([
    html.H1("Doppler Dashboard", style={'textAlign': 'center'}),
    dcc.Graph(id="doppler-fft-plot"),
    dcc.Graph(id="cropped-doppler-fft-plot"),
    dcc.Graph(id="doppler-heatmap-plot"),
])

# Layout
app.layout = html.Div([
    html.H1("Ductenna Dashboard", style={'textAlign': 'center'}),

    dcc.Location(id="url", refresh=False),  # Tracks the current URL
    html.Div([
        dcc.Link("Ranger (Distance)", href="/", style={'marginRight': '20px'}),
        dcc.Link("Doppler (Velocity)", href="/doppler"),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),
    # Main Dashboard Layout

    # Connection Controls
    html.Div([
        html.Button("Connect", id="connect-btn", n_clicks=0),
        html.Button("Disconnect", id="disconnect-btn", n_clicks=0),
        html.Button("Pause", id="pause-btn", n_clicks=0),
        html.Button("Start Recording", id="start-record-btn", n_clicks=0, disabled=True),
        html.Button("Stop Recording", id="stop-record-btn", n_clicks=0, disabled=True),
    ], style={'display': 'flex', 'justify-content': 'center', 'gap': '10px'}),

    html.Div(id="scope-status", children="🔴 Disconnected", style={
        'textAlign': 'center', 'marginTop': '10px', 'fontSize': '20px',
        'color': 'red', 'fontWeight': 'bold'
    }),

    # Number Inputs for Averaging
    html.Div([
        dcc.Input(id="ranging-averaging", type="number", placeholder="Enter Ranging Averaging"),
        html.Button("Confirm Averaging", id="ranging-avg-confirm-btn", n_clicks=0),
        dcc.Input(id="heatmap-sizing", type="number", placeholder="Enter Heat Map Size (num chirps)"),
        html.Button("Confirm Heatmap Sizing", id="heat-map-confirm-btn", n_clicks=0),
        dcc.Input(id="dist-vel-cutoff", type="number", placeholder="Enter Dist/Vel Cutoff (m or m/s)"),
        html.Button("Confirm FFT X Cutoff", id="distance-cutoff-confirm-btn", n_clicks=0),
        dcc.Input(id="position-label", type="text", placeholder="Enter Position Label"),
        html.Button("Confirm Position", id="position-confirm-btn", n_clicks=0),
    ], style={'display': 'flex', 'justify-content': 'center', 'gap': '10px', 'marginTop': '10px'}),

    # Live Plots
    dcc.Graph( id="raw-scope-plot"),
    html.Div(id="page-content"),  # Placeholder for page content,

    # Error Toast (Hidden Initially)
    dbc.Toast(
        id="error-toast",
        header="Error",
        is_open=False,
        dismissable=True,
        duration=10000,  # Auto-close in 5 seconds
        icon="danger",
        style={"position": "fixed", "top": "10px", "right": "10px"}
       ),

    # Interval Component (Disabled initially)
    dcc.Interval(id="scope-status-check", interval=1000, disabled=False),
    dcc.Interval(id="doppler-update-interval", interval=1500, disabled=True),
    dcc.Interval(id="ranging-update-interval", interval=1500, disabled=False)
])

@app.callback(
    Output("doppler-update-interval", "disabled", allow_duplicate=True),
    Input("url", "pathname"),
    prevent_initial_call=True
)
def toggle_new_page_updates(pathname):
    return pathname != "/doppler"  # Disable updates if not on the new page

@app.callback(
    Output("ranging-update-interval", "disabled", allow_duplicate=True),
    Input("url", "pathname"),
    prevent_initial_call=True
)
def toggle_main_dashboard_updates(pathname):
    return pathname != "/"  # Disable updates if not on the main dashboard

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    print(f'pathname: {pathname}')
    r.set("current_page", pathname)
    if pathname == "/doppler":
        return doppler_dashboard_layout
    else:
        return ranging_dashboard_layout

@app.callback(
    Output("raw-scope-plot", "figure", allow_duplicate=True),
    Output("chirp-plot", "figure"),
    Output("fft-plot", "figure"),
    Output("cropped-fft-plot", "figure"),
    Output("heatmap-plot", "figure"),
    Input("ranging-update-interval", "n_intervals"),
    prevent_initial_call=True
)
def update_plots(n_intervals):
    raw_scope_fig = None
    chirp_fig = None
    fft_fig = {}
    heatmap_fig = {}
    cropped_fft_fig = {}

    # Fetch data from Redis
    scope_measurement = r.xrevrange("scope_measurement", count=1)
    if scope_measurement:
        # read data from redis
        scope_measurement = scope_measurement[0][1]
        scope_measurement = json.loads(scope_measurement['data'])
        ch1 = scope_measurement['ch1']
        ch2 = scope_measurement['ch2']
        reading_times = scope_measurement['reading_times']
        # show raw ch1 and ch2 data
        raw_scope_fig = go.Figure()
        raw_scope_fig.add_trace(go.Scatter(x=reading_times, y=ch1, mode='lines', name='Ch1'))
        raw_scope_fig.add_trace(go.Scatter(x=reading_times, y=ch2, mode='lines', name='Ch2'))
        raw_scope_fig.update_layout(title="Raw Ch1 and Ch2 Data", xaxis_title="Time (s)", yaxis_title="Voltage (V)")
        # set range for y axis
        raw_scope_fig.update_yaxes(range=[-3, 5])
    
    
    pulse_indices = r.xrevrange("pulse_indices", count=1)
    if pulse_indices:
        pulse_indices = pulse_indices[0][1]
        pulse_indices = json.loads(pulse_indices['data'])
        pulse_start_index = pulse_indices['pulse_start_index']
        pulse_end_index = pulse_indices['pulse_end_index']
        sync_pulse = ch1[pulse_start_index:pulse_end_index]
        chirp = ch2[pulse_start_index:pulse_end_index]
        chirp_times = reading_times[pulse_start_index:pulse_end_index]
        # Create time-domain plot
        chirp_fig = go.Figure()
        chirp_fig.add_trace(go.Scatter(x=chirp_times, y=chirp, mode='lines', name='Chirp'))
        chirp_fig.add_trace(go.Scatter
        (x=chirp_times, y=sync_pulse, mode='lines', name='Square Wave'))
        chirp_fig.update_layout(title="Cropped Single Chirp", xaxis_title="Time (s)", yaxis_title="Voltage (V)")
        chirp_fig.update_yaxes(range=[-3, 5])

    distance_measurement = r.xrevrange("distance_measurement", count=1)
    if distance_measurement:
        distance_measurement = distance_measurement[0][1]
        distance_measurement = json.loads(distance_measurement['data'])
        distances = distance_measurement['distances']
        fft_vals = distance_measurement['fft_vals']
        ffts = distance_measurement['fft_freqs']
        cutoff_distances = distance_measurement['cutoff_distances']
        cutoff_magnitudes = distance_measurement['cutoff_magnitudes']

        fft_fig = go.Figure()
        distances = np.arange(len(fft_vals))
        fft_fig.add_trace(go.Scatter
        (x=distances, y=fft_vals, mode='lines', name='FFT Magnitude'))
        fft_fig.update_layout(title="Frequency Spectrum", xaxis_title="Distance (m)", yaxis_title="Magnitude (dB)")

        cropped_fft_fig = go.Figure()
        cropped_fft_fig.add_trace(go.Scatter(x=cutoff_distances, y=cutoff_magnitudes, mode='lines', name='FFT Magnitude'))
        cropped_fft_fig.update_layout(title="Cropped Frequency Spectrum", xaxis_title="Distance (m)", yaxis_title="Magnitude (dB)")


    heatmap_array = r.xrevrange("heatmap_data", count=1)
    if heatmap_array:
        heatmap_data = json.loads(heatmap_array[0][1]["data"])
        heatmap = np.array(heatmap_data["heatmap"])  # Convert back to a NumPy array
        heatmap_fig = go.Figure(data=go.Heatmap(z=heatmap, y = np.arange(len(ffts)), colorscale='Viridis'))
        heatmap_fig.update_layout(title="Distance Heat Map", xaxis_title="Distance (m)", yaxis_title="Time (s)")
        heatmap_fig.update_layout(height=600)
    
    return raw_scope_fig, chirp_fig, fft_fig, cropped_fft_fig, heatmap_fig

@app.callback(
    Output("raw-scope-plot", "figure"),
    Output("doppler-fft-plot", "figure"),
    Output("cropped-doppler-fft-plot", "figure"),
    Output("doppler-heatmap-plot", "figure"),
    Input("doppler-update-interval", "n_intervals"),
    prevent_initial_call=True
)
def update_plots_doppler(n_intervals):
    raw_scope_fig = {}
    chirp_fig ={}
    fft_fig = {}
    cropped_fft_fig = {}
    heatmap_fig = {}

   # Fetch data from Redis
    scope_measurement = r.xrevrange("scope_measurement", count=1)
    if scope_measurement:
        # read data from redis
        scope_measurement = scope_measurement[0][1]
        scope_measurement = json.loads(scope_measurement['data'])
        ch1 = scope_measurement['ch1']
        ch2 = scope_measurement['ch2']
        reading_times = scope_measurement['reading_times']
        # show raw ch1 and ch2 data
        raw_scope_fig = go.Figure()
        raw_scope_fig.add_trace(go.Scatter(x=reading_times, y=ch1, mode='lines', name='Ch1'))
        raw_scope_fig.add_trace(go.Scatter(x=reading_times, y=ch2, mode='lines', name='Ch2'))
        raw_scope_fig.update_layout(title="Raw Ch1 and Ch2 Data", xaxis_title="Time (s)", yaxis_title="Voltage (V)")
        # set range for y axis
        raw_scope_fig.update_yaxes(range=[-3, 5]) 

    # Fetch data from Redis
    doppler_fft = r.xrevrange("doppler_fft", count=1)
    if doppler_fft:
        doppler_fft = doppler_fft[0][1]
        doppler_fft = json.loads(doppler_fft['data'])
        velocities = doppler_fft['velocities']
        fft_vals = doppler_fft['fft_vals']
        cropped_velocities = doppler_fft['velocities_cutoff']
        cropped_fft_vals = doppler_fft['fft_vals_cutoff']
        
        fft_fig = go.Figure()
        distances = np.arange(len(fft_vals))
        fft_fig.add_trace(go.Scatter(x=distances, y=fft_vals, mode='lines', name='FFT Magnitude'))
        fft_fig.update_layout(title="Frequency Spectrum", xaxis_title="Velocity (m/s)", yaxis_title="Magnitude (dB)")

        cropped_fft_fig = go.Figure()
        cropped_fft_fig.add_trace(go.Scatter(x=cropped_velocities, y=cropped_fft_vals, mode='lines', name='FFT Magnitude'))
        cropped_fft_fig.update_layout(title="Cropped Frequency Spectrum", xaxis_title="Velocity (m/s)", yaxis_title="Magnitude (dB)")

    heatmap_array = r.xrevrange("doppler_heatmap_data", count=1)
    if heatmap_array:
        heatmap_data = json.loads(heatmap_array[0][1]["data"])
        heatmap = np.array(heatmap_data["heatmap"])
        heatmap_fig = go.Figure(data=go.Heatmap(z=heatmap, y = np.arange(len(cropped_velocities)), colorscale='Viridis'))
        heatmap_fig.update_layout(title="Velocity Heatmap", xaxis_title="Velocity (m/s)", yaxis_title="Time (s)")
        heatmap_fig.update_layout(height=600)

    return raw_scope_fig, fft_fig, cropped_fft_fig, heatmap_fig

@app.callback(
    Output("scope-status-check", "disabled", allow_duplicate=True),
    Input("connect-btn", "n_clicks"),
    Input("disconnect-btn", "n_clicks"),
    prevent_initial_call=True
)
def update_scope_state(connect_clicks, disconnect_clicks):
    print("update scope state tiggered")
    ctx = dash.callback_context
    if not ctx.triggered:
        return True

    button_id = ctx.triggered_id
    if button_id == "connect-btn":
        r.set("scope_desired_state", "connect")  
        print("🔄 Requesting Scope Connection...")
        return False

    elif button_id == "disconnect-btn":
        r.set("scope_desired_state", "disconnect") 
        print(" Requesting Scope Disconnection...")
        return False

# Monitor Scope Connection Status
@app.callback(
    Output("scope-status-check", "disabled"),
    Output("start-record-btn", "disabled"),
    Output("stop-record-btn", "disabled"),
    Output("error-toast", "is_open", allow_duplicate=True),
    Output("error-toast", "children", allow_duplicate=True),
    Output("scope-status", "children"),  # Update visual indicator
    Output("scope-status", "style"),  # Update color of indicator
    Input("scope-status-check", "n_intervals"),
    prevent_initial_call=True
)
def monitor_scope_connection(n_intervals):
    status = r.get("scope_status")
    if status == 'True':
        return False, False, False, False, "", "🟢 Connected", {
        'textAlign': 'center', 'marginTop': '10px', 'fontSize': '20px',
        'color': 'green', 'fontWeight': 'bold' }
    elif status == 'False':
        print("🔴 Disconnected")
        return True, True, True, False, "", "🔴 Disconnected", {'textAlign': 'center' , 'color': 'red', 'fontWeight': 'bold'}
    else:
        print("❌ Connection Failed!")
        print(status)
        return True, True, True, True, status, "🔴 Disconnected", {'textAlign': 'center', 'color': 'red', 'fontWeight': 'bold'}
    return dash.no_update

@app.callback(
    Output("error-toast", "is_open", allow_duplicate=True),  # Optional: Show a toast for confirmation
    Output("error-toast", "children", allow_duplicate=True),  # Optional: Update toast message
    Input("ranging-avg-confirm-btn", "n_clicks"),
    State("ranging-averaging", "value"),
    prevent_initial_call=True
)
def ranging_avg_button(n_clicks, value):
    if value is not None:
        r.set("ranging_averaging", value)  # Store the value in Redis
        print(f"Set ranging_averaging to {value}")
        return True, f"Ranging Averaging set to {value}"
    return False, ""


@app.callback(
    Output("error-toast", "is_open", allow_duplicate=True),  # Optional: Show a toast for confirmation
    Output("error-toast", "children", allow_duplicate=True),  # Optional: Update toast message
    Input("heat-map-confirm-btn", "n_clicks"),
    State("heatmap-sizing", "value"),
    prevent_initial_call=True
)
def heat_map_size_button(n_clicks, value):
    if value is not None:
        r.set("heat_map_size", value)  # Store the value in Redis
        print(f"Set heatmap_sizing to {value}")
        return True, f"Heatmap Sizing set to {value}"
    return False, ""

@app.callback(
    Output("error-toast", "is_open", allow_duplicate=True),  # Optional: Show a toast for confirmation
    Output("error-toast", "children", allow_duplicate=True),  # Optional: Update toast message
    Input("distance-cutoff-confirm-btn", "n_clicks"),
    State("dist-vel-cutoff", "value"),
    prevent_initial_call=True
)
def distance_cutoff_button(n_clicks, value):
    if value is not None:
        r.set("distance_cutoff", value)
        print(f"Set distance_cutoff to {value}")
        return True, f"FFT X Cutoff set to {value}"
    return False, ""

@app.callback(
    Output("error-toast", "is_open", allow_duplicate=True),  # Optional: Show a toast for confirmation
    Output("error-toast", "children", allow_duplicate=True),  # Optional: Update toast message
    Input("position-confirm-btn", "n_clicks"),
    State("position-label", "value"),
    prevent_initial_call=True
)
def position_label_button(n_clicks, value):
    if value is not None:
        r.set("position_label", value)
        print(f"Set position_label to {value}")
        return True, f"Position Label set to {value}"
    return False, ""

@app.callback(
    Input("start-record-btn", "n_clicks"),
    Input("stop-record-btn", "n_clicks"),
    prevent_initial_call=True
)
def handle_recording_buttons(start_clicks, stop_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, ""

    button_id = ctx.triggered_id
    if button_id == "start-record-btn":
        r.set("recording_data", "True")  # Set recording to True in Redis
        print("Recording started")
        return 
    elif button_id == "stop-record-btn":
        r.set("recording_data", "False")  # Set recording to False in Redis
        print("Recording stopped")
        return 
    return

if __name__ == "__main__":
    app.run(debug=True, port=8060)
