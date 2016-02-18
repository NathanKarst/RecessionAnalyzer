from tethys_sdk.gizmos import DatePicker, MapView, MVLayer, MVView, TextInput, Button, ButtonGroup, LinePlot, ScatterPlot, ToggleSwitch, RangeSlider
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .model import recessionExtract
import pandas as pd
import numpy as np


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
                                            
                                                                           
    concave_down_toggle = ToggleSwitch(name='concave_down_toggle', size='mini', display_text='Concave down recessions')

    fitting = ToggleSwitch(name='fitting', display_text='Nonlinear fitting',size='mini')
    
    min_length = RangeSlider(name='min_length', display_text='Minimum recession length', min=4, max=10, initial=4, step=1,attributes={'width':'40px'})
    
    rec_sens = RangeSlider(name='rec_sens', display_text='Recession detection sensitivity parameter', min=0, max=1, initial=1, step=0.01,
                           )

    antecedent_moisture = RangeSlider(name='min_length', display_text='Antecedent moisture parameter', min=0, max=1, initial=1, step=0.01)

    lag_start = RangeSlider(name='lag_start', display_text='Lag between max. obs. streamflow and defined rec. start', min=0, max=3, initial=0, step=1)


    run_button = Button(display_text='Run',
                        icon='glyphicon glyphicon-play',
                        style='success',
                        submit=True)
                        
    delete_button = Button(display_text='Delete',
                           icon='glyphicon glyphicon-trash',
                           disabled=True,
                           style='danger')
    
                           
    horizontal_buttons = ButtonGroup(buttons=[run_button, delete_button])

    line_plot_view = None
    scatter_plot_view = None
    if request.POST and 'gages' in request.POST:
        gageName = request.POST['gages'].split(',')
        gageName = [gageName[0].encode('ascii','ignore')]

        start = request.POST['start']
        stop = request.POST['stop']
        min_length = request.POST['min_length']
        selectivity = request.POST['rec_sens']*500
        ante=10
        window=3
        

        sitesDict = recessionExtract(gageName,start,stop)
        thekeys = list(sitesDict.keys())

        ts = sitesDict[gageName[0]]
        flow = ts[gageName[0]].values;
        thetime = np.arange(len(flow))

        line_plot_view = LinePlot(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Flow Time Series',
        spline=True,
        x_axis_title='Time',
        y_axis_title='Flow',
        y_axis_units='cfs',
        xAxis={
            'type': 'linear',
            },
        
        series=[{
               'name': gageName,
               'color': '#0066ff',
               'marker': {'enabled': False},
               'data': zip(thetime,ts[gageName[0]].values),
               }]
        )
        avals = ts['A0n'][ts['A0n'] > 0 ].values;
        bvals = ts['Bn'][ts['Bn']>0].values;
        tuplelist=[];
        for i in np.arange(len(avals)):
            tuplelist.append((avals[i],bvals[i]))





        scatter_plot_view = ScatterPlot(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Recession Parameters',
        spline=True,
        x_axis_title='log(a)',
        y_axis_title='b',
        x_axis_units = '[]',
        xAxis = {'type':'linear'},
        y_axis_units = '[]',
        series=[{
               'name': gageName,
               'color': '#0066ff',
               'data': tuplelist ,
               'dateTimeLabelFormats':{'second':'%Y'},
               }]
        )

    context = {'start': start, 
                'stop':stop, 
                'gages': gages, 
                'buttons': horizontal_buttons, 
                'line_plot_view':line_plot_view, 
                'scatter_plot_view':scatter_plot_view,
                'concave_down_toggle': concave_down_toggle,
                'fitting':fitting,
                'min_length':min_length,
                'antecedent_moisture':antecedent_moisture,
                'lag_start':lag_start,
                'rec_sens':rec_sens}

    return render(request, 'recession_analyzer/home.html', context)