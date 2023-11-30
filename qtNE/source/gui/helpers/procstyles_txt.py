import numpy as np
from scipy import signal
import scipy.ndimage as ndimage
import re
import collections
from scipy import interpolate


import qcodes
# from . import data_array
from qcodes_loop.data import data_array

## supporting functions for data processing

def create_kernel(x_dev, y_dev, cutoff, distr):
    distributions = {
        'gaussian': lambda r: np.exp(-(r**2) / 2.0),
        'exponential': lambda r: np.exp(-abs(r) * np.sqrt(2.0)),
        'lorentzian': lambda r: 1.0 / (r**2+1.0),
        'thermal': lambda r: np.exp(r) / (1 * (1+np.exp(r))**2)
    }
    func = distributions[distr]

    hx = np.floor((x_dev * cutoff) / 2.0)
    hy = np.floor((y_dev * cutoff) / 2.0)

    x = np.linspace(-hx, hx, int(hx * 2) + 1) / x_dev
    y = np.linspace(-hy, hy, int(hy * 2) + 1) / y_dev

    if x.size == 1: x = np.zeros(1)
    if y.size == 1: y = np.zeros(1)

    xv, yv = np.meshgrid(x, y)

    kernel = func(np.sqrt(xv**2+yv**2))
    kernel /= np.sum(kernel)

    # print(kernel)
    return kernel

def get_limits(x,y,z=[]):
    xmin, xmax = np.nanmin(x), np.nanmax(x)
    ymin, ymax = np.nanmin(y), np.nanmax(y)
    if z!=[]:
        zmin, zmax = np.nanmin(z), np.nanmax(z)

    # Thickness for 1d scans, should we do this here or
    # in the drawing code?
    if xmin == xmax:
        xmin, xmax = -1, 1

    if ymin == ymax:
        ymin, ymax = -1, 1

    return xmin, xmax, ymin, ymax, zmin, zmax


##

def f_identity(w):
    return w


def f_abs(w):
    """Take the absolute value of every datapoint."""
    w['name']='abs'

    wout = np.abs(w['ydata'])
    w['ydata'] = wout
    w['label']='abs('+w['processpar']+')'
    w['unit']='nA'
    
    return w



def f_log(w):
    """The base-10 logarithm of every datapoint."""
    w['name']='logarithm'
    
    # wout = np.log10(np.abs(w['ydata']))
    wout = np.log10(np.abs(w['ydata']),out=np.zeros_like(w['ydata']),where=(np.abs(w['ydata'])!=0))
    w['ydata'] = wout
    w['label']='log'+r'$_{10}$'+'(abs('+w['processpar']+'))'
    w['unit']='nA'
    
    return w



def f_xderiv(w,method,sigma):
    """Partial derivative along x axis"""

    try:
        # sigma=2    
        if method=='numerical':
            wout= np.diff(w['ydata'],axis=0)#,prepend=w['ydata'][0][0])
            wout=np.insert(wout,0,wout[0][0],axis=0)
        # wout.append(wout
        elif method=='smooth':
            wout = diffSmooth(w['ydata'], dy='y', sigma=sigma) # dy (str): direction to differentiate in; sigma (float):  parameter for gaussian filter kernel
        w['ydata'] = wout
        w['label']='d'+w['processpar']+'/dVx'
        w['unit']=r'$\mu$'+'Siemens'
    except:
        print('partial x: Cannot differentiate')
    
    return w



def f_yderiv(w,method,sigma):
    """Partial derivative along y axis"""

    try:
        # sigma=2    
        if method=='numerical':
            wout= np.diff(w['ydata'],axis=1)#,prepend=w['ydata'][0][0])
            wout=np.insert(wout,0,wout[0][0],axis=1)        
        elif method=='smooth':
            wout = diffSmooth(w['ydata'], dy='x', sigma=sigma) # dy (str): direction to differentiate in; sigma (float):  parameter for gaussian filter kernel
        w['ydata'] = wout
        w['label']='d'+w['processpar']+'/dVy'
        w['unit']=r'$\mu$'+'Siemens'
    except:
        print('partial y: Cannot differentiate')
    
    return w


def f_xintegrate(w):
    """Numerical integration - x axis."""
    if w['ydata'].ndim == 1: #if 1D 

        w['ydata'] = np.cumsum(w['ydata'])
        wout = w['ydata'] / abs(w['xdata'][0][0]-w['xdata'][0][1]) * 0.0129064037 
    else:

        if w['xdata'][1][0][0]!=w['xdata'][1][1][0]:
            sweepback=True
        else:
            sweepback=False

        wout=np.cumsum(w['ydata'],axis=0)

    if sweepback:
        for wcol in range(np.shape(w['ydata'])[0]):
            if wcol%2!=0:
                    wout[wcol]=np.array(list(reversed(wout[wcol])))

        wout = wout / abs(w['xdata'][1][0][0]-w['xdata'][1][0][1]) * 0.0129064037 

    w['label']='I.dV'
    w['unit']= r'$\mathrm{e}^2/\mathrm{h}$'
    
    w['ydata'] = wout
    return w


def f_yintegrate(w):
    """Numerical integration - y axis."""
    if w['ydata'].ndim == 1: #if 1D 
        print('Function not valid.')
        return
    else:

        if w['xdata'][1][0][0]!=w['xdata'][1][1][0]:
            sweepback=True
        else:
            sweepback=False

        wout=np.cumsum(w['ydata'],axis=1)

    if sweepback:
        for wcol in range(np.shape(w['ydata'])[0]):
            if wcol%2!=0:
                    wout[wcol]=np.array(list(reversed(wout[wcol])))

        wout = wout / abs(w['xdata'][1][0][0]-w['xdata'][1][0][1]) * 0.0129064037 

    w['label']='I.dV'
    w['unit']= r'$\mathrm{e}^2/\mathrm{h}$'
    
    w['ydata'] = wout
    return w



def f_lowpass(w, x_width=3, y_height=3, method='gaussian'):
    """Perform a low-pass filter."""
    kernel = create_kernel(x_width, y_height, 7, method)
    w['ydata'] = ndimage.filters.convolve(w['ydata'], kernel)
    w['ydata'] = np.ma.masked_invalid(w['ydata'])

    return w



def f_highpass(w, x_width=3, y_height=3, method='gaussian'):
    """Perform a high-pass filter."""
    kernel = create_kernel(x_width, y_height, 7, method)
    w['ydata'] = w['ydata'] - ndimage.filters.convolve(w['ydata'], kernel)
        # kernel = create_kernel(x_width, y_height, 7, method)
        # self.z = self.z - ndimage.filters.convolve(self.z, kernel)
    return w


def f_deriv(w,sigma):
    """Calculate the length of every gradient vector."""

    try:
        # sigma=2
        wout = diffSmooth(w['ydata'], dy='xy', sigma=sigma) # dy (str): direction to differentiate in; sigma (float):  parameter for gaussian filter kernel
        w['ydata'] = wout
        w['label']='d'+w['processpar']+'/dV'
        w['unit']=r'$\mu$'+'Siemens'
    except:
        print('xy: Cannot differentiate')
    
    return w

def f_movavg(w,m,n):
    """Moving average filter."""
    # print('moving average')
    
    # (m, n) = (int(w['avg_m']), int(w['avg_n']))
    
    datac=w['ydata']
    if datac.ndim==1:
        win=np.ones((m,))
        win/=win.sum()
        wout=signal.convolve(w['ydata'], win, mode='same')
        # wout=moving_average_1d(w['ydata'],win)
    else:
        win=np.ones((m,n))
        win/=win.sum()
        wout=signal.convolve2d(w['ydata'], win, mode='same', boundary='symm')
        # wout=moving_average_2d(w['ydata'],win)    
    
    w['ydata'] = wout
    return w

def f_savgol(w,samples,order,deriv):
    """Savitsky-Golay filter."""
    # print('savgol')
    
    nanvalues= np.isnan(w['ydata'])
    w['ydata'][nanvalues]=0
    print(nanvalues)
    deltay = abs(w['ydata'][0][0]-w['ydata'][0][1]) / 0.0129064037
    print(deltay)
    
    # try:
    wout = signal.savgol_filter(w['ydata'], int(samples), int(order), int(deriv), delta = deltay)
    # except:
        # print('Error smoothing. Check: samples must be odd and smaller than array')
        # wout=w['ydata']
    w['ydata'] = wout
    return w

def offset(w,value):

    w['ydata'] = w['ydata'] - value*np.ones(np.shape(w['ydata'])) 
    w['label']=w['processpar']+'-'+str(value)
    # w['unit']='nA'
    return w

def remove_bg_line(w,axis):
    # add smoothing 
    data=w['ydata']
    # print('_____in')
    # print(w['ydata'][0])
    

    if axis=='y':
        line_avg=np.zeros(np.shape(data)[1])
        count_avg=0
        for data_line in data:
            if not any(np.isnan(data_line)):
                count_avg+=1
                line_avg+=data_line #/np.shape(w['ydata'])[0]
        line_avg=line_avg/count_avg
        data_sub = data - np.array(line_avg)
        w['ydata'] = data_sub
        #w['ydata']-=line_avg

    elif axis=='x':
        x_line_avg=np.zeros(np.shape(data)[0])
        count_avg=np.zeros(np.shape(data)[0])
        element_avg=np.zeros(np.shape(data)[0])

        for row in list(zip(*data)): # [b[row] for b in a]
            for element,element_ind in zip(row,range(len(row)-1)):
                if not np.isnan(element):
                    count_avg[element_ind]+=1
                    element_avg[element_ind]+=element

        x_line_avg=element_avg/count_avg


        data_sub=[]

        for line_ind in range(np.shape(data)[0]):
            dataadd = data[line_ind] - np.ones(np.shape(data)[1])*x_line_avg[line_ind]
            data_sub.append(dataadd)

        w['ydata'] = data_sub

        # print('_____out')
        # print(w['ydata'][0])

    return w
    
    
def f_deinterlace(w,indices):
    """Deinterlace."""

    z=[]
    
    if w['xdata'][1][0][0]!=w['xdata'][1][1][0]:
        sweepback=True
    else:
        sweepback=False

    if indices=='odd':
        for ii in range(0,np.shape(w['ydata'])[0]):
            zarray=[]
            if ii%2!=0:
                for jj in range(0,np.shape(w['ydata'])[1]):
                    zarray.append(w['ydata'][ii,jj])
            else:
                try:
                    zarray.append(w['ydata'][ii+1,0])
                    for jj in range(1,np.shape(w['ydata'])[1]):
                        zarray.append(w['ydata'][ii+1,jj])
                except:
                    for jj in range(0,np.shape(w['ydata'])[1]):
                        zarray.append(w['ydata'][ii-1,0])
                if sweepback:
                    zarray=list(reversed(zarray))
            z.append(np.array(zarray))

        wout=np.array(z)

    elif indices=='even':
        for ii in range(0,np.shape(w['ydata'])[0]):
            zarray=[]
            if ii%2==0:
                for jj in range(0,np.shape(w['ydata'])[1]):
                    zarray.append(w['ydata'][ii,jj])
            else:
                try:
                    zarray.append(w['ydata'][ii+1,0])
                    for jj in range(1,np.shape(w['ydata'])[1]):
                        zarray.append(w['ydata'][ii+1,jj])
                except:
                    for jj in range(0,np.shape(w['ydata'])[1]):
                        zarray.append(w['ydata'][ii-1,0])
                if sweepback:
                    zarray=list(reversed(zarray))
            # print(zarray)
            z.append(np.array(zarray))

        wout=np.array(z)

    w['ydata'] = wout
    
    return w







## -------------- not in use


def f_integrate(w):
    """Numerical integration."""
    if w['ydata'].ndim == 1: #if 1D 

        w['ydata'] = np.cumsum(w['ydata'])
        wout = w['ydata'] / abs(w['xdata'][0][0]-w['xdata'][0][1]) * 0.0129064037 
    else:

        if w['xdata'][1][0][0]!=w['xdata'][1][1][0]:
            sweepback=True
        else:
            sweepback=False

        wout=np.cumsum(w['ydata'],axis=0)
        wout=np.cumsum(wout,axis=1)
    if sweepback:
        for wcol in range(np.shape(w['ydata'])[0]):
            if wcol%2!=0:
                    wout[wcol]=np.array(list(reversed(wout[wcol])))

        wout = wout / abs(w['xdata'][1][0][0]-w['xdata'][1][0][1]) * 0.0129064037 

    w['label']='I.dV'
    w['unit']= r'$\mathrm{e}^2/\mathrm{h}$'
    
    w['ydata'] = wout
    return w

        





    
    
## -----------------------------------------------------------------
def uniqueArrayName(dataset, name0):
    """ Generate a unique name for a DataArray in a dataset """
    ii = 0
    name = name0
    while name in dataset.arrays:
        name = name0 + '_%d' % ii
        ii = ii + 1
        if ii > 1000:
            raise Exception('too many arrays in DataSet')
    return name



def getEmptyWrap():
    w={'processpar': 'measured',
       'xdata': [],
       'ydata': [],
       'label': [],
       'unit': [],
       'name': []
       }
    return w


def processStyle_queue(function_queue,dataa,partoprocess):
    meas_arr_name = dataa.default_parameter_name(partoprocess)
    meas_array = dataa.arrays[meas_arr_name]
    
    w=getEmptyWrap()
    w['processpar']=partoprocess
    w['ydata']=meas_array.ndarray
    w['xdata']=list(meas_array.set_arrays)
    # print(type(w['xdata']) is tuple)  
    w['label']=getattr(meas_array,'label')
    w['unit']=getattr(meas_array,'unit')

    for function in function_queue:
        func=function_queue[function][0]
        dataout=func(w,**function_queue[function][1]) # executes style function, outputs dataout (wrapper)
        w=dataout

    # --- defines name of new data array with processed data and adds it to the original dataset 
    name='proc_'
    name = uniqueArrayName(dataa, name)
    # try:
    data_arr = data_array.DataArray(name=name, 
                                    label=dataout['label'],
                                    unit=dataout['unit'], 
                                    array_id=dataout['processpar']+'_'+name, 
                                    set_arrays=tuple(w['xdata']),
                                    preset_data=dataout['ydata'],
                                    full_name=name)
    # except:
    #     print('problem with qcodes DataArray')
    #     data_arr = data_array.DataArray(name=name, 
    #                         label=dataout['label'],
    #                         unit=dataout['unit'], 
    #                         array_id=dataout['processpar']+'_'+name, 
    #                         set_arrays=tuple(w['xdata']),
    #                         preset_data=dataout['ydata'],
    #                         full_name=name)
    dataa.add_array(data_arr)
  
    return dataa
    
    
## -- support functions 


def diffSmooth(im, dy='x', sigma=2): # from qtt.utilities.tools
    """ Simple differentiation of an image.

    Args:
        im (array): input image.
        dy (string or integer): direction of differentiation. can be 'x' (0) or 'y' (1) or 'xy' (2) or 'g' (3).
        sigma (float): parameter for gaussian filter kernel.

    """
    if sigma is None:
        imx = diffImage(im, dy)
        return imx

    if dy is None:
        imx = im.copy()
    elif dy == 0 or dy == 'x':
        if len(im.shape)==1:
            raise Exception(f'invalid parameter dy={dy} for 1D image')
        else:
            imx = ndimage.gaussian_filter1d(im, axis=1, sigma=sigma, order=1, mode='nearest')
    elif dy == 1 or dy == 'y':
        imx = ndimage.gaussian_filter1d(im, axis=0, sigma=sigma, order=1, mode='nearest')
    elif dy == -1:
        imx = -ndimage.gaussian_filter1d(im, axis=0,
                                         sigma=sigma, order=1, mode='nearest')
    elif dy == 2 or dy == 3 or dy == 'xy' or dy == 'xmy' or dy == 'xmy2' or dy == 'g' or dy == 'x2my2' or dy == 'x2y2':
        if len(np.array(im).shape) != 2:
            raise Exception(f'differentiation mode {dy} cannot be combined with input shape {np.array(im).shape}')
        imx0 = ndimage.gaussian_filter1d(
            im, axis=1, sigma=sigma, order=1, mode='nearest')
        imx1 = ndimage.gaussian_filter1d(
            im, axis=0, sigma=sigma, order=1, mode='nearest')
        if dy == 2 or dy == 'xy':
            imx = imx0 + imx1
        if dy == 'xmy':
            imx = imx0 - imx1
        if dy == 3 or dy == 'g':
            imx = np.sqrt(imx0 ** 2 + imx1 ** 2)
        if dy == 'xmy2':
            warnings.warn('please do not use this option')
            imx = np.sqrt(imx0 ** 2 + imx1 ** 2)
        if dy == 'x2y2':
            imx = imx0 ** 2 + imx1 ** 2
        if dy == 'x2my2':
            imx = imx0 ** 2 - imx1 ** 2
    else:
        raise Exception('differentiation method %s not supported' % dy)
    return imx


# def moving_average_1d(data,window):
    # window/=window.sum()
    # return signal.convolve(data,window,mode='same')


# def moving_average_2d(data,window):
    # window/=window.sum()
    # return signal.convolve2d(data,window,mode='same', boundary='symm')        
    
    



# def f_xderiv(w, method='midpoint'):
#     """Find the rate of change between every datapoint in the x-direction."""
    
#     if w['ydata'].ndim==1:
#         x=w['xdata'][0]
#         y=w['ydata']

#         if method == 'midpoint':
#             dx = np.diff(x, axis=1)
#             ddata = np.diff(y, axis=1)

#             x = x[:,:-1] + dx / 2.0
#             y = ddata / dx
#         elif method == '2nd order central diff':
#             y = (y[:,2:] - y[:,:-2]) / (y[:,2:] - y[:,:-2])
#             x = x[:,1:-1]

#     else:
#         y=w['xdata'][0]
#         x=w['xdata'][1]
#         z=w['ydata']


#         # print(y)
#         # print(z)

#         if method == 'midpoint':
#             dx = np.diff(x, axis=1)
#             ddata = np.diff(z, axis=1)

#             x = x[:,:-1] + dx / 2.0
#             y = y[:-1]
#             z = ddata / dx
#         elif method == '2nd order central diff':
#             z = (z[:,2:] - z[:,:-2]) / (x[:,2:] - x[:,:-2])
#             x = x[:,1:-1]
#             y = y[1:-1]

#         print(w['xdata'])

#         w['xdata']=(y,x)
#         # w['xdata'][1]=x
#         w['ydata']=z

#         print(w['xdata'])

#         print(np.size(y))
#         print(np.size(x))
#         print(np.size(z))
#         print(np.size(w['xdata'][0]))
#         print(np.size(w['xdata'][1]))
#         print(np.size(w['ydata']))

#     return w


# def f_yderiv(w, method='midpoint'):
#     """Find the rate of change between every datapoint in the y-direction."""
    
#     if w['ydata'].ndim==1:
#         print('Invalid process function.')
#     else:
#         x=w['xdata'][0]
#         y=w['xdata'][1]
#         z=w['ydata']

#         if method == 'midpoint':
#             dy = np.diff(y, axis=0)
#             ddata = np.diff(z, axis=0)

#             x = x[:-1,:]
#             y = y[:-1,:] + dy / 2.0
#             z = ddata / dy
#         elif method == '2nd order central diff':
#             z = (z[2:] - z[:-2]) / (y[2:] - y[:-2])
#             x = x[1:-1]
#             y = y[1:-1]

#         w['xdata'][0]=x
#         w['xdata'][1]=y
#         w['ydata']=z

#     return w



# def f_dderiv(w, theta=0.0, method='midpoint'):
#     """Calculate the component of the gradient in a specific direction."""
#     xdir, ydir = np.cos(theta), np.sin(theta)

#     xcomp = w
#     xcomp.f_xderiv(method=method)
#     ycomp = w
#     ycomp.f_yderiv(method=method)

#     if method == 'midpoint':
#         xvalues = xcomp['ydata'][:-1,:]
#         yvalues = ycomp['ydata'][:,:-1]

#         w['xdata'][0], w['xdata'][1], w['ydata'] = xcomp['xdata'][0][:-1,:], ycomp['xdata'][1][:,:-1], xvalues * xdir + yvalues * ydir
#     elif method == '2nd order central diff':
#         xvalues = xcomp['ydata'][1:-1,:]
#         yvalues = ycomp['ydata'][:,1:-1]

#         w['xdata'][0], w['xdata'][1], w['ydata'] = xcomp['xdata'][0][1:-1,:], ycomp['xdata'][1][:,1:-1], xvalues * xdir + yvalues * ydir

#     return w





# def f_xinterp(w, points):
#     """Interpolate every row onto a uniformly spaced grid."""
#     x=w['xdata'][0]
#     y=w['xdata'][1]
#     if not w['ydata'].ndim==1:
#         z=w['ydata']

#     xmin, xmax, ymin, ymax, _, _ = get_limits(x,y,z)

#     xinterp = np.linspace(xmin, xmax, points)

#     rows = z.shape[0]
#     values = np.zeros((rows, points))

#     for i in range(rows):
#         f = interpolate.interp1d(x.ravel(), z[:,i].ravel(), bounds_error=False, fill_value=np.nan)
#         values[i] = f(xinterp)

#     y_avg = np.average(y, axis=1)[np.newaxis].T

#     w['xdata']=(np.tile(xinterp, (1, points)), np.tile(y_avg,(rows,1)))
#     w['ydata']= values

#     # self.set_data(np.tile(x, (rows,1)), np.tile(y_avg, (1, points)), values)

#     print(w['xdata'])
#     print(w['ydata'])
#     return w

# def f_yinterp(w):
#     """Interpolate every column onto a uniformly spaced grid."""
#     xmin, xmax, ymin, ymax, _, _ = self.get_limits()

#     y = np.linspace(ymin, ymax, points)[np.newaxis].T

#     cols = self.z.shape[1]
#     values = np.zeros((points, cols))

#     for i in range(cols):
#         f = interpolate.interp1d(self.y[:,i].ravel(), self.z[:,i].ravel(),
#                                  bounds_error=False, fill_value=np.nan)
#         values[:,i] = f(y).ravel()

#     x_avg = np.average(self.x, axis=0)

#     self.set_data(np.tile(x_avg, (points,1)), np.tile(y, (1,cols)), values)

