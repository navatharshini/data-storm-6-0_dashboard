import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

app = dash.Dash(__name__)
app.title = "Agent Dashboard"

# Load data
df = pd.read_csv('train_storming_round.csv')

# Derived metrics
df['months_to_first_sale'] = pd.to_datetime(df['first_policy_sold_month'], errors='coerce').dt.month - pd.to_datetime(df['agent_join_month'], errors='coerce').dt.month
df['months_to_first_sale'] = df['months_to_first_sale'].fillna(0).astype(int)
df['risk_score'] = df['new_policy_count'].apply(lambda x: 1 - min(x / 10, 1))

# CSS style definitions
card_style = {
    'padding': '20px',
    'margin': '10px',
    'backgroundColor': '#f9f9f9',
    'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.1)',
    'borderRadius': '10px',
    'flex': '1',
    'textAlign': 'center'
}
row_style = {
    'display': 'flex',
    'flexWrap': 'wrap',
    'justifyContent': 'space-around'
}

app.layout = html.Div([
    html.H1("Agent Performance Dashboard", style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#007BFF', 'color': 'white'}),
    
    # Summary metrics
    html.Div([
        html.Div([
            html.H3("Total Agents"),
            html.P(f"{len(df):,}")
        ], style=card_style),

        html.Div([
            html.H3("Avg New Policies"),
            html.P(f"{df['new_policy_count'].mean():.2f}")
        ], style=card_style),

        html.Div([
            html.H3("Top Performer"),
            html.P(df.loc[df['new_policy_count'].idxmax(), 'agent_code'])
        ], style=card_style)
    ], style=row_style),
    
    html.Br(),

    # Visualizations
    html.Div([
        html.Div([
            dcc.Graph(id='policy-distribution'),
            dcc.Graph(id='income-vs-policy')
        ], style={'flex': '1', 'padding': '10px'}),

        html.Div([
            dcc.Graph(id='risk-score-chart'),
            html.Label("Select Agent:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='agent-selector',
                options=[{'label': i, 'value': i} for i in df['agent_code'].unique()],
                value=df['agent_code'].iloc[0],
                style={'marginTop': '10px'}
            )
        ], style={'flex': '1', 'padding': '10px'})
    ], style=row_style),

    html.Br(),

    # Action recommendations
    html.Div([
        html.Div([
            html.H3("📋 Suggested Interventions", style={'marginBottom': '10px'}),
            html.Ul(id='action-items')
        ], style=card_style)
    ], style={'padding': '20px'})
])

# Callbacks
@app.callback(
    Output('policy-distribution', 'figure'),
    Input('agent-selector', 'value'))
def update_policy_distribution(selected_agent):
    fig = px.histogram(df, x='new_policy_count', nbins=20, title="New Policy Count Distribution")
    agent_value = df[df['agent_code'] == selected_agent]['new_policy_count'].values[0]
    fig.add_vline(x=agent_value, line_dash="dash", line_color="red")
    return fig

@app.callback(
    Output('income-vs-policy', 'figure'),
    Input('agent-selector', 'value'))
def update_income_vs_policy(selected_agent):
    fig = px.scatter(df, x='new_policy_count', y='net_income', hover_name='agent_code',
                     title="Income vs. New Policies")
    selected = df[df['agent_code'] == selected_agent]
    fig.add_trace(go.Scatter(x=selected['new_policy_count'], y=selected['net_income'],
                             mode='markers', marker=dict(size=12, color='red'),
                             name='Selected Agent'))
    return fig

@app.callback(
    Output('risk-score-chart', 'figure'),
    Input('agent-selector', 'value'))
def update_risk_chart(selected_agent):
    fig = px.bar(df.sort_values('risk_score', ascending=False).head(20),
                 x='agent_code', y='risk_score', title='Top 20 Agents by Risk Score')
    fig.update_layout(xaxis_title="Agent", yaxis_title="Risk Score (Lower is better)")
    return fig

@app.callback(
    Output('action-items', 'children'),
    Input('agent-selector', 'value'))
def update_actions(selected_agent):
    agent_data = df[df['agent_code'] == selected_agent].iloc[0]
    actions = []

    if agent_data['new_policy_count'] < 3:
        actions.append(html.Li("🚨 Assign a mentor to boost performance"))
    if agent_data['unique_proposal'] < 10:
        actions.append(html.Li("📝 Encourage proposal generation activities"))
    if agent_data['months_to_first_sale'] > 3:
        actions.append(html.Li("📈 Provide sales acceleration support"))

    if not actions:
        actions.append(html.Li("✅ Agent is performing well. No intervention needed."))
    
    return actions

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
