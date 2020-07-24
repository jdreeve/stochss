#!/usr/bin/env python3
import json
from json.decoder import JSONDecodeError
import nbformat
from nbformat import v4 as nbf
from os import path

from .run_model import ModelFactory
from .rename import get_unique_file_name
from .generate_notebook_cells import generate_imports_cell, generate_model_cell, generate_run_cell, generate_configure_simulation_cell, get_algorithm
from .stochss_errors import ModelNotFoundError, ModelNotJSONFormatError, JSONFileNotModelError


def convert_to_notebook(_model_path, name=None, settings=None, dest_path=None):
    user_dir = '/home/jovyan'

    model_path = path.join(user_dir,_model_path)
    file = model_path.split('/').pop()
    if name is None:
        name = file.split('.')[0].replace('-', '_')
    if dest_path is None:
        dest_path = model_path.split(file)[0]
    
    # Collect .mdl Data
    try:
        with open(model_path, 'r') as json_file:
            json_data = json.loads(json_file.read())
            json_data['name'] = name
    except FileNotFoundError as e:
        raise ModelNotFoundError('Could not read the file: ' + str(e))
    except JSONDecodeError as e:
        raise ModelNotJSONFormatError('The data is not JSON decobable: ' + str(e))

    is_ode = json_data['defaultMode'] == "continuous" if settings is None else settings['simulationSettings']['algorithm'] == "ODE"
    gillespy2_model = ModelFactory(json_data, is_ode).model

    if settings is None or settings['simulationSettings']['isAutomatic']:
        algorithm, solv_name = get_algorithm(gillespy2_model)
    else:
        algorithm, solv_name = get_algorithm(gillespy2_model, algorithm=settings['simulationSettings']['algorithm'])
    
    # Create new notebook
    cells = []
    # Create Markdown Cell with name
    cells.append(nbf.new_markdown_cell('# {0}'.format(name)))
    try:
        if settings is None:
            import_cell = generate_imports_cell(json_data, algorithm, solv_name)
            config_cell = generate_configure_simulation_cell(json_data, algorithm, solv_name)
        else:
            import_cell = generate_imports_cell(json_data, algorithm, solv_name, settings=settings['simulationSettings'])
            config_cell = generate_configure_simulation_cell(json_data, algorithm, solv_name, settings=settings['simulationSettings'])
        # Create imports cell
        cells.append(nbf.new_code_cell(import_cell))
        # Create Model Cell
        cells.append(nbf.new_code_cell(generate_model_cell(json_data, name)))
        # Instantiate Model Cell
        cells.append(nbf.new_code_cell('model = {0}()'.format(name)))
        if settings is not None and not settings['simulationSettings']['isAutomatic'] and solv_name == "SSACSolver":
            # Instantiate Solver Cell
            cells.append(nbf.new_code_cell('solver = SSACSolver(model=model)'))
        # Configure Simulation Cell
        cells.append(nbf.new_code_cell(config_cell))
        # Model Run Cell
        cells.append(nbf.new_code_cell(generate_run_cell(json_data)))
    except KeyError as err:
        raise JSONFileNotModelError("Could not convert your model: " + str(err))
    # Plotting Cell
    cells.append(nbf.new_code_cell('results.plotplotly()'))

    # Append cells to worksheet
    nb = nbf.new_notebook(cells=cells)

    # Open and write to file
    dest_file = get_unique_file_name('{}.ipynb'.format(name), dest_path)[0]
    with open(dest_file, 'w') as f:
        nbformat.write(nb, f, version=4)
    f.close()

    return {"Message":'{0} successfully created'.format(dest_file),"FilePath":dest_file.replace(user_dir+'/', ""),"File":dest_file.split('/').pop()}