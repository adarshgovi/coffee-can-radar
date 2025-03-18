import dash
from dash import html, dcc
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import redis
import pandas as pd

# Connect to Redis
r = redis.Redis(host="localhost", port=6379, db=0)

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='live-graph'),
    dcc.Interval(id='interval', interval=10)  # Refresh every second
])

@app.callback(Output('live-graph', 'figure'), Input('interval', 'n_intervals'))
def update_graph(n_intervals):
    # Read recent data from Redis
    data = r.xrevrange("sensor_stream", count=100)
    
    timestamps = [float(entry[1][b'timestamp']) for entry in data][::-1]
    values = [float(entry[1][b'value']) for entry in data][::-1]

    figure = go.Figure(data=[go.Scatter(x=timestamps, y=values, mode='lines+markers')])
    figure.update_layout(
        title='Real-time Sensor Data',
        xaxis_title='Timestamp',
        yaxis_title='Sensor Value'
    )
    return figure

if __name__ == '__main__':
    app.run(debug=True)
