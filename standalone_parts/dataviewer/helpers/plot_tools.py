import numpy as np

def get_indices_qcodes(data,x,y):
    '''
    data - qcodes dataset converted to x_array_dict (to_xarray_dict)

    '''
    # y array - get value span and num elements

    setpoints = data.depends_on

    y_data = data[setpoints[0]].to_numpy()
    nanarray_y=~(np.isnan(y_data))

    y_array=y_data[nanarray_y]
    y_numel=len(y_data)
    y_span=y_data[y_numel-1]-y_data[0]

    if y_span!=0:
        indy_coarse=(y_data[0]*y_numel/y_span-y*y_numel/y_span)
        indy_coarse=int(abs(indy_coarse))

        if y_numel>3:
            if indy_coarse<3:
                indsy=np.arange(0,indy_coarse+3)
            elif indy_coarse>y_numel-3:
                indsy=np.arange(indy_coarse-3,y_numel)
            else:
                indsy=np.arange(indy_coarse-3,indy_coarse+3)

        else:
            indsy=np.arange(0,y_numel)

        binsize_y=abs(y_span/y_numel)
        toly=0.1*binsize_y
        for ind in indsy:
            if y_array[ind]-binsize_y/2-toly < y < y_array[ind]+binsize_y/2+toly:  
                indy_fine=ind

    else:
        indy_fine=0   

    ## x array - get value span and num elements
    

    x_data = data[setpoints[1]].to_numpy()
    nanarray_x=~(np.isnan(x_data[indy_fine]))

    x_array=x_data[nanarray_x][0]
    x_numel=len(x_array)
    x_span=x_array[x_numel-1]-x_array[0]


    if x_span!=0:
        indx_coarse=(x_array[0]*x_numel/x_span-x*x_numel/x_span)
        indx_coarse=int(abs(indx_coarse))

        if x_numel>3:
            if indx_coarse<3:
                indsx=np.arange(0,indx_coarse+3)
            elif indx_coarse>x_numel-3:
                indsx=np.arange(indx_coarse-3,x_numel)
            else:
                indsx=np.arange(indx_coarse-3,indx_coarse+3)

        else:
            indsx=np.arange(0,x_numel)

        binsize_x=abs(x_span/x_numel)
        tolx=0.1*binsize_x
        for ind in indsx:
            if x_array[ind]-binsize_x/2-tolx < x < x_array[ind]+binsize_x/2+tolx:  
                indx_fine=ind


    else:
        indx_fine=0

    return indx_fine, indy_fine



def get_indices(data,x,y):

    # y array - get value span and num elements

    nanarray_y=~(np.isnan(data.set_arrays[0]))

    y_array=data.set_arrays[0][nanarray_y]
    y_numel=len(data.set_arrays[0][nanarray_y])
    y_span=data.set_arrays[0][y_numel-1]-data.set_arrays[0][0]

    if y_span!=0:
        indy_coarse=(data.set_arrays[0][0]*y_numel/y_span-y*y_numel/y_span)
        indy_coarse=int(abs(indy_coarse))

        if y_numel>3:
            if indy_coarse<3:
                indsy=np.arange(0,indy_coarse+3)
            elif indy_coarse>y_numel-3:
                indsy=np.arange(indy_coarse-3,y_numel)
            else:
                indsy=np.arange(indy_coarse-3,indy_coarse+3)

        else:
            indsy=np.arange(0,y_numel)

        binsize_y=abs(y_span/y_numel)
        toly=0.1*binsize_y
        for ind in indsy:
            if y_array[ind]-binsize_y/2-toly < y < y_array[ind]+binsize_y/2+toly:  
                indy_fine=ind

    else:
        indy_fine=0   

    ## x array - get value span and num elements

    nanarray_x=~(np.isnan(data.set_arrays[1][indy_fine]))

    x_array=data.set_arrays[1][indy_fine][nanarray_x]
    x_numel=len(data.set_arrays[1][indy_fine][nanarray_x])
    x_span=data.set_arrays[1][indy_fine][x_numel-1]-data.set_arrays[1][indy_fine][0]


    if x_span!=0:
        indx_coarse=(data.set_arrays[1][indy_fine][0]*x_numel/x_span-x*x_numel/x_span)
        indx_coarse=int(abs(indx_coarse))

        if x_numel>3:
            if indx_coarse<3:
                indsx=np.arange(0,indx_coarse+3)
            elif indx_coarse>x_numel-3:
                indsx=np.arange(indx_coarse-3,x_numel)
            else:
                indsx=np.arange(indx_coarse-3,indx_coarse+3)

        else:
            indsx=np.arange(0,x_numel)

        binsize_x=abs(x_span/x_numel)
        tolx=0.1*binsize_x
        for ind in indsx:
            if x_array[ind]-binsize_x/2-tolx < x < x_array[ind]+binsize_x/2+tolx:  
                indx_fine=ind


    else:
        indx_fine=0

    return indx_fine, indy_fine