
import os
import numpy as np


import shutil

import pickle
from tempfile import gettempdir


def read_tmp(tmp_file=None):

		with open(os.path.join(gettempdir(),tmp_file),"rb") as f:
			tempdata = []
			try:
				while True:
					tempdata.append(pickle.load(f))
			except EOFError:
				pass
		for kk in range(len(tempdata)): tempdata[0].update(tempdata[kk])
		for kk in range(len(tempdata)-1,0,-1):tempdata.pop(kk)

		return tempdata[0]




def set_status(val):
	# 1 - started, 0 - closed

	global status
	status=val

def get_status():

	try:
		if status==1:
			status
			return status
	except:
		pass