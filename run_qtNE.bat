@ ECHO OFF 
 
IF EXIST C:\Users\NE-admin\Anaconda3\envs\qtNE\python.exe ( 
	 SET PYTHON_PATH=C:\Users\NE-admin\Anaconda3\envs\qtNE
	 GOTO mark1 
) 
 
:mark1 
 
SET PYTHON_PATH=C:\Users\NE-admin\Anaconda3\envs\qtNE
 
IF EXIST "%PYTHON_PATH%\Scripts\ipython-script.py" ( 
	 call C:\Users\NE-admin\Anaconda3\Scripts\activate.bat qtNE 
 	call ipython -i C:\qtNE_standalone\qtNE_shell.py
 
pause
	 GOTO EOF 
)
echo Failed to run
pause
 
: EOF