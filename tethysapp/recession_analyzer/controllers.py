from tethys_sdk.gizmos import DatePicker, MapView, MVLayer, MVView, TextInput, Button, ButtonGroup, LinePlot, ScatterPlot, ToggleSwitch, RangeSlider, TimeSeries
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .model import recessionExtract
import pandas as pd
import numpy as np
from .app import RecessionAnalyzer
import os


@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    gages  = TextInput(name='gages', display_text='Gage', initial='11477000',attributes={'size':15})

    start = DatePicker(name='start',
                                            display_text='Start date',
                                            autoclose=True,
                                            format='yyyy-m-d',
                                            start_date='01/01/1910',
                                            initial='2000-01-01')
    stop = DatePicker(name='stop',
                                            display_text='Stop date',
                                            autoclose=True,
                                            format='yyyy-m-d',
                                            start_date='01/01/1910',
                                            initial='2015-01-01')  
                                            
                                                                           
    concave_down_toggle = ToggleSwitch(name='concave_down_toggle', size='mini', display_text='Concave recessions')

    fitting = ToggleSwitch(name='fitting', display_text='Nonlinear fitting',size='mini')
    
    min_length = RangeSlider(name='min_length', min=4, max=10, initial=4, step=1,attributes={"onchange":"showValue(this.value,'min_length');"})
    
    rec_sens = RangeSlider(name='rec_sens', min=0, max=1, initial=1, step=0.01,
                           attributes={"onchange":"showValue(this.value,'rec_sense');"})

    antecedent_moisture = RangeSlider(name='antecedent_moisture', min=0, max=1, initial=1, step=0.01,attributes={"onchange":"showValue(this.value,'antecedent_moisture');"})

    lag_start = RangeSlider(name='lag_start', min=0, max=3, initial=0, step=1,attributes={"onchange":"showValue(this.value,'lag_start');"})

    submitted=''

    if request.POST:
        app_workspace = RecessionAnalyzer.get_user_workspace(request.user)
        new_file_path = os.path.join(app_workspace.path,'current_plot.txt')
        concave = 'nonconcave'
        fit='linfit'

        if request.POST.get('concave_down_toggle'):
            concave = 'concave'
        if request.POST.get('fitting'):
            fit='nonlinfit'


        with open(new_file_path,'w') as a_file:
            poststring = request.POST['gages']+'\n' + request.POST['start']+','+request.POST['stop']+','+request.POST['rec_sens']+','+request.POST['min_length']+','+request.POST['antecedent_moisture']+','+request.POST['lag_start']+','+fit+','+concave
            a_file.write(poststring)

        submitted='submitted'


    context = {'start': start, 
                'stop':stop, 
                'gages': gages,
                'concave_down_toggle': concave_down_toggle,
                'fitting':fitting,
                'min_length':min_length,
                'submitted':submitted,
                'antecedent_moisture':antecedent_moisture,
                'lag_start':lag_start,
                'rec_sens':rec_sens}

    return render(request, 'recession_analyzer/home.html', context)

def results(request):
    '''
    Controller for results plotting page
    '''
    app_workspace = RecessionAnalyzer.get_user_workspace(request.user)
    new_file_path = os.path.join(app_workspace.path,'current_plot.txt')
    with open(new_file_path,'r') as a_file:
        textFileLines = a_file.readlines()


    gageName = textFileLines[0].split('\n');
    gageName = gageName[0].split(',')
    params = textFileLines[1].split(',')
    start = params[0]; stop = params[1];
    rec_sense=params[2]; min_length=params[3];
    antecedent_moisture=params[4];
    lag_start=params[5];
    fit = params[6]; concave = params[7];

    min_length = float(min_length)
    selectivity = float(rec_sense)*500
    ante=10
    window=3
    #sitesDict = recessionExtract(gageName,start,stop)
    sitesDict = recessionExtract(gageName, start,stop,ante=10, alph=0.90, window=3, selectivity=selectivity, minLen=min_length, option=1, lin=1)


    ts = sitesDict[gageName[0]]
    flow = ts[gageName[0]].values;
    data = zip(ts.index,flow)

    print(gageName)

    line_plot_view = TimeSeries(
    height='250px',
    width='250px',
    engine='highcharts',
    title='Flow Time Series',
    spline=True,
    x_axis_title='Time',
    y_axis_title='Flow',
    y_axis_units='cfs',
    series=[{
           'name': ['Gage number: ' + gageName[0]],
           'data': data,
           }]
    )


    avals = ts['A0n'][ts['A0n'] > 0 ].values;
    bvals = ts['Bn'][ts['Bn']>0].values;
    tuplelist=[];
    for i in np.arange(len(avals)):
        tuplelist.append((avals[i],bvals[i]))





    scatter_plot_view = ScatterPlot(
    height='250px',
    width='250px',
    engine='highcharts',
    title='Recession Parameters',
    spline=True,
    x_axis_title='loga',
    y_axis_title='b',
    x_axis_units = '[]',
    xAxis = {'type':'logarithmic'},
    y_axis_units = '[]',
    series=[{
           'name': gageName,
           'data': tuplelist ,
           }]
    )

    context = {
            'line_plot_view':line_plot_view,
            'scatter_plot_view':scatter_plot_view
           }
    return render(request, 'recession_analyzer/results.html', context)
