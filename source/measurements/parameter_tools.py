import numpy as np


def sweepcombined(numpars,*argv):
    sweep_vals=np.tile([np.zeros(numpars)],(len(argv[1]),1))
    ii=-1
    for arg in argv:
        ii+=1
        for ff in range(len(arg)):
            sweep_vals[ff][ii]=arg[ff]
    return sweep_vals

def _set_combi_generic(par_list,setlist,gainlist):
    for kk in range(len(par_list)):
        par_list[kk].set(setlist[kk]/gainlist[kk])

def _get_combi_generic(par_list,gainlist):
    result=[]
    for kk in range(len(par_list)):
        result.append(par_list[kk].get()*gainlist[kk])

    return result

def _set_combi(instr,list_dacs,setlist,gainlist):
    for kk in range(len(list_dacs)):
        getattr(instr,'dac'+str(list_dacs[kk])).set(setlist[kk]/gainlist[kk])

def _get_combi(instr,list_dacs,gainlist):
    result=[]
    for kk in range(len(list_dacs)):
        result.append(getattr(instr,'dac'+str(list_dacs[kk])).get()*gainlist[kk]) # instr._get_dac(list_dacs[kk])*gainlist[kk])

    return result
