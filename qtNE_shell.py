import os
import sys

def do_start_dataviewer():


    """
    Retrieve initialization files and base (package) directory

    """
    
    basedir= os.getcwd()

    sys.path.append(os.path.abspath(os.path.join(basedir, 'source')))
    ignorelist = []
    i = 1

    filelist = [(os.path.join(basedir, 'init',),'00_dataviewer_shell.py')]
    return filelist


def do_start_station():

    """
    Retrieve initialization files and base (package) directory

    """
    
    basedir= os.getcwd()

    sys.path.append(os.path.abspath(os.path.join(basedir, 'source')))
    # print(basedir)
    ignorelist = []
    ignorelist = ['00_dataviewer_shell.py']
    i = 1

    filelist = get_shell_files(os.path.join(basedir, 'init'), ignorelist)
    return filelist



def get_shell_files(path, ignore_list):
    ret = []

    entries = os.listdir(path)
    for i in entries:
        if len(i) > 0 and i[0] == '.':
            continue

        if os.path.isdir(i):
            subret = get_shell_files(os.path.join(path, i))
            for j in subret:
                insert_in_file_list(ret, j, ignore_list)
        else:
            insert_in_file_list(ret, (path, i), ignore_list)

    return ret




def insert_in_file_list(entries, entry, ignore_list):
    adddir, addname = entry
    if os.path.splitext(addname)[1] != ".py":
        return

    for start in ignore_list:
        if addname.startswith(start):
            return

    index = 0
    for (dir, name) in entries:
        if name[0] > addname[0] or (name[0] == addname[0] and name[1] > addname[1]):
            entries.insert(index, entry)
            break
        index += 1

    if index == len(entries):
        entries.append(entry)



def show_start_help():

    import IPython
    ip_version = IPython.__version__.split('.')
    if int(ip_version[0]) > 0 or int(ip_version[1]) > 10:
        ip = IPython.core.ipapi.get()
        ip.exit()
    else:
        ip = IPython.ipapi.get()
        ip.magic('Exit')


if __name__ == '__main__':

    print('\n \n')
    print('Starting qtNE environment...\n')
    
    mode = None
    while mode != 1 and mode != 2:
        mode = int(input('What do you want to run? [1: Station, 2: Dataviewer-only]: '))
        
    if mode==1:
        print('\n')
        filelist = do_start_station()

    elif mode==2:
        print('\n')
        filelist=do_start_dataviewer()

    for (dir, name) in filelist:
        filename = '%s/%s' % (dir, name)
        print('Executing %s...' % (filename))
        try:
            exec(open(filename).read())
        except SystemExit:
            break

    try:
        del filelist, dir, name, filename
    except:
        pass