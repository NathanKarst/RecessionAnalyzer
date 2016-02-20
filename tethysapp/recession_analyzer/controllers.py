from tethys_sdk.gizmos import DatePicker, MapView, MVLayer, MVView, TextInput, Button, ButtonGroup, LinePlot, ScatterPlot, ToggleSwitch, RangeSlider, TimeSeries
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .model import recessionExtract
import pandas as pd
import numpy as np
from .app import RecessionAnalyzer
import os
import cPickle as pickle

@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    gages_initial = '11477000'
    start_initial = '2000-01-01'
    stop_initial = '2015-01-01'
    concave_initial= False
    nonlinear_fitting_initial= False
    rec_sense_initial= 1
    min_length_initial= 4
    antecedent_moisture_initial = 1
    lag_start_initial = 0

    if request.POST:
        gages_initial = request.POST['gages_input']
        start_initial = request.POST['start_input']
        stop_initial = request.POST['stop_input']

        if 'concave_input' in request.POST:
            concave_initial=True;
        else:
            concave_initial=False;

        if 'nonlinear_fitting_input' in request.POST:
            nonlinear_fitting_initial=True;
        else:
            nonlinear_fitting_initial=False;

        rec_sense_initial=request.POST['rec_sense_input']
        min_length_initial=request.POST['min_length_input']
        antecedent_moisture_initial = request.POST['antecedent_moisture_input']
        lag_start_initial = request.POST['lag_start_input']




    gages_options  = TextInput(name='gages_input', display_text='Gage', initial=gages_initial,attributes={'size':15})

    start_options = DatePicker(name='start_input',
                                            display_text='Start date',
                                            autoclose=True,
                                            format='yyyy-m-d',
                                            start_date='01/01/1910',
                                            initial=start_initial)
    stop_options = DatePicker(name='stop_input',
                                            display_text='Stop date',
                                            autoclose=True,
                                            format='yyyy-m-d',
                                            start_date='01/01/1910',
                                            initial=stop_initial)


    concave_options = ToggleSwitch(name='concave_input', size='small', initial=concave_initial, display_text='Concave recessions')

    nonlinear_fitting_options = ToggleSwitch(name='nonlinear_fitting_input', display_text='Nonlinear fitting',size='small',initial = nonlinear_fitting_initial)
    
    min_length_options = RangeSlider(name='min_length_input', min=4, max=10, initial=min_length_initial, step=1,attributes={"onchange":"showValue(this.value,'min_length_initial');"})
    
    rec_sense_options = RangeSlider(name='rec_sense_input', min=0, max=1, initial=rec_sense_initial, step=0.01,
                           attributes={"onchange":"showValue(this.value,'rec_sense_initial');"})

    antecedent_moisture_options = RangeSlider(name='antecedent_moisture_input', min=0, max=1, initial=antecedent_moisture_initial, step=0.01,attributes={"onchange":"showValue(this.value,'antecedent_moisture_initial');"})

    lag_start_options = RangeSlider(name='lag_start_input', min=0, max=3, initial=lag_start_initial, step=1,attributes={"onchange":"showValue(this.value,'lag_start_initial');"})

    submitted=''

    if request.POST:
        app_workspace = RecessionAnalyzer.get_user_workspace(request.user)
        new_file_path = os.path.join(app_workspace.path,'current_plot.txt')

        pickle.dump(request.POST, open(new_file_path[:-4] + '.p','w'))

        #with open(new_file_path,'w') as a_file:
        #    poststring = request.POST['gages_input']+'\n' + request.POST['start_input']+','+request.POST['stop_input']+','+request.POST['rec_sense_input']+','+request.POST['min_length_input']+','+request.POST['antecedent_moisture_input']+','+request.POST['lag_start_input']+','+str(nonlinear_fitting_initial)+','+str(concave_initial)
        #    a_file.write(poststring)

        submitted='submitted'


    context = {'start_options': start_options,
               'rec_sense_initial':rec_sense_initial,
               'antecedent_moisture_initial':antecedent_moisture_initial,
               'lag_start_initial':lag_start_initial,
               'min_length_initial':min_length_initial,
                'stop_options':stop_options,
                'gages_options' : gages_options,
                'concave_options': concave_options,
                'nonlinear_fitting_options':nonlinear_fitting_options,
                'min_length_options':min_length_options,
                'submitted':submitted,
                'antecedent_moisture_options':antecedent_moisture_options,
                'lag_start_options':lag_start_options,
                'rec_sense_options':rec_sense_options}

    return render(request, 'recession_analyzer/home.html', context)

def results(request):
    '''
    Controller for results plotting page
    '''
    app_workspace = RecessionAnalyzer.get_user_workspace(request.user)
    new_file_path = os.path.join(app_workspace.path,'current_plot.txt')
    with open(new_file_path,'r') as a_file:
        textFileLines = a_file.readlines()

    ## load the pickled POST dictionary from the user workspace
    post = pickle.load(open(new_file_path[:-4] + '.p','r'))
    
    gageName    = post['gages_input']
    start       = post['start_input']
    stop        = post['stop_input']
    rec_sense   = post['rec_sense_input']
    min_length  = post['min_length_input']
    ante_moist  = post['antecedent_moisture_input']
    lag_start   = post['lag_start_input']
    
    # if these aren't selected in the original form, then a value won't be saved in the 
    # POST dictionary, so we have to handle them a bit differently. 
    nonlin_fit  = post.get('nonlinear_fitting_input',False)     
    concave     = post.get('concave_input', False)              

    #gageName = textFileLines[0].split('\n');
    #gageName = gageName[0].split(',')
    #print 'Old way:' + str(gageName)
    #params = textFileLines[1].split(',')
    #start = params[0]; stop = params[1];
    #rec_sense=params[2]; min_length=params[3];
    #ante_moist=params[4];
    #lag_start=params[5];
    #fit = params[6]; concave = params[7];

    min_length = float(min_length)
    selectivity = float(rec_sense)*500
    ante=10
    window=3
    #sitesDict = recessionExtract(gageName,start,stop)
    sitesDict = recessionExtract([gageName], start,stop,ante=10, alph=0.90, window=3, selectivity=selectivity, minLen=min_length, option=1, lin=1)


    ts = sitesDict[gageName]
    flow = ts[gageName].values;
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
           'name': ['Gage number: ' + gageName],
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
