@ ECHO OFF 
 
SET NB_DIR=%1 
SET PATH_CONDA=C:\Users\Antonio\anaconda3
SET ENV=qtNE_new_2023
 
SET PYTHON_PATH=%PATH_CONDA%\envs\%ENV%
 
IF EXIST "%PYTHON_PATH%\Scripts\ipython-script.py" ( 
 	start jupyter notebook --notebook-dir=%NB_DIR%
 
pause
	 GOTO EOF 
)
echo Failed to run
pause
 
: EOF