# Put your persistent store models in this file
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float
from sqlalchemy.orm import sessionmaker


import pandas as pd
import numpy as np
import urllib
from io import StringIO
from numpy import NaN, Inf, arange, isscalar, asarray, array
import sys
from scipy import stats as sp
from scipy import optimize as op


        
def recessionExtract(sites, start,stop,ante=10, alph=0.90, window=3, selectivity=100, minLen=5, option=1, lin=1):
    sitesDict = {};
    for site in sites:
        d = getTimeSeries(site,start,stop)
        dateandtime=pd.to_datetime(d['Time'])
        d = pd.DataFrame(d['Discharge'].values,columns=[site],index=pd.DatetimeIndex(dateandtime))
        selector = (d[site].max()-d[site].min())/selectivity;
        print(selector)
        [maxtab, mintab]=peakdet(d[site], selector);

        #initialize peaks
        d['peaks']=-1;

        #get rid of peaks too close to the start

        if ante>2:
            maxtab = maxtab[maxtab[:,0].astype(int)>ante];
        else:
            maxtab = maxtab[maxtab[:,0].astype(int)>1];


        d.ix[maxtab[:,0].astype(int),'peaks']=maxtab[:,1];

        d['smooth']= pd.rolling_mean(d[site],window); d['smooth'][0:2] = d[site][0:2];
        d['Dunsmooth']= d[site].diff().shift(-1);
        d['DDsmooth']=d['smooth'].diff().shift(-1).diff().shift(-1);
        d['DDunsmooth'] = d[site].diff().shift(-1).diff().shift(-1);
        d = d[:-2];

        #boolean vector for recession periods
        if option==0:
            d['choose']=d['Dunsmooth']<0;
        else:
            d['choose']=(d['Dunsmooth']<0) & ((d['DDsmooth']>=0)|(d['DDunsmooth']>=0));

        #each peak should have associated with it an API, an An, A0n, Bn, A, A0, B
        #an rsqn, and an rsq. Loop through all peaks, compute each parameter

        datesMax = d.ix[d['peaks']>0].index;

        d['An']=np.nan; d['Bn']=np.nan; d['A0n']=np.nan; d['api']=np.nan;
        for i in np.arange(len(datesMax)-1):
            recStart = datesMax[i]; peak1 = datesMax[i]+pd.DateOffset(days=1); peak2 = datesMax[i+1];
            recEnd = d[peak1:peak2][d[peak1:peak2]['choose']==False].index[0];
            if len(d[recStart:recEnd])<minLen:
                continue;

            t = np.arange(len(d[site][recStart:recEnd]));
            q0 = d[site][recStart];
            if lin==1:
                ab=fitRecession(t,d[site][recStart:recEnd])

                afit=ab[0];
                bfit=ab[1];
                if bfit>=1 and bfit<10 and afit > 0 and afit<1000:
                    d['An'][recStart] = afit; d['Bn'][recStart]=bfit;
                    beforeRec = d[site][recStart-pd.DateOffset(days=ante):recStart];
                    beforeRec = beforeRec[::-1]
                    factor = alph**np.arange(len(beforeRec))
                    api = np.sum(beforeRec*factor)
                    d['api'][recStart] = api
            else:
                def func(t, a, r):
                    return (q0**(r)-a*r*t)**(1/r)
                try:
                    popt, cov = op.curve_fit(func,t,d[site][recStart:recEnd]);
                except RuntimeError:
                    continue;
                afit = popt[0]; bfit = 1-popt[1];
                if bfit>=1 and bfit<10:
                    d['An'][recStart] = afit; d['Bn'][recStart]=bfit;
                    beforeRec = d[site][recStart-pd.DateOffset(days=ante):recStart];
                    beforeRec = beforeRec[::-1]
                    factor = alph**np.arange(len(beforeRec))
                    pi = np.sum(beforeRec*factor)
                    d['api'][recStart] = api


        notAn = d['An'][~np.isnan(d['An'])];
        notBn = d['Bn'][~np.isnan(d['Bn'])];

        ag = sp.gmean(notAn)
        exponent = np.sum((notBn-np.mean(notBn))*np.log10(notAn/ag))/sum((notBn-np.mean(notBn))**2)
        qscale = 10**(-exponent)
        d['A0n'][~np.isnan(d['An'])]=d['An'][~np.isnan(d['An'])]*qscale**(d['Bn'][~np.isnan(d['An'])]-1)
        sitesDict[site]=d;
    return sitesDict

def fitRecession(time,discharge):
    """ INPUTS: time [numpy array]
                discharge [numpy array]
    
        OUTPUTS: recession parameter (a,b) pair
    
        This is a very simple fitting procedure, but it can easily be superceded.
    """
    dq = np.diff(discharge)
    p = np.polyfit(np.log(discharge[1:]),np.log(-dq),1)
    return (np.exp(p[1]),p[0]) #(a,b)
    
def BergnerZouhar(A,B):
    """ INPUTS: A, B [numpy arrays
        OUTPUTS: a [numpy array]
    
        a is the scaled version of A such that log(a) and B are linearly uncorrelated
        Note: I've numerically tested that the correlation is actually removed.
    """
    num = -np.sum((B - np.mean(B))*(np.log(A) - np.mean(np.log(A))))
    den = np.sum((B - np.mean(B))**2)
    q0 = np.exp(num/den)
    print(A*q0**(B-1) )
    return A*q0**(B-1)




def peakdet(v, delta, x = None):
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html

    Returns two arrays

    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.

    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.

    """
    maxtab = []
    mintab = []

    if x is None:
        x = arange(len(v))

    v = asarray(v)

    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')

    if not isscalar(delta):
        sys.exit('Input argument delta must be a scalar')

    if delta <= 0:
        sys.exit('Input argument delta must be positive')

    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN

    lookformax = True

    for i in arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]

        if lookformax:
            if this < mx-delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True

    return array(maxtab), array(mintab)

def getTimeSeries(gage,start,stop):
    dataparse = lambda x: pd.datetime.strptime(x, '%Y-%m-%d')
    response = urllib.request.urlopen('http://waterdata.usgs.gov/nwis/dv?cb_00060=on&format=rdb&site_no=' + gage + '&referred_module=sw&period=&begin_date='+start+'&end_date='+stop)
    print(response)
    tsv = response.read().decode("utf8")
    tsv = StringIO(tsv)
    df = pd.read_csv(tsv,sep='\t',header=26,index_col=False,parse_dates=[2],date_parser=dataparse,skiprows=[27])
    df.columns = ['Agency','Site','Time','Discharge','DischargeQualification']
    df = df[df.DischargeQualification=='A']
    return df