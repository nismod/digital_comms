"""Plotting

"""
import plotly.plotly as py
import plotly.graph_objs as go
import pandas as pd
import numpy as np

trace = go.Scatter( x=ex_Gfast['year_completed'], y=ex_Gfast['all_premises_y'] )
data = [trace]
url = py.plot(data, filename='ex_Gfast_time-series')

trace = go.Scatter( x=ex_FTTdp['year_completed'], y=ex_FTTdp['all_premises_y'] )
data = [trace]
url = py.plot(data, filename='ex_FTTdp_time-series')

trace = go.Scatter( x=ex_FTTH['year_completed'], y=ex_FTTH['all_premises_y'] )
data = [trace]
url = py.plot(data, filename='ex_FTTH_time-series')