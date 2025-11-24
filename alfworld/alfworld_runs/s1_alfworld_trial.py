"""Adapted from https://github.com/ysymyth/ReAct/blob/master/alfworld.ipynb"""

import os
import sys
import json
import yaml
import shutil
import openai
import importlib
import alfworld
import alfworld.agents.environment
from utils import Model, get_chat, get_completion
from env_history import EnvironmentHistory
from scene_graph import *

from buffer import Buffer
from ruleminer import RuleMiner
from rulesverification import RuleVerifier

from typing import List, Dict, Any, Tuple
 

########## ! model initialization ##########
model_name = 'gpt-4o-mini' # 'gpt-4o-mini' # 'gpt-4o'
env_name = 'alfworld'
io_dir = '/home/sawyer/Workspace/wall-e_alfworld'
buffer = Buffer(io_dir = io_dir, env_name = env_name, model_name = model_name)
miner = RuleMiner(io_dir = io_dir, env_name = env_name, model_name=model_name)  # Create a RuleMiner instance
ruleverifier = RuleVerifier(env_name = env_name, io_dir = io_dir)

interval = 5 # 1
########## ! model initialization ##########


openai.api_key = os.environ["OPENAI_API_KEY"]
FOLDER = io_dir + '/prompts'
PROMPT_FILE = 'alfworld_3prompts.json'
with open(os.path.join(FOLDER, PROMPT_FILE), 'r') as f:
    d = json.load(f)

def llm(prompt: str, model: Model, stop: List[str] = ["\n"]):
    try:
        cur_try = 0
        while cur_try < 6:
            if model == "text-davinci-003":
                text = get_completion(prompt=prompt, temperature=cur_try * 0.2, stop_strs=stop)
            else:
                text = get_chat(prompt=prompt, model=model, temperature=cur_try * 0.2, stop_strs=stop)
            # dumb way to do this
            if len(text.strip()) >= 5:
                return text
            cur_try += 1
        return ""
    except Exception as e:
        print(prompt)
        print(e)
        import sys
        sys.exit(1)

def process_ob(ob):
    if ob.startswith('You arrive at loc '):
        ob = ob[ob.find('. ')+2:]    
    return ob

def prcess_action_string(text):
    text = text.replace(' in ', ' in/on ')
    text = text.replace(' on ', ' in/on ')
    return text

def alfworld_run(env, base_prompt, memory: List[str], to_print=True, ob='', model: Model = "text-davinci-003") -> Tuple[EnvironmentHistory, bool]:
    if len(memory) > 3:
        env_history = EnvironmentHistory(base_prompt, ob, memory[-3:], [])
    else:
        env_history = EnvironmentHistory(base_prompt, ob, memory, [])
    env_history.reset()
    if to_print:
        print(ob)
        sys.stdout.flush()
    cur_step = 0



    ##################################################
    # construct initial scene graph with initial observation
    # ! [1. data collection] raw trajectory buffer path 
    ##################################################
    sg = SceneGraph(initialization_info = ob)
    sg_history = []
    # sg.display_graph()
    # sg_file_path = os.path.join(io_dir, 'traj_data', env_name, 'inferenceTime_SG', f'traj_{taskID}', f'transition_info_EnvironmentID{taskID}.json')
    # sg.display_graph()
    ##################################################
    # construct initial scene graph with initial observation
    ##################################################


    while cur_step < 49:
        action_orig = llm(str(env_history) + ">", stop=['\n'], model=model).strip()

        ############ process action_orig ############
        action_orig = re.sub(r'^[^a-zA-Z]+', '', action_orig)
        # List of valid action keywords
        valid_actions = ["go to", "open", "close", "take", "put", "clean", "heat", "cool", "use", "look"]
        action = action_orig
        for action_keyword in valid_actions:
            if action_orig.startswith(action_keyword):
                if action_keyword == 'put':
                    action = prcess_action_string(action_orig)

        if action.startswith('To solve'):
            action = 'think: ' + action
        ############ process action_orig ############

        env_history.add("action", action)
        observation, reward, done, info = env.step([action])
        observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]
        if action.startswith('think:'):
            observation = 'OK.'
        env_history.add("observation", observation)


        ##################################################
        # update scene graph with action and observation at each step
        # ! [1. data collection] raw trajectory buffer path 
        ##################################################
        for action_keyword in valid_actions:
            if action.startswith(action_keyword):
                sg_history.append(copy.deepcopy(sg.graph))
                interaction_info = '> ' + action + '\n' + observation
                sg.update_graph(interaction_info)
        # sg.display_graph()
        # sg.save_to_json(f"/home/sawyer/Workspace/reflexion/alfworld_runs/buffer_SG-{exp_mode}_{model_type}/traj_{z}/transition_info_EnvironmentID{z}.json")
        ##################################################
        # update scene graph with action and observation at each step
        ##################################################

    
        if to_print:
            print(f'> {action}\n{observation}')
            sys.stdout.flush()
        if done:
            return env_history, True, sg_history
        # if the action is the same as the previous action, terminate the interaction
        elif env_history.check_is_exhausted():
            return env_history, False, sg_history
        cur_step += 1
    return env_history, False, sg_history

PREFIXES = {
    'pick_and_place': 'put',
    'pick_clean_then_place': 'clean',
    'pick_heat_then_place': 'heat',
    'pick_cool_then_place': 'cool',
    'look_at_obj': 'examine',
    'pick_two_obj': 'puttwo'
}

def run_trial(
        trial_log_path: str,
        world_log_path: str,
        trial_idx: int,
        env_configs: List[Dict[str, Any]],
        use_memory: bool,
        model: Model,
    ) -> List[Dict[str, Any]]:
    importlib.reload(alfworld)
    importlib.reload(alfworld.agents.environment)


    ####################### ! clear buffer_traj and buffer_SG #######################
    # Delete all files and subdirectories in buffer_traj after processing all trajectories
    buffer_traj_dir = os.path.join(io_dir, 'traj_data', env_name, 'buffer_traj')
    if os.path.exists(buffer_traj_dir):
        for item in os.listdir(buffer_traj_dir):
            item_path = os.path.join(buffer_traj_dir, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception as e:
                print(f"Error deleting {item_path}: {e}")

    buffer_sg_dir = os.path.join(io_dir, 'traj_data', env_name, 'buffer_SG')
    if os.path.exists(buffer_sg_dir):
        for item in os.listdir(buffer_sg_dir):
            item_path = os.path.join(buffer_sg_dir, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception as e:
                print(f"Error deleting {item_path}: {e}")
    ####################### ! clear buffer_traj and buffer_SG #######################




    with open('/home/sawyer/Workspace/alfworld/configs/base_config.yaml') as reader:
        config = yaml.safe_load(reader)
    split = "train" # eval_out_of_distribution

    env = getattr(alfworld.agents.environment, config["env"]["type"])(config, train_eval=split)
    env = env.init_env(batch_size=1)

    num_successes: int = 0
    num_additional_successes: int = 0
    num_envs: int = len(env_configs)

    for z, env_config in enumerate(env_configs):
        task_id = z
        ob, info = env.reset()
        ob = '\n'.join(ob[0].split('\n\n')[1:])
        name = '/'.join(info['extra.gamefile'][0].split('/')[-3:-1])

        print(f"using {name}")

        if env_config["is_success"]:
            num_successes += 1

            # log to world log
            with open(world_log_path, 'a') as wf:
                wf.write(f'Environment #{z} Trial #{trial_idx}: SUCCESS\n')
            with open(trial_log_path, 'a') as wf:
                wf.write(f'\n#####\n\nEnvironment #{z}: Success\n\n#####\n')
            continue

        for i, (k, v) in enumerate(PREFIXES.items()):
            if name.startswith(k):
                base_prompt = 'Interact with a household to solve a task. Here are two examples.\n' + d[f'react_{v}_1'] + d[f'react_{v}_0']
                # use the memory generated in the last round
                final_env_history, is_success, sg_history = alfworld_run(env, base_prompt, env_config["memory"] if use_memory else [], to_print=True, ob=ob, model=model)

                # update env config
                if is_success:
                    status_str: str = f'Environment #{z} Trial #{trial_idx}: SUCCESS'
                    env_configs[z]['is_success'] = True
                    num_successes += 1
                    num_additional_successes += 1
                else:
                    status_str: str = f'Environment #{z} Trial #{trial_idx}: FAIL'

                # log to world log
                with open(world_log_path, 'a') as f:
                    f.write(status_str + '\n')

                # log env results to trial log
                with open(trial_log_path, 'a') as wf:
                    wf.write(f'\n#####\n\nEnvironment #{z}:\n{str(final_env_history)}\n\nSTATUS: {"OK" if is_success else "FAIL"}\n\n#####\n')
                
                print(f'look: i: {i}, k: {k}, v: {v}')


                ####################
                # ! [1. data collection] raw trajectory buffer path 
                file_path = os.path.join(io_dir, 'traj_data', env_name, 'buffer_traj', f'traj_{z}', f'transition_info_EnvironmentID{z}_Trial#{trial_idx}.json')
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    # json.dump(final_env_history, f, cls=NumpyEncoder, indent=4)
                    f.write(str(final_env_history))
                print(f'look: file_path: {file_path}')

                sg_history_file = os.path.join(io_dir, 'traj_data', env_name, 'buffer_SG', f'traj_{z}', f'sg_transition_info_EnvironmentID{z}_Trial#{trial_idx}.json')
                os.makedirs(os.path.dirname(sg_history_file), exist_ok=True)
                # with open(sg_history_file, 'w') as f:
                #     f.write(str(sg_history))
                with open(sg_history_file, 'w') as f:
                    json.dump(sg_history, f)
                print(f'look: sg_history_file: {sg_history_file}')
                ####################

        ####################
        # ! [1. data collection] raw trajectory --> json format
        if (task_id + 1) % interval == 0 or (task_id + 1 == num_envs and (task_id + 1) % interval):
            if task_id + 1 == num_envs and (task_id + 1) % interval:
                current_interval = (task_id + 1) % interval
            else:
                current_interval = interval
            start_task_id = max(0, task_id + 1 - current_interval)

            ## Stage : transition buffering
            # ! [1. data collection] raw trajectory --> json format
            buffer.string_buffer_for_transitions_pure(current_interval, start_task_id)

            # ! [2. rules mining] rules mining
            miner.get_rules_all()

            # [Stage 1] rules code generation
            #######################
            ruleverifier.rules_code_all()
            # [Stage 2] rules code verification
            #######################
            ruleverifier.functions_verification()
            # [Stage 3] rules selection
            # selected_rules, sorted_rules, pruned_functions_set_string = ruleverifier.select_rules()
            ruleverifier.select_rules()

            if task_id >= 100:
                break
        ####################




    # close environment object
    env.close()

    # log trial results to trial and world logs
    log_str: str = f"""
-----
SUCCESS: {num_successes}
ADDITIONAL SUCCESS: {num_additional_successes}
FAIL: {num_envs - num_successes}
TOTAL: {num_envs}
ACCURACY: {round(num_successes / num_envs, 2)}
-----"""
    with open(trial_log_path, 'a') as wf:
        wf.write(log_str)
    with open(world_log_path, 'a') as wf:
        wf.write(log_str + '\n')

    return env_configs
