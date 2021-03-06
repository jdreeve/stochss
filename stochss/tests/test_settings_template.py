import unittest
import json
import os

os.chdir('/stochss')

template_path = "stochss_templates/workflowSettingsTemplate.json"


class TestWorkflowSettingsTemplate(unittest.TestCase):

    def test_settings_elements(self):
        with open(template_path, "r") as template_file:
            template = json.load(template_file)

        template_keys = sorted(list(template.keys()))
        model_path = "client/models/settings.js"

        with open(model_path, "r") as model_file:
            children = model_file.read().split("children: {").pop().split('}')[0].split(',')
            model_keys = sorted(list(map(lambda item: item.strip().split(':')[0], children)))
            
        self.assertEqual(template_keys, model_keys)


    def test_simulation_settings_elements(self):
        with open(template_path, "r") as template_file:
            template = json.load(template_file)

        template_keys = sorted(list(template['simulationSettings'].keys()))
        sim_settings_path = "client/models/simulation-settings.js"

        with open(sim_settings_path, "r") as sim_settings_file:
            data = sim_settings_file.read().split("props: {").pop().split('}')[0].split(',')
            sim_settings_keys = sorted(list(map(lambda item: item.strip().split(':')[0], data)))

        self.assertEqual(template_keys, sim_settings_keys)


    def test_psweep_settings_elements(self):
        with open(template_path, "r") as template_file:
            template = json.load(template_file)

        template_keys = sorted(list(template['parameterSweepSettings'].keys()))
        psweep_settings_path = "client/models/parameter-sweep-settings.js"

        with open(psweep_settings_path, "r") as psweep_settings_file:
            data = psweep_settings_file.read()
            props = data.split("props: {").pop().split('}')[0].split(',')
            children = data.split("children: {").pop().split('}')[0].split(',')
            psweep_settings_keys = list(map(lambda item: item.strip().split(':')[0], props))
            psweep_settings_keys.extend(list(map(lambda item: item.strip().split(':')[0], children)))

        psweep_settings_keys.sort()
        self.assertEqual(template_keys, psweep_settings_keys)


    def test_results_settings_elements(self):
        with open(template_path, "r") as template_file:
            template = json.load(template_file)

        template_keys = sorted(list(template['resultsSettings'].keys()))
        results_settings_path = "client/models/results-settings.js"

        with open(results_settings_path, "r") as results_settings_file:
            data = results_settings_file.read().split("props: {").pop().split("}")[0].split(",")
            results_settings_keys = sorted(list(map(lambda item: item.strip().split(":")[0], data)))

        self.assertEqual(template_keys, results_settings_keys)

