import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import dash_table
from sqlalchemy import create_engine
#df = pd.read_csv('aggr.csv', parse_dates=['Entry time'])



engine = create_engine('postgresql://nps_demo_user:12345678@demobase.chjqryvwruco.us-east-2.rds.amazonaws.com:5432/strategy')
df = pd.read_sql("SELECT * from trades", engine.connect(), parse_dates=('Entry time',))

def filter_df(df,exchange,leverage,start_date,end_date):
  df_new=df[(df['exchage']==exchange) & (df['margin']==leverage) & (df['Entry time']>start_date) & (df['Entry time']<=end_date)]
  df_new['yyym']=df_new['yyym']=df_new.apply(lambda row: pd.Timestamp(row['Entry time'].year, row['Entry time'].month, 1), axis=1)
  #df_new['month']
  return(df_new)

def calc_returns_over_month(dff):
    out = []

    for name, group in dff.groupby('yyym',as_index=False):
        exit_balance = group.head(1)['Exit balance'].values[0]
        entry_balance = group.tail(1)['Entry balance'].values[0]
        monthly_return = (exit_balance*100 / entry_balance)-100
        out.append({
            'month': group['yyym'].min(),
            'entry': entry_balance,
            'exit': exit_balance,
            'monthly_return': monthly_return
        })
    return out


def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)['BTC Price'].values[0]
    btc_end_value = dff.head(1)['BTC Price'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(dff):
    start_value = dff.tail(1)['Exit balance'].values[0]
    end_value = dff.head(1)['Entry balance'].values[0]
    returns = (end_value * 100/ start_value)-100
    return returns



app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css', 'https://codepen.io/uditagarwal/pen/YzKbqyV.css'])


app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Bitcoin Leveraged Trading Backtest Analysis", className='h2-title'),
            ],
            className='study-browser-banner row'
    ),
    html.Div(
        className="row app-body",
        children=[
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        className="padding row",
                        children=[
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Exchange",),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['exchage'].unique()
                                        ],
                                        value='Bitmex',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ]
                            ),
                            html.Div(
                            	className="two columns card",
                            	children=[
                            		html.H6("Select Leverage",),
                                    dcc.RadioItems(
                                    	id='leverage-select',
                                    	options=[{'label': label, 'value': label} for label in df['margin'].unique()],
                                    	value=1,
                                    	labelStyle={'display': 'inline-block'})




                            	]),
                            html.Div(
                            	className="three columns card",
                            	children=[
                            		html.H6("Select a Date Range",),
                            		dcc.DatePickerRange(
                    					id='date-range-select', # The id of the DatePicker, its always very important to set an Id for all our components
					                    start_date=df['Entry time'].min(), # The start_date is going to be the min of Order Date in our dataset
					                    end_date=df['Entry time'].max(),
					                    display_format='MMM YY',)



                            	]),
                            html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Strategy Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Strategy vs. Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                        ]
                )
        ]),
        html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart"
                                       
                )
            ]
        ),
      html.Div(

                className="padding row",
                children=[
                    html.Div(
                        className="six columns card",
                        children=[
                            dash_table.DataTable(
                                id='table',
                                columns=[
                                    {'name': 'Number', 'id': 'Number'},
                                    {'name': 'Trade type', 'id': 'Trade type'},
                                    {'name': 'Exposure', 'id': 'Exposure'},
                                    {'name': 'Entry balance', 'id': 'Entry balance'},
                                    {'name': 'Exit balance', 'id': 'Exit balance'},
                                    {'name': 'Pnl (incl fees)', 'id': 'Pnl (incl fees)'},
                                ],
                                style_cell={'width': '50px'},
                                style_table={
                                    'maxHeight': '450px',
                                    'overflowY': 'scroll'
                                },
                            )
                        ],

                    ),
                  dcc.Graph(
                        id="pnl-types",
                        className="six columns card",
                        figure={}
                    )
                ]
            ),
             html.Div(
                className="padding row",
                children=[
                    dcc.Graph(
                        id="daily-btc",
                        className="six columns card",
                        figure={}
                    ),
                    dcc.Graph(
                        id="balance",
                        className="six columns card",
                        figure={}
                    )
                ]
            ) 
    ])        
])


@app.callback(
    [dash.dependencies.Output('date-range-select', 'start_date'), dash.dependencies.Output('date-range-select', 'end_date')],
    [dash.dependencies.Input('exchange-select', 'value')])

def update_output(value):
	df2=df[df['exchage']==value]
	new_start=df2['Entry time'].min()
	new_end=df2['Entry time'].max()
	return new_start,new_end
    

@app.callback(
    [
        dash.dependencies.Output('monthly-chart', 'figure'),
        dash.dependencies.Output('market-returns', 'children'),
        dash.dependencies.Output('strat-returns', 'children'),
        dash.dependencies.Output('strat-vs-market', 'children')
    ],
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date')

    )
)
def update_monthly(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(dff)
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns

    return {
        'data': [
            go.Candlestick(
                open=[each['entry'] for each in data],
                close=[each['exit'] for each in data],
                x=[each['month'] for each in data],
                low=[each['entry'] for each in data],
                high=[each['exit'] for each in data]
            )
        ],
        'layout': {
            'title': 'Overview of Monthly performance'
        }
    }, f'{btc_returns:0.2f}%', f'{strat_returns:0.2f}%', f'{strat_vs_market:0.2f}%'


@app.callback(
    dash.dependencies.Output('table', 'data'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)
def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return dff.to_dict('records')


@app.callback(
	dash.dependencies.Output('pnl-types','figure'),
	(
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)

def update_bar(exchange, leverage, start_date, end_date):
	data=[]
	dff = filter_df(df, exchange, leverage, start_date, end_date)
	#short=dff[dff['Trade type']=='Short']
	#lng=dff[dff['Trade type']=='Long']
	#trace1=	go.Bar(y=short['Pnl (incl fees)'],x=short['Entry time'],name='Short')
	#trace2= go.Bar(y=lng['Pnl (incl fees)'],x=lng['Entry time'],name='Long')
	for name,group in dff.groupby('Trade type',as_index=False):
		data.append(go.Bar(y=group['Pnl (incl fees)'],x=group['Entry time'],name=name))

	return {
			'data':data,
			'layout': go.Layout(
				title='Pnl Vs Trade Type',
				width= 800,
				height= 600,
#				margin={'l': 20, 'b': 20, 't': 50, 'r': 50}
				)
	}
			

@app.callback(
    dash.dependencies.Output('daily-btc', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)

def update_btc(exchange, leverage, start_date, end_date):
	dff = filter_df(df, exchange, leverage, start_date, end_date)
	
	trace=[]
	trace.append(go.Scatter(x=dff["Entry time"], y=dff['BTC Price'], mode='lines',marker={'size': 8, "opacity": 0.6, "line": {'width': 0.5}}, ))
	return {
			'data':trace,
			'layout': go.Layout(
				title="Daily BTC Price",
				width= 800,
				height= 500)
	}

@app.callback(
    dash.dependencies.Output('balance', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)

def update_balance(exchange, leverage, start_date, end_date):
	dff = filter_df(df, exchange, leverage, start_date, end_date)
	
	trace=[]
	trace.append(go.Scatter(x=dff["Entry time"], y=dff['Exit balance']+dff['Pnl (incl fees)'], mode='lines',marker={'size': 8, "opacity": 0.6, "line": {'width': 0.5}}, ))
	return {
			'data':trace,
			'layout': go.Layout(
				title="Balance Overtime",
				width= 800,
				height= 500)
	}

if __name__ == "__main__":
    app.run_server(debug=True)