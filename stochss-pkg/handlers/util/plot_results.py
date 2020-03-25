#!/usr/bin/env python3


import json
from os import path
from .stochss_errors import StochSSFileNotFoundError, PlotNotAvailableError


def read_plots_file(plots_file_path):
    '''
    Read the plots file and return its contents.

    Attributes
    ----------
    plots_file_path : str
        Path to the plots file.
    '''
    try:
        with open(plots_file_path, 'r') as plt_file:
            plots = json.load(plt_file)
        return plots
    except FileNotFoundError as err:
        raise StochSSFileNotFoundError("Could not find the plot file: {0}".format(err))
    

def get_plot_fig(plots_file_path, plt_key):
    '''
    Get the plots for the workflow and return the plot at the plt_key.

    Attributes
    ----------
    plots_file_path : str
        Path to the plots file.
    plt_key : str
        The key that the target plot is stored under.
    '''
    plots = read_plots_file(plots_file_path)
    try:
        return plots[plt_key]
    except KeyError as err:
        raise PlotNotAvailableError("The plot is not available: "+str(err))


def edit_plot_fig(plt_fig, plt_data):
    '''
    Edit the title, x-axis label, and/or y-axis label to the plt_data.

    Attributes
    ----------
    plt_fig : json
        The plot figure to be edited.
    plt_data : str
        The data that needs to be applied to the plot.
    '''
    plt_data = json.loads(plt_data)
    for key in plt_data.keys():
        if key == "title":
            plt_fig['layout']['title']['text'] = plt_data[key]
        else:
            plt_fig['layout'][key]['title']['text'] = plt_data[key]

    return plt_fig


def plot_results(plots_path, plt_key, plt_data=None):
    user_dir = "/home/jovyan"

    full_path = path.join(user_dir, plots_path)
    
    plt_fig = get_plot_fig(full_path, plt_key)

    if type(plt_fig) is str:
        return plt_fig
    if not plt_data:
        return json.dumps(plt_fig)
    plt_fig = edit_plot_fig(plt_fig, plt_data)
    return json.dumps(plt_fig)

        