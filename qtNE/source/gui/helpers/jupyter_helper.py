import nbformat as nbf
from textwrap import dedent
from os import getcwd, path
from datetime import datetime


def create_qcodes_nb(index,data_path, save_path = getcwd()):

    nb = nbf.v4.new_notebook()

    pp = index.parent().data()
    row=index.row()


    text = """\
        ..."""
    
    code_imports = dedent("""\
    #import packages
    import sys
    import os
    from time import sleep
    import matplotlib

    matplotlib.rc('xtick', labelsize=15) 
    matplotlib.rc('ytick', labelsize=15)

    font = {'family' : 'Arial',
            'size'   : 18}

    matplotlib.rc('font', **font)

    import matplotlib.pyplot as plt
    import numpy as np
    from qcodes import (
        initialise_or_create_database_at
    )

    from qcodes.dataset.plotting import plot_dataset
    from qcodes.logger.logger import start_all_logging

    from qcodes.dataset.plotting import plot_by_id
    from qcodes.dataset.data_set import load_by_id
    from qcodes.dataset.plotting import plot_2d_scatterplot
    import pickle
    import matplotlib.animation as animation

    from  matplotlib.animation import FFMpegWriter
    np.set_printoptions(threshold=sys.maxsize)

    colormap='viridis'
        """)
    
    data_path = data_path

    code_db_plot = dedent(f"""def id_plot(database, run_id, title="", directory=os.getcwd() """)
    code_db_plot2 = dedent(
        f"""):
            database=database
            initialise_or_create_database_at(f"{data_path}""")
    code_db_plot3 = dedent(
        """\\{database}\\db_{database}.db")

            matplot = plot_by_id(run_id, cmap=colormap)[0][-1];
            plt.close('all')

            matplot.set_aspect('equal','box')
            matplot.set_title(title+'\\n'+f'#{database}- {run_id}')

            fig1 = matplot.figure
            fig1.set_tight_layout(True)

            fig1.show()
            fig1.savefig(directory+title+f'{database} -{run_id}.png', dpi=150)

            return fig1
            """)

    database=pp
    # print(database)
    rid=index.sibling(row,0).data()
    # print(rid)

    code_db_data=dedent(f"""
    id_plot({database}, {rid}, title='')

                        """)

    nb['cells'] = [ nbf.v4.new_markdown_cell(text),
                    nbf.v4.new_code_cell(code_imports),
                    nbf.v4.new_code_cell(code_db_plot+code_db_plot2+code_db_plot3),
                    nbf.v4.new_code_cell(code_db_data)]
    
    now = datetime.now()
    fname = now.strftime("%Y%m%d_%H%M%S")+str('.ipynb')

    nbf.write(nb, path.join(save_path,fname))

    return