'''
Use BaseHandler for page requests since
the base API handler has some logic that prevents
requests without a referrer field
'''

import logging
import json
import os
import subprocess
from notebook.base.handlers import APIHandler
from json.decoder import JSONDecodeError
from tornado import web

from .util.workflow_status import get_status
from .util.plot_results import plot_results
from .util.convert_to_notebook import convert_to_notebook
from .util.convert_to_1d_param_sweep_notebook import convert_to_1d_psweep_nb
from .util.convert_to_2d_param_sweep_notebook import convert_to_2d_psweep_nb
from .util.convert_to_sciope_me import convert_to_sciope_me
from .util.convert_to_model_inference_notebook import convert_to_mdl_inference_nb
from .util.stochss_errors import StochSSAPIError
from .util.run_workflow import initialize

log = logging.getLogger('stochss')


class LoadWorkflowAPIHandler(APIHandler):
    '''
    ########################################################################
    Handler for getting the Workflow's status, info, type, model for the 
    Workflow manager page.
    ########################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Retrieve workflow's status, info, and model from User's file system.

        Attributes
        ----------
        '''
        stamp = self.get_query_argument(name="stamp")
        wkfl_type = self.get_query_argument(name="type")
        path = self.get_query_argument(name="path")
        self.set_header('Content-Type', 'application/json')
        user_dir = "/home/jovyan"
        log.debug("Time stamp of the workflow: {0}".format(stamp))
        log.debug("The type of the workflow: {0}".format(wkfl_type))
        log.debug("The path to the workflow/model: {0}".format(path))
        title_types = {"gillespy":"Ensemble Simulation","parameterSweep":"Parameter Sweep"}
        name_types = {"gillespy":"_ES","parameterSweep":"_PS"}
        parent_path = os.path.dirname(path)
        if path.endswith('.mdl'):
            resp = {"mdlPath":path,"timeStamp":stamp,"type":wkfl_type,
                    "status":"new","titleType":title_types[wkfl_type],
                    "wkflParPath": parent_path}
            name = path.split('/').pop().split('.')[0]
            resp["wkflName"] = name + name_types[wkfl_type] + stamp
            resp["wkflDir"] = resp['wkflName'] + ".wkfl"
            resp["startTime"] = None
        elif path.endswith('.wkfl'):
            resp = {"wkflDir":path.split('/').pop(), "wkflParPath":parent_path}
            resp["status"] = get_status(path)
            name = path.split('/').pop().split('.')[0]
            resp["wkflName"] = name
            try:
                resp["timeStamp"] = "_"+"_".join(name.split('_')[-2:])
            except:
                resp["timeStamp"] = None
            try:
                with open(os.path.join(user_dir, path, "info.json"), "r") as info_file:
                    info = json.load(info_file)
                resp["type"] = info['type']
                resp["startTime"] = info['start_time']
                resp["mdlPath"] = info['source_model'] if resp['status'] == "ready" else info['wkfl_model']
                resp["titleType"] = title_types[info['type']]
            except FileNotFoundError as err:
                self.set_status(404)
                error = {"Reason":"Info File Not Found","Message":"Could not find the workflow info file: "+str(err)}
                log.error("Exception information: {0}".format(error))
                self.write(error)
            except JSONDecodeError as err:
                self.set_status(406)
                error = {"Reason":"File Not JSON Format","Message":"The workflow info file is not JSON decodable: "+str(err)}
                log.error("Exception information: {0}".format(error))
                self.write(error)
        try:
            with open(os.path.join(user_dir, resp['mdlPath']), "r") as model_file:
                resp["model"] = json.load(model_file)
        except:
            resp["model"] = None
            resp["error"] = {"Reason":"Model Not Found","Message":"Could not find the model file: "+resp['mdlPath']}
        resp["settings"] = self.get_settings(os.path.join(resp['wkflParPath'], resp['wkflDir']), resp['mdlPath'])
        log.debug("Response: {0}".format(resp))
        self.write(resp)
        self.finish()


    def get_settings(self, wkfl_path, mdl_path):
        settings_path = os.path.join(wkfl_path, "settings.json")
        
        if os.path.exists(settings_path):
            with open(settings_path, "r") as settings_file:
                return json.load(settings_file)

        with open("/stochss/stochss_templates/workflowSettingsTemplate.json", "r") as template_file:
            settings_template = json.load(template_file)
        
        if os.path.exists(mdl_path):
            with open(mdl_path, "r") as mdl_file:
                mdl = json.load(mdl_file)
                try:
                    settings = {"simulationSettings":mdl['simulationSettings'],
                                "parameterSweepSettings":mdl['parameterSweepSettings'],
                                "resultsSettings":settings_template['resultsSettings']}
                    return settings
                except:
                    return settings_template
        else:
            return settings_template


class RunWorkflowAPIHandler(APIHandler):
    '''
    ########################################################################
    Handler for running workflows.
    ########################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Start running a workflow and record the time in UTC in the workflow_info file.
        Creates workflow directory and workflow_info file if running a new workflow.  Copys 
        model into the workflow directory.

        Attributes
        ----------
        '''
        data = json.loads(self.get_query_argument(name="data"))
        log.debug("Handler query string: {0}".format(data))
        opt_type = data['optType']
        wkfl_type = data['type']
        model_path = data['mdlPath']
        workflow_path = data['wkflPath']
        log.debug("Actions for the workflow: {0}".format(opt_type))
        log.debug("Type of workflow: {0}".format(wkfl_type))
        log.debug("Path to the model: {0}".format(model_path))
        log.debug("Path to the workflow: {0}".format(workflow_path))
        exec_cmd = ["/stochss/stochss/handlers/util/run_workflow.py", "{}".format(model_path), "{0}".format(workflow_path), "{0}".format(wkfl_type) ] # Script commands
        opt_type = list(map(lambda el: "-" + el, list(opt_type))) # format the opt_type for argparse
        exec_cmd.extend(opt_type) # Add opt_type to exec_cmd
        log.debug("Exec command sent to the subprocess: {0}".format(exec_cmd))
        log.debug('Sending the workflow run cmd')
        pipe = subprocess.Popen(exec_cmd)
        log.debug('The workflow has started')
        self.finish()


class SaveWorkflowAPIHandler(APIHandler):
    '''
    ########################################################################
    Handler for saving workflows.
    ########################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Start saving the workflow.  Creates the workflow directory and workflow_info file if
        saving a new workflow.  Copys model into the workflow directory.

        Attributes
        ----------
        '''
        data = json.loads(self.get_query_argument(name="data"))
        log.debug("Handler query string: {0}".format(data))
        opt_type = data['optType']
        wkfl_type = data['type']
        model_path = data['mdlPath']
        workflow_path = data['wkflPath']
        settings = data['settings']
        log.debug("Actions for the workflow: {0}".format(opt_type))
        log.debug("Type of workflow: {0}".format(wkfl_type))
        log.debug("Path to the model: {0}".format(model_path))
        log.debug("Path to the workflow: {0}".format(workflow_path))
        kwargs = {"save":True,"settings":settings}
        if 'n' in opt_type:
            kwargs['new'] = True
        else:
            kwargs['existing'] = True
        if 'r' in opt_type:
            kwargs['run'] = True
        resp = initialize(model_path, workflow_path, wkfl_type, **kwargs)
        log.debug("Response to the command: {0}".format(resp))
        if resp:
            self.write(resp)
        else:
            self.write(errors)
        self.finish()


class WorkflowStatusAPIHandler(APIHandler):
    '''
    ########################################################################
    Handler for getting Workflow Status (checking for RUNNING and COMPLETE files.
    ########################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Retrieve workflow status based on status files.

        Attributes
        ----------
        '''
        workflow_path = self.get_query_argument(name="path")
        log.debug('Getting the status of the workflow')
        status = get_status(workflow_path)
        log.debug('The status of the workflow is: {0}\n'.format(status))
        self.write(status)
        self.finish()


class PlotWorkflowResultsAPIHandler(APIHandler):
    '''
    ########################################################################
    Handler for getting result plots based on plot type.
    ########################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Retrieve a plot figure of the workflow results based on the plot type 
        in the request body.

        Attributes
        ----------
        '''
        workflow_path = self.get_query_argument(name="path")
        log.debug("The path to the workflow: {0}\n".format(workflow_path))
        body = json.loads(self.get_query_argument(name='data'))
        log.debug("Plot args passed to the plot: {0}\n".format(body))
        results_path = os.path.join(workflow_path, 'results/plots.json')
        log.debug("Path to the workflow results: {0}\n".format(results_path))
        plt_key = body['plt_key']
        log.debug("Key identifying the requested plot: {0}\n".format(plt_key))
        plt_data = body['plt_data']
        log.debug("Title and axis data for the plot: {0}\n".format(plt_data))
        self.set_header('Content-Type', 'application/json')
        try:
            if "None" in plt_data:
                plt_fig = plot_results(results_path, plt_key)
            else:
                plt_fig = plot_results(results_path, plt_key, plt_data) # Add plot data to the exec cmd if its not "None"
            log.debug("Plot figure: {0}\n".format(plt_fig))
            self.write(plt_fig)
        except StochSSAPIError as err:
            self.set_status(err.status_code)
            error = {"Reason":err.reason,"Message":err.message}
            log.error("Exception information: {0}\n".format(error))
            self.write(error)
        self.finish()


class WorkflowLogsAPIHandler(APIHandler):
    '''
    ########################################################################
    Handler for getting Workflow logs.
    ########################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Retrieve workflow logs from User's file system.

        Attributes
        ----------
        '''
        logs_path = self.get_query_argument(name="path")
        log.debug("Path to the workflow logs file: {0}\n".format(logs_path))
        full_path = os.path.join("/home/jovyan/", logs_path)
        log.debug("Full path to the workflow logs file: {0}\n".format(full_path))
        try:
            with open(full_path, 'r') as log_file:
                data = log_file.read()
            log.debug("Contents of the log file: {0}\n".format(data))
            if data:
                resp = data
            else:
                resp = "No logs were recoded for this workflow."
            log.debug("Response: {0}\n".format(resp))
            self.write(resp)
        except FileNotFoundError as err:
            self.set_status(404)
            self.set_header('Content-Type', 'application/json')
            error = {"Reason":"StochSS File or Directory Not Found","Message":"Could not find the workflow log file: "+str(err)}
            log.error("Exception information: {0}\n".format(error))
            self.write(error)
        self.finish()


class WorkflowNotebookHandler(APIHandler):
    '''
    ##############################################################################
    Handler for handling conversions from model (.mdl) file or workflows (.wkfl) 
    to Jupyter Notebook (.ipynb) file for notebook workflows.
    ##############################################################################
    '''
    @web.authenticated
    async def get(self):
        '''
        Create a jupyter notebook workflow using a stochss model.

        Attributes
        ----------
        '''
        log.setLevel(logging.DEBUG)
        workflow_type = self.get_query_argument(name="type")
        path = self.get_query_argument(name="path")
        settings = None

        if path.endswith('.wkfl'):
            name = path.split('/').pop().split('.')[0].replace('-', '_')
            with open(os.path.join(path, "info.json"), "r") as info_file:
                info = json.load(info_file)
                workflow_type = info['type']
            with open(os.path.join(path, "settings.json"), "r") as settings_file:
                settings = json.load(settings_file)
            if workflow_type == "parameterSweep":
                workflow_type = "1d_parameter_sweep" if settings['parameterSweepSettings']['is1D'] else "2d_parameter_sweep"
            path = info['source_model'] if info['wkfl_model'] is None else info['wkfl_model']
            log.debug("Name for the notebook: {0}".format(name))

        log.debug("Type of workflow to be run: {0}\n".format(workflow_type))
        log.debug("Path to the model: {0}\n".format(path))
        workflows = {"gillespy":convert_to_notebook,
                    "1d_parameter_sweep":convert_to_1d_psweep_nb,
                    "2d_parameter_sweep":convert_to_2d_psweep_nb,
                    "sciope_model_exploration":convert_to_sciope_me,
                    "model_inference":convert_to_mdl_inference_nb}
        try:
            resp = workflows[workflow_type](path, name=name, settings=settings) if settings is not None else workflows[workflow_type](path)
            log.debug("Response: {0}\n".format(resp))
            self.write(resp)
        except StochSSAPIError as err:
            self.set_status(err.status_code)
            self.set_header('Content-Type', 'application/json')
            error = {"Reason":err.reason,"Message":err.message}
            log.error("Exception information: {0}\n".format(error))
            self.write(error)
        log.setLevel(logging.WARNING)
        self.finish()

