#!/usr/bin/env python3

import os
import json
from .rename import get_unique_file_name
from .stochss_errors import StochSSFileNotFoundError
# from run_model import ModelFactory
from gillespy2.sbml.SBMLimport import convert
import gillespy2


def convert_to_gillespy_model(path):
    if os.path.exists(path):
        gpy_model, errors = convert(path)
        return gpy_model, errors
    else:
        raise StochSSFileNotFoundError("Could not find the sbml file: "+path)


def convert_to_stochss_model(stochss_model, gillespy_model, full_path):
    comp_id = 1
    errors = []
    if type(gillespy_model) is gillespy2.core.gillespy2.Model:
        sbml_model_file = full_path.split('/').pop()
        stochss_model_file = gillespy_model.name + '.mdl'
        stochss_model_path = get_unique_file_name(stochss_model_file, full_path.split(sbml_model_file)[0])[0]

        species = gillespy_model.get_all_species()
        stochss_species, algorithm, default_mode, comp_id = get_species(species, comp_id)
        stochss_model['species'].extend(stochss_species)
        stochss_model['defaultMode'] = default_mode
        stochss_model['simulationSettings']['algorithm'] = algorithm

        parameters = gillespy_model.get_all_parameters()
        stochss_parameters, comp_id = get_parameters(parameters, comp_id)
        stochss_model['parameters'].extend(stochss_parameters)

        reactions = gillespy_model.get_all_reactions()
        stochss_reactions, comp_id = get_reactions(reactions, stochss_species, comp_id)
        stochss_model['reactions'].extend(stochss_reactions)

        events = gillespy_model.listOfEvents
        stochss_events, comp_id = get_events(events, stochss_species, stochss_parameters, comp_id)
        stochss_model['eventsCollection'].extend(stochss_events)

        rate_rules = gillespy_model.listOfRateRules
        stochss_rate_rules, comp_id = get_rate_rules(rate_rules, stochss_species, stochss_parameters, comp_id)
        stochss_model['rules'].extend(stochss_rate_rules)

        assignment_rules = gillespy_model.listOfAssignmentRules
        stochss_assignment_rules, comp_id = get_assignment_rules(assignment_rules, stochss_species, stochss_parameters, comp_id)
        stochss_model['rules'].extend(stochss_assignment_rules)
        
        function_definitions = gillespy_model.listOfFunctionDefinitions
        stochss_function_definitions, comp_id = get_function_definitions(function_definitions, comp_id)
        stochss_model['functionDefinitions'].extend(stochss_function_definitions)

        stochss_model['defaultID'] = comp_id

        with open(stochss_model_path, "w") as stochss_file:
            json.dump(stochss_model, stochss_file)
    
        return "The SBML Model was successfully converted to a StochSS Model.", errors
    else:
        return "ERROR! We were unable to convert the SBML Model into a StochSS Model.", []


def get_species(species, comp_id):
    stochss_species = []
    mode = "dynamic"
    algorithm = "SSA"

    for name in species.keys():
        if not species[name].mode == "dynamic":
            mode = "continuous"
            algorithm = "Hybrid-Tau-Leaping"
            break

    for name in species.keys():
        specie = species[name]

        stochss_specie = {"compID":comp_id,
                          "name":specie.name,
                          "value":specie.initial_value,
                          "mode":mode,
                          "switchTol": 0.03,
                          "switchMin": 100,
                          "isSwitchTol": True,
                          "annotation": "",
                          "diffusionCoeff":0,
                          "subdomains": [
                              "subdomain 1: ",
                              "subdomain 2: "
                          ]}

        stochss_species.append(stochss_specie)
        comp_id += 1

    return stochss_species, algorithm, mode, comp_id


def get_parameters(parameters, comp_id):
    stochss_parameters = []

    for name in parameters.keys():
        parameter = parameters[name]

        stochss_parameter = {"compID":comp_id,
                             "name":parameter.name,
                             "expression":str(parameter.expression),
                             "annotation": ""
                            }

        stochss_parameters.append(stochss_parameter)
        comp_id += 1

    return stochss_parameters, comp_id


def get_reactions(reactions, stochss_species, comp_id):
    stochss_reactions = []

    for name in reactions.keys():
        reaction = reactions[name]

        stochss_reaction = {"compID":comp_id,
                            "name":reaction.name,
                            "reactionType": "custom-propensity",
                            "massaction": False,
                            "propensity": reaction.propensity_function,
                            "annotation": "",
                            "rate": {},
                            "subdomains": [
                              "subdomain 1: ",
                              "subdomain 2: "
                            ],
                            "reactants": [],
                            "products": [],
                            }

        reactants = reaction.reactants
        stochss_reactants = get_reactants(reactants, stochss_species)
        stochss_reaction['reactants'].extend(stochss_reactants)

        products = reaction.products
        stochss_products = get_products(products, stochss_species)
        stochss_reaction['products'].extend(stochss_products)

        summary = build_summary(stochss_reactants, stochss_products)
        stochss_reaction['summary'] = summary
        
        stochss_reactions.append(stochss_reaction)
        comp_id += 1

    return stochss_reactions, comp_id


def get_reactants(reactants, stochss_species):
    stochss_reactants = []

    for specie in reactants.keys():
        ratio = reactants[specie]
        stoich_species = get_specie(stochss_species, specie.name)

        stochss_reactant = {"ratio":ratio,"specie":stoich_species}
        stochss_reactants.append(stochss_reactant)

    return stochss_reactants


def get_products(products, stochss_species):
    stochss_products = []

    for specie in products.keys():
        ratio = products[specie]
        stoich_species = get_specie(stochss_species, specie.name)

        stochss_product = {"ratio":ratio,"specie":stoich_species}
        stochss_products.append(stochss_product)

    return stochss_products


def get_specie(stochss_species, name):
    return list(filter(lambda specie: specie['name'] == name, stochss_species))[0]


def get_parameter(stochss_parameters, name):
    return list(filter(lambda parameter: parameter['name'] == name, stochss_parameters))[0]


def build_summary(stochss_reactants, stochss_products):
    summary = ""

    if len(stochss_reactants):
        reactant_elements = list(map(build_summary_element, stochss_reactants))
        reactants_summary = '+'.join(reactant_elements)
    else:
        reactants_summary = "\\emptyset"
    summary += reactants_summary

    summary += " \\rightarrow "

    if len(stochss_products):
        product_elements = list(map(build_summary_element, stochss_products))
        products_summary = '+'.join(product_elements)
    else:
        products_summary = "\\emptyset"
    summary += products_summary

    return summary


def build_summary_element(stoich_specie):
    ratio = stoich_specie['ratio']
    name = stoich_specie['specie']['name']

    if ratio > 1:
        return "{0}{1}".format(ratio, name)
    else:
        return name


def get_events(events, stochss_species, stochss_parameters, comp_id):
    stochss_events = []

    for name in events.keys():
        event = events['name']

        stochss_event = {"compID":comp_id,
                         "name": event.name,
                         "annotation": "",
                         "delay": event.delay,
                         "priority": event.priority,
                         "triggerExpression": event.trigger.expression,
                         "initialValue": event.trigger.value,
                         "persistent": event.trigger.persistent,
                         "useValuesFromTriggerTime": event.use_values_from_trigger_time,
                         "eventAssignment": []
                        }

        assignments = event.assignments
        stochss_assignments = get_event_assignments(assignments, stochss_species, stochss_parameters)
        stochss_event['eventAssignment'].extend(stochss_assignments)

        stochss_events.append(stochss_event)
        comp_id += 1

    return stochss_events, comp_id


def get_event_assignment(assignments, stochss_species, stochss_parameters):
    stochss_assignments = []

    for assignment in assignments:
        try:
            variable = get_specie(stochss_species, assignment.variable.name)
        except:
            variable = get_parameter(stochss_parameters, assignment.variable.name)

        stochss_assignment = {"variable": variable,
                              "expression": assignment.expression
                             }

        stochss_assignments.append(stochss_assignment)

    return stochss_assignments


def get_rate_rules(rate_rules, stochss_species, stochss_parameters, comp_id):
    stochss_rate_rules = []

    for name in rate_rules.keys():
        rate_rule = rate_rules[name]

        try:
            variable = get_specie(stochss_species, rate_rule.species.name)
        except:
            variable = get_parameter(stochss_parameters, rate_rule.species.name)

        stochss_rate_rule = {"compID":comp_id,
                             "name":rate_rule.name,
                             "expression":rate_rule.expression,
                             "type":"Rate Rule",
                             "variable":variable,
                             "annotation": ""
                            }

        stochss_rate_rules.append(stochss_rate_rule)
        comp_id += 1

    return stochss_rate_rules, comp_id


def get_assignment_rules(assignment_rules, stochss_species, stochss_parameters, comp_id):
    stochss_assignment_rules = []

    for name in assignment_rules.keys():
        assignment_rule = assignment_rules[name]

        try:
            variable = get_specie(stochss_species, assignment_rule.variable.name)
        except:
            variable = get_parameter(stochss_parameters, assignment_rule.variable.name)

        stochss_assignment_rule = {"compID":comp_id,
                                   "name":assignment_rule.name,
                                   "expression":assignment_rule.expression,
                                   "type":"Assignment Rule",
                                   "variable":variable,
                                   "annotation": ""
                                  }

        stochss_assignment_rules.append(stochss_assignment_rule)
        comp_id += 1

    return stochss_assignment_rules, comp_id


def get_function_definitions(function_definitions, comp_id):
    stochss_function_definitions = []

    for name in function_definitions.keys():
        function_definition = function_definitions[name]

        function_elements = function_definition.function.split(': ')
        expression = function_elements.pop()
        variables = function_elements[0].split('lambda ').pop()
        signature = "{0}({1})".format(function_definition.name, variables)

        stochss_function_definition = {"compID":comp_id,
                                       "name":function_defintion.name,
                                       "function":function_definition.function,
                                       "expression":expression,
                                       "variables":variables,
                                       "signature":signature,
                                       "annotation": ""
                                       }

        stochss_function_definitions.append(stochss_function_definition)
        comp_id += 1

    return stochss_function_definitions, comp_id


def convert_sbml_to_model(path, model_template):
    user_dir = "/home/jovyan"
    
    full_path = os.path.join(user_dir, path)
    template = json.loads(model_template)
    gillespy_model, sbml_errors = convert_to_gillespy_model(full_path)
    sbml_errors = list(map(lambda error: error[0], sbml_errors))
    msg, errors = convert_to_stochss_model(template, gillespy_model, full_path)
    sbml_errors.extend(errors)
    resp = {"message":msg,"errors":sbml_errors}
    return resp