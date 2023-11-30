@ ECHO OFF 

SET CONDA_INSTALL=LOCAL
SET PATH_CONDA=C:\Users\Antonio\anaconda3
SET ENV=qtNE_new_2023
 
IF EXIST "%PATH_CONDA%\envs\%ENV%\python.exe" ( 
	 SET PYTHON_PATH=%PATH_CONDA%\envs\%ENV%
	 GOTO mark1 
) 
 
:mark1 

SET PYTHON_PATH=%PATH_CONDA%\envs\%ENV%
 
IF EXIST "%PYTHON_PATH%\Scripts\ipython-script.py" ( 
	IF %CONDA_INSTALL%==GLOBAL (
		call C:\ProgramData\anaconda3\Scripts\activate.bat %ENV%
	)
	IF %CONDA_INSTALL%==LOCAL (
		call %PATH_CONDA%\Scripts\activate.bat %ENV%
	)
 	call ipython -i %cd%\qtNE_shell.py
 
pause
	 GOTO EOF 
)
echo Failed to run
pause
 
: EOF