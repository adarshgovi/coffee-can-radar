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

# Layout
app.layout = html.Div([
    html.H1("Ductenna Dashboard", style={'textAlign': 'center'}),

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
        dcc.Input(id="ranging-averaging", type="number", placeholder="Enter Avg 1"),
        html.Button("Confirm 1", id="confirm-btn-1", n_clicks=0),
        dcc.Input(id="heatmap-sizing", type="number", placeholder="Enter Avg 2"),
        html.Button("Confirm 2", id="confirm-btn-2", n_clicks=0),
    ], style={'display': 'flex', 'justify-content': 'center', 'gap': '10px', 'marginTop': '10px'}),

    # Live Plots
    dcc.Graph( id="scope-plot", figure={
            "data": [
                {"x": [], "y": [], "type": "scatter", "name": "Chirp"},
                {"x": [], "y": [], "type": "scatter", "name": "Square Wave"}
            ],
            "layout": {"title": "Scope Plot"}
        }
    ),

    dcc.Graph(id="fft-plot"),
    dcc.Graph(id="heatmap-plot"),

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
    dcc.Interval(id="data-update-interval", interval=1000, disabled=True)
])

@app.callback(
    Output("scope-plot", "figure"),
    Input("data-update-interval", "n_intervals"),
    prevent_initial_call=True
)
def update_plots(n_intervals):
    # Fetch data from Redis
    print("updating plots")
    scope_measurement = r.xrevrange("scope_measurement", count=1)
    print(scope_measurement)
    if scope_measurement:
        # print("got data")
        scope_measurement = scope_measurement[0][1]
        scope_measurement = json.loads(scope_measurement['data'])
        chirp = scope_measurement['chirp']
        square_wave = scope_measurement['square_wave']

        # Plot Chirp
        time = np.arange(len(chirp)) / 100000
        return {
            "x": [[time], [time]],
            "y": [[chirp], [square_wave]],
        }, [0,1]
    print("no data")

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
    Output("data-update-interval", "disabled"),
    Output("scope-status-check", "disabled"),
    Output("start-record-btn", "disabled"),
    Output("stop-record-btn", "disabled"),
    Output("error-toast", "is_open"),
    Output("error-toast", "children"),
    Output("scope-status", "children"),  # Update visual indicator
    Output("scope-status", "style"),  # Update color of indicator
    Input("scope-status-check", "n_intervals"),
    prevent_initial_call=True
)
def monitor_scope_connection(n_intervals):
    status = r.get("scope_status")
    if status == 'True':
        return False, False, False, False, False, "", "🟢 Connected", {
        'textAlign': 'center', 'marginTop': '10px', 'fontSize': '20px',
        'color': 'green', 'fontWeight': 'bold' }
    elif status == 'False':
        print("🔴 Disconnected")
        return True, True, True, True, False, "", "🔴 Disconnected", {'textAlign': 'center' , 'color': 'red', 'fontWeight': 'bold'}
    else:
        print("❌ Connection Failed!")
        print(status)
        return True, True, True, True, True, status, "🔴 Disconnected", {'textAlign': 'center', 'color': 'red', 'fontWeight': 'bold'}
    return dash.no_update


if __name__ == "__main__":
    app.run(debug=True)
