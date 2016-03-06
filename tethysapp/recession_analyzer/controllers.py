from tethys_sdk.gizmos import DatePicker, MapView, MVLayer, MVView, TextInput, Button, ButtonGroup, LinePlot, ScatterPlot, ToggleSwitch, RangeSlider, TimeSeries, PlotView, SelectInput
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .model import recessionExtract, createAbJson
import pandas as pd
import numpy as np
from .app import RecessionAnalyzer
import os
import cPickle as pickle
import simplejson as json

import urllib
from io import StringIO


@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    testString = 'fubar'
    gages_initial = '11477000'
    start_initial = '2000-01-01'
    stop_initial = '2015-01-01'
    concave_initial= False
    nonlinear_fitting_initial= False
    rec_sense_initial= 1
    min_length_initial= 4
    antecedent_moisture_initial = 1
    lag_start_initial = 0
    abJson='';

    #if submitting parameters and doing analysis,
    #but not submitting a site from the dropdown menu
    #make sure to persist the values in the sliders/etc
    if request.POST and 'site_submit' not in request.POST:
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

    #if submitting a new site with the dropdown menu
    #should also persist the data, but use the
    #stored post from the initial submit
    if request.POST and 'site_submit' in request.POST:
        app_workspace = RecessionAnalyzer.get_user_workspace(request.user)
        new_file_path = os.path.join(app_workspace.path,'current_plot.txt')
        post = pickle.load(open(new_file_path[:-4] + '.p','r'))
        gages_initial       = post['gages_input']
        start_initial       = post['start_input']
        stop_initial        = post['stop_input']
        rec_sense_initial   = post['rec_sense_input']
        min_length_initial  = post['min_length_input']
        ante_moist_initial  = post['antecedent_moisture_input']
        lag_start_initial   = post['lag_start_input']
        nonlin_fit_initial  = post.get('nonlinear_fitting_input',False)
        concave_initial     = post.get('concave_input', False)


    #checkGageExistence(gages_initial)

    #initialize options for all the sliders, plots, etc
    ##################################################
    ##################################################
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

    ## initialize empty plots
    scatter_plot_view = buildRecParamPlot([])
    line_plot_view = buildFlowTimeSeriesPlot([])


    select_input_options = SelectInput(display_text='Select gage',
                            name='select_input',
                            multiple=False,
                            options=[],
                            initial=[],
                            original=[])



    #"Analyze recessions" button has been pressed
    # this stores new set of analysis parameters
    # and performs recession analysis, stores data in dictionaries
    # creates a new dropdown box with user gages
    if request.POST and 'submit_button' in request.POST:
        app_workspace = RecessionAnalyzer.get_user_workspace(request.user)
        new_file_path = os.path.join(app_workspace.path,'current_plot.txt')
        pickle.dump(request.POST, open(new_file_path[:-4] + '.p','w'))
        post = pickle.load(open(new_file_path[:-4] + '.p','r'))
        submitted='submitted'
        gageNames   = post['gages_input'].split(',')
        start       = post['start_input']
        stop        = post['stop_input']
        rec_sense   = post['rec_sense_input']
        min_length  = post['min_length_input']
        ante_moist  = post['antecedent_moisture_input']
        lag_start   = post['lag_start_input']


        nonlin_fit  = post.get('nonlinear_fitting_input',False)
        concave     = post.get('concave_input', False)

        min_length = float(min_length)
        selectivity = float(rec_sense)*500
        ante=10
        window=3

        sitesDict, startStopDict = recessionExtract(gageNames, start,stop,ante=10, alph=0.90, window=3, selectivity=selectivity, minLen=min_length, option=1, nonlin_fit=nonlin_fit)

        abJson = createAbJson(sitesDict,gageNames);


        new_file_path = os.path.join(app_workspace.path,'current_dict.p')
        pickle.dump(sitesDict, open(new_file_path,'w'))

        new_file_path = os.path.join(app_workspace.path,'current_startStop.p')
        pickle.dump(startStopDict, open(new_file_path,'w'))

        gageName = gageNames[0]
        ts = sitesDict[gageName]
        startStop = startStopDict[gageName]
        startVec = startStop[0]
        endVec = startStop[1]
        flow = ts[gageName];
        tsinds = ts.index
        data = zip(tsinds,flow);


        ##################TESTING REC/NOTREC plot
        series = [];
        #build recessions

        series.append({'name':' ','color':'#0066ff',
                           'data':zip(flow[tsinds[0]:startVec[0]].index,flow[tsinds[0]:startVec[0]])})
        series.append({'name':' ','color':'#ff6600',
                           'data':zip(flow[startVec[0]:endVec[0]].index,flow[startVec[0]:endVec[0]])})
        for i in np.arange(0,len(startVec)-1):
            series.append({'name':' ','color':'#0066ff',
                           'data':zip(flow[endVec[i]:startVec[i+1]].index,flow[endVec[i]:startVec[i+1]])})
            series.append({'name':' ','color':'#ff6600',
                           'data':zip(flow[startVec[i+1]:endVec[i+1]].index,flow[startVec[i+1]:endVec[i+1]])})

        series.append({'name':' ','color':'#0066ff',
                           'data':zip(flow[endVec[-1]:tsinds[-1]].index,flow[endVec[-1]:tsinds[-1]])})

        optionsTuples = zip(gageNames,gageNames)


        select_input_options = SelectInput(display_text='Select gage',
                            name='select_input',
                            multiple=False,
                            initial=[gageName],
                            options=optionsTuples,
                            attributes={"onchange":"updatePlot(this.value);"})

        line_plot_view = buildFlowTimeSeriesPlot(series)

        avals = ts['A0n'][ts['A0n'] > 0 ].values;
        bvals = ts['Bn'][ts['Bn']>0].values;
        tuplelist = zip(avals,bvals)

        scatter_plot_view = buildRecParamPlot(tuplelist)
        

    #This updates the HIGHCHART when a gage is selected from the drop down
    # menu...does not perform any new analyses, simply loads data
    #stored in workspace from original analysis
    if request.POST and 'site_submit' in request.POST:

        app_workspace = RecessionAnalyzer.get_user_workspace(request.user)
        new_file_path = os.path.join(app_workspace.path,'current_plot.txt')
        post = pickle.load(open(new_file_path[:-4] + '.p','r'))
        new_file_path = os.path.join(app_workspace.path,'current_dict.p')
        sitesDict = pickle.load(open(new_file_path,'r'))

        new_file_path = os.path.join(app_workspace.path,'current_startStop.p')
        startStopDict = pickle.load(open(new_file_path,'r'))

        submitted='submitted'

        gageName = request.POST['select_input']

        ts = sitesDict[gageName]
        startStop = startStopDict[gageName]
        startVec = startStop[0]
        endVec = startStop[1]
        flow = ts[gageName];
        tsinds = ts.index
        data = zip(tsinds,flow);
        series = [];

        series.append({'name':' ','color':'#0066ff',
                           'data':zip(flow[tsinds[0]:startVec[0]].index,flow[tsinds[0]:startVec[0]])})
        series.append({'name':' ','color':'#ff6600',
                           'data':zip(flow[startVec[0]:endVec[0]].index,flow[startVec[0]:endVec[0]])})
        for i in np.arange(0,len(startVec)-1):
            series.append({'name':' ','color':'#0066ff',
                           'data':zip(flow[endVec[i]:startVec[i+1]].index,flow[endVec[i]:startVec[i+1]])})
            series.append({'name':' ','color':'#ff6600',
                           'data':zip(flow[startVec[i+1]:endVec[i+1]].index,flow[startVec[i+1]:endVec[i+1]])})

        series.append({'name':' ','color':'#0066ff',
                           'data':zip(flow[endVec[-1]:tsinds[-1]].index,flow[endVec[-1]:tsinds[-1]])})

        gageNames    = post['gages_input'].split(',')

        optionsTuples = zip(gageNames,gageNames)

        select_input_options = SelectInput(display_text='Select gage',
                            name='select_input',
                            multiple=False,
                            initial=[gageName],
                            options=optionsTuples,
                            attributes={"onchange":"updatePlot(this.value);"})

        line_plot_view = buildFlowTimeSeriesPlot(series)


        avals = ts['A0n'][ts['A0n'] > 0 ].values;
        bvals = ts['Bn'][ts['Bn']>0].values;
        tuplelist = zip(avals,bvals)
        
        scatter_plot_view = buildRecParamPlot(tuplelist)

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
                'rec_sense_options':rec_sense_options,
               'line_plot_view':line_plot_view,
               'scatter_plot_view':scatter_plot_view,
               'select_input_options':select_input_options,
               'abJson':abJson
                }

    return render(request, 'recession_analyzer/home.html', context)


def checkGageExistence(gage):
    response = urllib.urlopen('http://waterservices.usgs.gov/nwis/site/?format=rdb&sites='+gage)

    tsv = response.read().decode('utf8')
    tsv = StringIO(tsv)

    # the read will fail if the gage is no valid
    try: df = pd.read_csv(tsv,sep='\t',header=29,index_col=False,skiprows=[30])
    except: return False

    # we only want stream gages
    if set(df.site_tp_cd) == set(['ST']): return True
    return False

def buildFlowTimeSeriesPlot(series):
    highcharts_object = {
        'chart': {
            'zoomType': 'x'
        },
        'title': {
            'text': 'Flow time series'
        },
        'legend': {
            'layout': 'vertical',
            'align': 'right',
            'verticalAlign': 'middle',
            'borderWidth': 0,
            'enabled': False
        },
        'xAxis': {
            'title': {
                'enabled': True,
                'text': 'time',
                'offset': 35
            },
            'type': 'datetime',
            'tickLength': 10
        },
        'yAxis': {
            'title': {
                'enabled': True,
                'text': 'Discharge [cfs]'
            }
        },
        'tooltip': {
            'pointFormat': '{point.y} cfs',
            'valueDecimals': 2,
            'xDateFormat': '%d %b %Y %H:%M'
        },
        'series': series}
    return PlotView(highcharts_object=highcharts_object,
                              width='100%',
                              height='300px',
                              attributes='id=hydrograph-plot')

def buildRecParamPlot(tuplelist):
    scatter_highchart = {
        'chart': {
            'type':'scatter',
            'zoomType': 'xy'
        },
        'title': {
            'text': 'Recession parameters'
        },
        'legend': {
            'layout': 'vertical',
            'align': 'right',
            'verticalAlign': 'middle',
            'borderWidth': 0,
            'enabled': False
        },
        'exporting': {
            'enabled':'true'
        },
        'tooltip': {
            'pointFormat':'b={point.y:,.2f}, a={point.x:,.2f}'
        },
        'xAxis': {
            'title': {
                'enabled': True,
                'text': 'a',
                'offset': 35
            },
            'type': 'logarithmic',
            'tickLength': 10
        },
        'yAxis': {
            'title': {
                'enabled': True,
                'text': 'b'
            }
        },
        'series': [{'name':' ','data':tuplelist}]}

    return PlotView(highcharts_object=scatter_highchart,
                              width='100%',
                              height='300px',
                              attributes='id=ab-scatter')


## DRALLE: CAN WE GET RID OF THIS NOW? IF SO, FEEL FREE TO DELETE.
def results(request):
    '''
    Controller for results plotting page
    '''
    app_workspace = RecessionAnalyzer.get_user_workspace(request.user)
    new_file_path = os.path.join(app_workspace.path,'current_plot.txt')
    #with open(new_file_path,'r') as a_file:
    #    textFileLines = a_file.readlines()

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
    sitesDict, startStopDict = recessionExtract([gageName], start,stop,ante=10, alph=0.90, window=3, selectivity=selectivity, minLen=min_length, option=1, nonlin_fit=nonlin_fit)

    ts = sitesDict[gageName]
    startStop = startStopDict[gageName]
    startVec = startStop[0]
    endVec = startStop[1]
    flow = ts[gageName];
    tsinds = ts.index
    data = zip(tsinds,flow);

    ##################TESTING REC/NOTREC plot
    series = [];
    #build recessions

    series.append({'name':' ','color':'#0066ff',
                       'data':zip(flow[tsinds[0]:startVec[0]].index,flow[tsinds[0]:startVec[0]])})
    series.append({'name':' ','color':'#ff6600',
                       'data':zip(flow[startVec[0]:endVec[0]].index,flow[startVec[0]:endVec[0]])})
    for i in np.arange(0,len(startVec)-1):
        series.append({'name':' ','color':'#0066ff',
                       'data':zip(flow[endVec[i]:startVec[i+1]].index,flow[endVec[i]:startVec[i+1]])})
        series.append({'name':' ','color':'#ff6600',
                       'data':zip(flow[startVec[i+1]:endVec[i+1]].index,flow[startVec[i+1]:endVec[i+1]])})

    series.append({'name':' ','color':'#0066ff',
                       'data':zip(flow[endVec[-1]:tsinds[-1]].index,flow[endVec[-1]:tsinds[-1]])})




    line_plot_view = TimeSeries(
    height='250px',
    width='250px',
    engine='highcharts',
    title='Flow Time Series',
    spline=True,
    x_axis_title='Time',
    y_axis_title='Flow',
    y_axis_units='cfs',
    series=series
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
