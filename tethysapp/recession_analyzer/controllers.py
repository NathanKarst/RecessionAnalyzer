from tethys_sdk.gizmos import DatePicker, MapView, MVLayer, MVView, TextInput, Button, ButtonGroup, LinePlot, ScatterPlot
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .model import TimeSeries, getRecessions


@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    gages  = TextInput(name='gages', display_text='Gage', initial='11477000')      

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
        start = request.POST['start']
        stop = request.POST['stop']
        
        ts = TimeSeries(gageName[0],start,stop)
        rec = getRecessions(gageName,ts)
        
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
            'type': 'datetime',
            },
        
        series=[{
               'name': gageName,
               'color': '#0066ff',
               'marker': {'enabled': False},
               'data': zip(ts.time,ts.discharge),
               'dateTimeLabelFormats':{'second':'%Y'},
               }]
        )
        
        scatter_plot_view = ScatterPlot(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Recession Parameters',
        spline=True,
        x_axis_title='log(a)',
        y_axis_title='b',
        x_axis_units = '[]',
        y_axis_units = '[]',
        xAxis = {'type':'logarithmic'},
        series=[{
               'name': gageName,
               'color': '#0066ff',
               'data': zip(rec.A,rec.B),
               'dateTimeLabelFormats':{'second':'%Y'},
               }]
        )

    context = {'start': start, 'stop':stop, 'gages': gages, 'buttons': horizontal_buttons, 'line_plot_view':line_plot_view, 'scatter_plot_view':scatter_plot_view}

    return render(request, 'recession_analyzer/home.html', context)