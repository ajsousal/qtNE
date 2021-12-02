import os
import json
import sys
import msvcrt

ESCAPE=chr(27)
    
def find_all(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result
    
def find_all_dirs(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in dirs:
            result.append(os.path.join(root, name))
    return result
    


print('Welcome to qtNE installer! \n \n This setup will: \n - generate an executable .bat file \n - generate the qtNE configuration file\n')

print(('Press any key to continue or ESC to exit the setup.'))
while True:
    if msvcrt.kbhit():
        key=msvcrt.getch()
        if ord(key)==27:
            sys.exit()
        elif ord(key)!=27:
            break

envname=input("Name of target environment: ")
pythonpaths=find_all("python.exe","C:\\")

envpath=os.path.dirname([path for path in pythonpaths if '\\envs\\'+envname+'\\' in path][0])

if envpath:
    print('Environment path: '+envpath)
else:
    input('Environment not found! Press any key to close the installer...')



installpaths=find_all("qtNE.cfg","C:\\")
# installpaths=find_all_dirs("qtNE","C:\\")

if len(installpaths)>1:
    print('Found multiple instances of qtNE:')
    print('\n'.join(installpaths))
    pathindex=input('Where should it be installed: [1 - '+str(len(installpaths))+']: \n')
    installpath=os.path.dirname(installpaths[int(pathindex)-1])
else:
    installpath=os.path.dirname(installpaths[0])
    

print('qtNE installation path: '+installpath)


bat_lines=[]
bat_lines.append('@ ECHO OFF \n \n')
bat_lines.append('IF EXIST '+envpath+'\\python.exe '+'( \n')
bat_lines.append('\t SET PYTHON_PATH='+envpath+'\n')
bat_lines.append('\t GOTO mark1 \n')
bat_lines.append(') \n \n')
bat_lines.append(':mark1 \n \n')
bat_lines.append('SET PYTHON_PATH='+envpath+'\n \n')
bat_lines.append('IF EXIST "%PYTHON_PATH%\\Scripts\\ipython-script.py" ( \n')
bat_lines.append('\t call '+os.path.dirname(os.path.dirname(envpath))+'\\Scripts\\activate.bat '+envname+' \n \t')
bat_lines.append('call ipython -i '+ installpath+'\\qtNE_shell.py' '\n \n')
bat_lines.append('pause\n')
bat_lines.append('\t GOTO EOF \n)\n')
bat_lines.append('echo Failed to run\n')
bat_lines.append('pause\n \n')
bat_lines.append(': EOF')

with open(os.path.join(installpath,'run_qtNE.bat'),'w') as f:
    f.writelines(bat_lines)
    


##############################



with open(os.path.join(installpath,'qtNE.cfg')) as json_file:
    data=json.load(json_file)    

    
datadir_new=input('Path to data storage: ')
while True:
    if not datadir_new:
        print('Enter a valid path. \n \n')
        datadir_new=input('Path to data storage: ')
        continue
    else:
        break

if not os.path.isdir(datadir_new):# dir doesnt exist, create
    createdatadir=input('Specified directory for data storage does not exist. Do you want to create it? [Y/n] \n')
    while True:
        if not createdatadir:
            os.mkdir(datadir_new)
            break
        elif createdatadir=='Y' or createdatadir=='y' or createdatadir=='yes' or createdatadir=='Yes': 
            os.mkdir(datadir_new)
            break
        elif createdatadir=='N' or createdatadir=='n' or createdatadir=='No' or createdatadir=='no':
            print('Setting up default data storage folder.')
            datadir_new=data['datadir']
            break
        else:
            print('Invalid input [Y/n]. \n')
            continue
    
measurementdir_new=input('Path to measurement scripts storage: ')
while True:
    if not measurementdir_new:
        print('Enter a valid path. \n \n')
        measurementdir_new=input('Path to data storage: ')
        continue
    else:
        break
        
if not os.path.isdir(measurementdir_new):# dir doesnt exist, create
    createmeasdir=input('Specified directory for measurement script storage does not exist. Do you want to create it? [Y/n] \n')
    while True:    
        if not createmeasdir:
            os.mkdir(measurementdir_new)
            break
        elif createmeasdir=='Y' or createmeasdir=='y' or createmeasdir=='yes' or createmeasdir=='Yes':
            os.mkdir(measurementdir_new)
            break
        elif createmeasdir=='N' or createmeasdir=='n' or createmeasdir=='No' or createmeasdir=='no':
            print('Setting up default measurement scripts folder.')
            measurementdir_new=data['measurementdir']
            break
        else:
            print('Invalid input [Y/n]. \n')
            continue


    
tempdir_new=os.path.join(installpath,'tmp')


default_user_new=input('Name of default user: ')
if not os.path.isdir(os.path.join(datadir_new,default_user_new)):# dir doesnt exist, create
    print('Creating data directory for '+default_user_new)
    os.mkdir(os.path.join(datadir_new,default_user_new))
if not os.path.isdir(os.path.join(measurementdir_new,default_user_new)):# dir doesnt exist, create
    print('Creating measurement scripts directory for '+default_user_new)
    os.mkdir(os.path.join(measurementdir_new,default_user_new))



externaldir_new=input('Path to external modules storage: ')
while True:
    if not externaldir_new:
        print('Enter a valid path. \n \n')
        externaldir_new=input('Path to data storage: ')
        continue
    else:
        break
        
if not os.path.isdir(externaldir_new):# dir doesnt exist, create
    createmeasdir=input('Specified directory for measurement script storage does not exist. Do you want to create it? [Y/n] \n')
    while True:    
        if not createmeasdir:
            os.mkdir(externaldir_new)
            break
        elif createmeasdir=='Y' or createmeasdir=='y' or createmeasdir=='yes' or createmeasdir=='Yes':
            os.mkdir(externaldir_new)
            break
        elif createmeasdir=='N' or createmeasdir=='n' or createmeasdir=='No' or createmeasdir=='no':
            print('Setting up default external modules folder.')
            externaldir_new=data['external_modules']
            break
        else:
            print('Invalid input [Y/n]. \n')
            continue



if datadir_new:
    data['datadir']=datadir_new
if measurementdir_new: 
    data['measurementdir']=measurementdir_new
data['default_user']=default_user_new
data['tempdir']=tempdir_new
data['external_modules']=externaldir_new

print('Data directory: '+data['datadir'])
print('Measurement directory: '+data['measurementdir'])
print('Default user: '+data['default_user'])
print('External modules: '+data['external_modules'])
print('Temporary files directory: '+data['tempdir'])

with open(os.path.join(installpath,'qtNE.cfg'),'w') as json_file:
    json.dump(data,json_file,indent=4)
    
    
input('qtNE setup finished. Press any key to exit.')
