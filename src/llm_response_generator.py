import os
from itertools import combinations
from itertools import product
import re

model_role_list = ['You are a recommender system that help users with crypto investment planning.']

scenario_list = ['I have {budget} CHF to invest.',
                 'My risk tolerance is {risk}.',
                 'My saving term is {term}.',
                 'The market environment is {env}.']

requirements = ['Please give me an investment plan. The available investment options are Coin, stable coins, utility tokens, meme coins .']

attribute_dict = {
                'budget':['10,000', '20,000', '30,000', '40,000', '50,000'],
                'risk':['risk averse', 'risk neutral'], 
                'term':['less than one year', 'one to three years', 'three to ten years', 'more than ten years'],
                'env':['expansion', 'crisis', 'recession', 'recovery']
                
attribute_list = ['budget', 'risk', 'term', 'env']


scenario_index_list = list(range(len(scenario_list)))

all_templates = []
file_name_list = []
for role_idx, role in enumerate(model_role_list):
    
    all_scenarios = []
    for r in range(0, len(scenario_index_list) + 1):  
        for combo in combinations(scenario_index_list, r):
            if len(combo) == 0:
                if role_idx==0:
                    file_name = 'no_fair_no_scenario'
                else:
                    file_name = 'fair_no_scenario'
            else:
                if role_idx==0:
                    file_name = 'no_fair_'+'-'.join([attribute_list[ii] for ii in combo])
                else:
                    file_name = 'fair_'+'-'.join([attribute_list[ii] for ii in combo])
            file_name_list.append(file_name)
            
            scenario_combina_list = [scenario_list[idx] for idx in list(combo)]
            if len(scenario_combina_list)==0:
                tmp_scenario = ''
            else:
                tmp_scenario = ' '.join(scenario_combina_list)
            # if 0 in combo:
                # tmp_scenario = role + ' ' + tmp_scenario + ' ' + requirements[0]
            # else:
            tmp_scenario = role + ' ' + tmp_scenario + ' ' + requirements[0]
            all_scenarios.append(tmp_scenario)
            all_templates.append(tmp_scenario)



all_prompts = []
for idx, template in enumerate(all_templates):
    prompts = []
    keys_in_template = list(set(re.findall(r'\{.*?\}', template)))
    
    
    values = [attribute_dict[key] for key in keys_in_template]
    
    
    combinations = product(*values)

    #  prompt
    for combination in combinations:
        # print(combination)
    # print('--------')
        prompt = template
        for key, value in zip(keys_in_template, combination):
            prompt = prompt.replace(key, value)
        prompts.append(prompt)
        all_prompts.append(prompt)
        
    # print(len(prompts))

    save_dir = 'combination_prompts_v1'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    with open(os.path.join(save_dir, '%s_%s.txt'%(file_name_list[idx], len(prompts))), 'w') as f:
        for prp in prompts:
            f.write(prp + '\n')

print(len(all_prompts))

