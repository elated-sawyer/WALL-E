from utilsextra import *
import os
import json
from stateinfo_transform import *

# openai.api_key = os.environ["OPENAI_API_KEY"]
FOLDER = '/home/**/Workspace/reflexion/alfworld_runs/prompts'
PROMPT_FILE = 'alfworld_3prompts.json'
with open(os.path.join(FOLDER, PROMPT_FILE), 'r') as f:
    d = json.load(f)

def LLM_request(request, max_retries = 5):
    llm = ChatOpenAI( model_name="gpt-4o", temperature=0)
    if max_retries == 0:
        log_info("************Failed to get workflow. Consider updating your prompt.************\n\n")
        return {}
    try:
        llmrequest_system = "You're an expert in Minecraft. You can help answer some questions related to gameplay mechanics, strategies, and item usage."
        llmrequest_query = request
        messages = [
            SystemMessage(content=llmrequest_system),
            HumanMessage(content=llmrequest_query)
        ]

        llm_response = llm(messages)
        llm_response = llm_response.content
        llm_response = re.sub(r'^[^\w]+|[^\w]+$', '', llm_response)

        return llm_response
        # debug #######################
    except Exception as e:
        log_info(f"Error arises in WorldModel prediction part: {e} Trying again!\n\n")

        return LLM_request(
            request,
            max_retries=max_retries - 1
        )



class Buffer:
    """ Manages state transitions and logs results for analysis. """
    def __init__(self, worldmodel_mode = 'rules', rules_dir=None, rule_code_file = None, tran_memory_dir = None, model_name="gpt-4o", temperature=0):
        """ Initializes the buffer with a specific model configuration. """


        self.llm = ChatOpenAI(
            model_name=model_name, 
            temperature=temperature, 
            response_format = { "type": "json_object" }
            )

        self.worldmodel_mode = worldmodel_mode

        try:
            self.record_wrong = load_json_file('/home/**/Workspace/MP5/MP5_agent/agent/buffer_fact/buffer_wrong.json')
        except:
            self.record_wrong = {}
        try:
            self.record_correct = load_json_file('/home/**/Workspace/MP5/MP5_agent/agent/buffer_fact/buffer_correct.json')
        except:
            self.record_correct = {}
        
        if rules_dir is None:
            self.rules = {}
        else:
            self.rules = load_json_file(rules_dir)


        if tran_memory_dir is None:
            self.tran_memory = {}
        else:
            self.tran_memory = load_json_file(tran_memory_dir)

        self.functions_set = []
        if rule_code_file is None:
            pass
        else:
            self.load_functions_from_file(rule_code_file)

    def load_functions_from_file(self, code_file):
        with open(code_file, 'r') as f:
            function_strings = json.load(f)
        
        for func_str in function_strings:
            exec(func_str, globals())
            func_name = re.search(r'def\s+(\w+)\s*\(', func_str).group(1)
            self.functions_set.append(globals()[func_name])

    def run_all_functions(self, state, action):
        for func in self.functions_set:
            feedback, success, suggestion = func(state=state, action=action)
            if not success:  
                action_result = {
                    "feedback": feedback,
                    "success": success,
                    "suggestion": suggestion
                }
                print(action_result)
                return action_result
        action_result = {
            "feedback": "You completed the action successfully.",
            "success": True,
            "suggestion": ""
        }
        return action_result

    def worldcode_get_prediction(self, state, action):
        feedback = "You completed the action successfully."
        act_success = True
        suggestion = ''
        if self.functions_set:
            success = self.run_all_functions(state, action)
            if not success['success']:
                act_success = success['success']
                feedback = success['feedback']
                suggestion = success['suggestion']
        action_result = {
            "feedback": feedback,
            "success": act_success,
            "suggestion": suggestion
        }
        return action_result



    def worldmodel_get_prediction(self, state, action, max_retries=5):

        # TODO to be check
        # examples = 'Interact with a household to solve a task. Here are some examples.\n' + d[f'react_put_1'] + d[f'react_cool_0'] + d[f'react_heat_0']

        if max_retries == 0:
            log_info("************Failed to get workflow. Consider updating your prompt.************\n\n")
            return {}

        try:
            
            valid_actions = ["go to", "open", "close", "take", "put", "clean", "heat", "cool", "use", "look"]
            for act_type in valid_actions:
                if action.startswith(act_type):
                    break
      
            rules_act = self.rules.get(act_type, [])
            rules_string = list_to_prompt(rules_act)

            # world_model_system = load_prompt("world_model_system").format(rules=rules_string)
            world_model_system = load_prompt("world_model_system").replace("<rules>", rules_string) # .replace("<examples>", examples)
            if self.worldmodel_mode == 'rules':
                world_model_query = load_prompt("world_model_query").format(
                    inital_state=state, 
                    action=action
                )
            elif self.worldmodel_mode == 'ref':
                # reference_transitions = list_dict_to_prompt(self.memory.search_transitions(action))
                reference_transitions = list_dict_to_prompt(self.tran_memory.get(action['name'], [])) 
                world_model_query = load_prompt("world_model_query_withRef").format(
                    state=state, 
                    action=action,
                    reference_transitions = reference_transitions
                )
            else:
                raise NotImplementedError
            world_model_query += "\nMake your prediction for 'rules check', 'success'. You should only give the 'rules check', 'success', with out any other information."
                
            messages = [
                SystemMessage(content=world_model_system),
                HumanMessage(content=world_model_query)
            ]

            llm_response = self.llm(messages)
            wm_prediction_dict = llm_response.content

            # ensure the format
            prediction_json = fix_and_parse_json(wm_prediction_dict)
            prediction_json['success']['success'] = self.convert_to_bool(prediction_json['success']['success'])
            if self.functions_set:
                if prediction_json['success']['success']:
                    success = self.run_all_functions(state, action)
                    if not success['success']:
                        prediction_json['state 1'] = state
                        prediction_json['success'] = success
                        prediction_json['rules check'] = 99
                        return prediction_json
            return prediction_json
            # debug #######################
        except Exception as e:
            log_info(f"Error arises in WorldModel prediction part: {e} Trying again!\n\n")
            return self.worldmodel_get_prediction(
                state,
                action,
                max_retries=max_retries - 1
            )

    def string_buffer_for_transitions_pure(self, interval, task_id):
        """ Processes transitions from a task directory and logs them. """
        record_c_w = {}
        record_correct = {}
        record_wrong = {}
        record = {}
        record_wrong_prediction = {}
        for kk in range(interval):
            trajectory_dir = f'/home/**/Workspace/reflexion/alfworld_runs/buffer_traj-testset_agent/traj_{task_id+kk}' # for test set
            files = os.listdir(trajectory_dir)
            # Filter the list to include only JSON files
            json_files = [f for f in files if f.endswith('.json')]
            for json_file in json_files:
                file_path = os.path.join(trajectory_dir, json_file)
                with open(file_path, 'r', encoding='utf-8') as file:
                    # input_str = json.load(file)
                    input_str = file.read()

                # Step 1: Remove everything before "Here is the task:"
                task_start_idx = input_str.find("Here is the task:")
                if task_start_idx != -1:
                    input_str = input_str[task_start_idx:]
                
                # Step 2: Initialize variables
                state_text = ""
                action_text = ""
                action_result = False
                
                # List of valid action keywords
                valid_actions = ["go to", "open", "close", "take", "put", "clean", "heat", "cool", "use", "look"]
                
                # Step 3: Split input string into lines and iterate through them
                lines = input_str.splitlines()
                for i, line in enumerate(lines):
                    # Step 4: Check if line starts with '>'
                    if line.strip().startswith('>'):
                        # Step 5: Strip leading non-alphanumeric characters and check for valid actions
                        stripped_line = line.lstrip("> ").strip()
                        for action_keyword in valid_actions:
                            if stripped_line.startswith(action_keyword):
                                # Store the action
                                action_text = stripped_line
                                # Store the state (everything before this line)
                                state_text = "\n".join(lines[:i])
                                # Step 6: Determine the result (check the next line)

                                # Find the position of the first newline character
                                newline_index = state_text.find('\n')
                                # Remove everything before and including the first newline character
                                if newline_index != -1:
                                    state_text = state_text[newline_index + 1:]
                                
                                if i + 1 < len(lines) and lines[i + 1].strip() == "Nothing happens.":
                                    action_result = False
                                else:
                                    action_result = True


                                # state transfer:
                                ##################
                                state = state_info_transformation(state_text)
                                action = convert_action(action_text)


                                # pure collection:
                                ##################
                                transition_info = {'inital_state': state, 'action': action, 'action_result': action_result}
                                record_c_w.setdefault(action_keyword, []).append(transition_info)

                                # # wm pred collection:
                                # ##################
                                # predicted_state_1 = self.worldmodel_get_prediction(state=state, action=action)
                                # positive=action_result
                                # negative=predicted_state_1['success']['success']
                                # if positive != negative: 
                                #     transition_info = {'inital_state': state, 'action': action, 'action_result': action_result}
                                #     record_wrong.setdefault(action_keyword, []).append(transition_info)
                                #     name_neg = action_keyword+'_negative'
                                #     if name_neg in record:
                                #         record[name_neg] += 1
                                #     else:
                                #         record[name_neg] = 1
                                #     transition_info = {'inital_state': state, 'action': action, 'wrong_prediction_result': predicted_state_1}
                                #     record_wrong_prediction.setdefault(action_keyword, []).append(transition_info)
                                # else:
                                #     transition_info = {'inital_state': state, 'action': action, 'action_result': predicted_state_1}
                                #     record_correct.setdefault(action_keyword, []).append(transition_info)
                                #     name_pos = action_keyword+'_positive'
                                #     if name_pos in record:
                                #         record[name_pos] += 1
                                #     else:
                                #         record[name_pos] = 1

                                # wm pred collection:
                                ##################
                                positive=action_result
                                if positive == False: 
                                    transition_info = {'inital_state': state, 'action': action, 'action_result': action_result}
                                    record_wrong.setdefault(action_keyword, []).append(transition_info)
                                    name_neg = action_keyword+'_negative'
                                    if name_neg in record:
                                        record[name_neg] += 1
                                    else:
                                        record[name_neg] = 1
                                    transition_info = {'inital_state': state, 'action': action, 'wrong_prediction_result': action_result}
                                    record_wrong_prediction.setdefault(action_keyword, []).append(transition_info)
                                else:
                                    transition_info = {'inital_state': state, 'action': action, 'action_result': action_result}
                                    record_correct.setdefault(action_keyword, []).append(transition_info)
                                    name_pos = action_keyword+'_positive'
                                    if name_pos in record:
                                        record[name_pos] += 1
                                    else:
                                        record[name_pos] = 1


                                # # Print or store the result (depending on your use case)
                                # print(f"[State text]: {state_text}")
                                # print(f"[State json]: {state}")
                                # print(f"[Action]: {action}")
                                # print(f"[Action Result]: {action_result}")
                                # # print(f"[Predicted Action Result]: {predicted_state_1}")
                                # print("------------------")

                                with open('/home/**/Workspace/reflexion/alfworld_runs/reflexion_run_logs/trajrecord.log', 'a') as wf:
                                    wf.write(f"\n[State text]: {state_text}")
                                    wf.write(f"\n[State json]: {state}")
                                    wf.write(f"\n[Action]: {action}")
                                    wf.write(f"\n[Action Result]: {action_result}")
                                    # wf.write(f"\n[Predicted Action Result]: {predicted_state_1}")
                                    wf.write("\n--------------------------------------------------------\n")
                                break

                with open(f'/home/**/Workspace/reflexion/alfworld_runs/buffer_fact/buffer_wrong_taskID{task_id}_interval{interval}.json', 'w') as f:
                    json.dump(record_wrong, f, indent=4)
                with open(f'/home/**/Workspace/reflexion/alfworld_runs/buffer_fact/buffer_correct_taskID{task_id}_interval{interval}.json', 'w') as f:
                    json.dump(record_correct, f, indent=4)
                with open(f'/home/**/Workspace/reflexion/alfworld_runs/buffer_fact/buffer_c_w_taskID{task_id}_interval{interval}.json', 'w') as f:
                    json.dump(record_c_w, f, indent=4)
                with open(f'/home/**/Workspace/reflexion/alfworld_runs/buffer_fact/buffer_prediction_record_taskID{task_id}_interval{interval}.json', 'w') as f:
                    json.dump(record, f, indent=4)
                with open(f'/home/**/Workspace/reflexion/alfworld_runs/buffer_fact/[fordebug]buffer_wrong_prediction_taskID{task_id}_interval{interval}.json', 'w') as f:
                    json.dump(record_wrong_prediction, f, indent=4)

            with open(f'/home/**/Workspace/reflexion/alfworld_runs/buffer_fact/buffer_wrong_taskID{task_id}_interval{interval}.json', 'w') as f:
                json.dump(record_wrong, f, indent=4)
            with open(f'/home/**/Workspace/reflexion/alfworld_runs/buffer_fact/buffer_correct_taskID{task_id}_interval{interval}.json', 'w') as f:
                json.dump(record_correct, f, indent=4)
            with open(f'/home/**/Workspace/reflexion/alfworld_runs/buffer_fact/buffer_c_w_taskID{task_id}_interval{interval}.json', 'w') as f:
                json.dump(record_c_w, f, indent=4)
            with open(f'/home/**/Workspace/reflexion/alfworld_runs/buffer_fact/buffer_prediction_record_taskID{task_id}_interval{interval}.json', 'w') as f:
                json.dump(record, f, indent=4)
            with open(f'/home/**/Workspace/reflexion/alfworld_runs/buffer_fact/[fordebug]buffer_wrong_prediction_taskID{task_id}_interval{interval}.json', 'w') as f:
                json.dump(record_wrong_prediction, f, indent=4)


    def convert_to_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ["true", "1", "yes"]:
                return True
            elif lower_value in ["false", "0", "no"]:
                return False
        return value

    ## through whole trajectory for buffer
    ## use it after completing/failing a task
    def buffer_for_transitions(self, interval, task_id):
        """ Processes transitions from a task directory and logs them. """
        ########################
        for kk in range(interval):
            trajectory_dir = f"/home/**/Workspace/MP5/MP5_agent/agent/buffer_traj-trainingset/traj_{task_id+kk}"
            
            files = os.listdir(trajectory_dir)
            # Filter the list to include only JSON files
            json_files = [f for f in files if f.endswith('.json')]
        ########################

            # # debug 
            # json_files = json_files[9:]
            for json_file in json_files:
                file_path = os.path.join(trajectory_dir, json_file)
                with open(file_path, 'r', encoding='utf-8') as file:
                    trajectory = json.load(file)

                num_steps = len(trajectory) - 3
                for i in range(1, num_steps, 3): # 0 element is for "task info"
                    state_0 = trajectory[i]
                    action = trajectory[i + 1]
                    action_success = trajectory[i + 2]
                    predicted_state_1 = self.worldmodel_get_prediction(state=state_0, action=action)
                    # check_result = self.state_checker(positive=action_success, negative=predicted_state_1['success'])
                    # if not check_result.get('is_same', True):  # Assume true if 'is_same' is missing
                    #     transition_info = {'state_0': state_0, 'action': action, 'state_1': state_1, 'check_result': check_result}
                    #     self.record.setdefault(action['name'], []).append(transition_info)

                    positive=action_success['success']['success']
                    negative=predicted_state_1['success']['success']
                    if positive != negative: 
                        transition_info = {'state_0': state_0, 'action': action, 'action_result': action_success}
                        self.record_wrong.setdefault(action['name'], []).append(transition_info)
                    else:
                        transition_info = {'state_0': state_0, 'action': action, 'action_result': predicted_state_1}
                        self.record_correct.setdefault(action['name'], []).append(transition_info)
                        # TODO to be check
                        self.memory.add_successful_transition(action, transition_info)
                
                with open(f'/home/**/Workspace/MP5/MP5_agent/agent/buffer_fact/buffer_wrong_taskID{task_id}_interval{interval}_negativesamples.json', 'w') as f:
                    json.dump(self.record_wrong, f, indent=4)
                with open(f'/home/**/Workspace/MP5/MP5_agent/agent/buffer_fact/buffer_correct_taskID{task_id}_interval{interval}_negativesamples.json', 'w') as f:
                    json.dump(self.record_correct, f, indent=4)
                print(f'{file_path} collection is completed')

        with open(f'/home/**/Workspace/MP5/MP5_agent/agent/buffer_fact/buffer_wrong_taskID{task_id}_interval{interval}_negativesamples.json', 'w') as f:
            json.dump(self.record_wrong, f, indent=4)
        with open(f'/home/**/Workspace/MP5/MP5_agent/agent/buffer_fact/buffer_correct_taskID{task_id}_interval{interval}_negativesamples.json', 'w') as f:
            json.dump(self.record_correct, f, indent=4)
        
        with open(f'/home/**/Workspace/MP5/MP5_agent/agent/buffer_trans_memory/buffer_trans_memory_taskID{task_id}_interval{interval}.json', 'w') as f:
            json.dump(self.memory.transition, f, indent=4)
        print(f'[Stage]buffer_for_transitions--task_id:{task_id}')


    ## through whole trajectory for buffer
    ## use it after completing/failing a task
    def buffer_for_transitions_pure(self, interval, task_id):
        """ Processes transitions from a task directory and logs them. """
        ########################
        for kk in range(interval):
            trajectory_dir = f"/home/**/Workspace/MP5/MP5_agent/agent/buffer_traj-trainingset/traj_{task_id+kk}"
            
            files = os.listdir(trajectory_dir)
            # Filter the list to include only JSON files
            json_files = [f for f in files if f.endswith('.json')]
        ########################

            # # debug 
            # json_files = json_files[9:]
            for json_file in json_files:
                file_path = os.path.join(trajectory_dir, json_file)
                with open(file_path, 'r', encoding='utf-8') as file:
                    trajectory = json.load(file)

                num_steps = len(trajectory) - 3
                for i in range(1, num_steps, 3): # 0 element is for "task info"
                    state_0 = trajectory[i]
                    action = trajectory[i + 1]
                    action_success = trajectory[i + 2]

                    transition_info = {'state_0': state_0, 'action': action, 'action_result': action_success}
                    self.record_wrong.setdefault(action['name'], []).append(transition_info)
                    self.memory.add_successful_transition(action, transition_info)

        with open(f'/home/**/Workspace/MP5/MP5_agent/agent/buffer_fact/buffer_wrong_taskID{task_id}_interval{interval}.json', 'w') as f:
            json.dump(self.record_wrong, f, indent=4)
        with open(f'/home/**/Workspace/MP5/MP5_agent/agent/buffer_fact/buffer_correct_taskID{task_id}_interval{interval}.json', 'w') as f:
            json.dump(self.record_correct, f, indent=4)
        
        with open(f'/home/**/Workspace/MP5/MP5_agent/agent/buffer_trans_memory/buffer_trans_memory_taskID{task_id}_interval{interval}.json', 'w') as f:
            json.dump(self.memory.transition, f, indent=4)
        print(f'[Stage]buffer_for_transitions--task_id:{task_id}')


    ## through whole trajectory for buffer
    ## use it after completing/failing a task
    def buffer_for_wmtest(self, trajectory_dir, worldmodelstyle):
        """ Processes transitions from a task directory and logs them. """
        record = {}

        for root, dirs, files in os.walk(trajectory_dir):
            for file in files:
                if file.endswith('.json'):  
                    file_path = os.path.join(root, file)

                    with open(file_path, 'r', encoding='utf-8') as file:
                        trajectory = json.load(file)

                    num_steps = len(trajectory) - 3
                    for i in range(1, num_steps, 3): # 0 element is for "task info"
                        state_0 = trajectory[i]
                        action = trajectory[i + 1]
                        action_success = trajectory[i + 2]
                        predicted_state_1 = self.worldmodel_get_prediction(state=state_0, action=action)
                        # check_result = self.state_checker(positive=action_success, negative=predicted_state_1['success'])
                        # if not check_result.get('is_same', True):  # Assume true if 'is_same' is missing
                        #     transition_info = {'state_0': state_0, 'action': action, 'state_1': state_1, 'check_result': check_result}
                        #     self.record.setdefault(action['name'], []).append(transition_info)

                        positive=action_success['success']['success']
                        negative=predicted_state_1['success']['success']
                        if positive != negative: 
                            transition_info = {'state_0': state_0, 'action': action, 'action_result': action_success}
                            self.record_wrong.setdefault(action['name'], []).append(transition_info)
                            name_neg = action['name']+'_negative'
                            if name_neg in record:
                                record[name_neg] += 1
                            else:
                                record[name_neg] = 1
                        else:
                            transition_info = {'state_0': state_0, 'action': action, 'action_result': predicted_state_1}
                            self.record_correct.setdefault(action['name'], []).append(transition_info)
                            name_pos = action['name']+'_positive'
                            if name_pos in record:
                                record[name_pos] += 1
                            else:
                                record[name_pos] = 1

                        with open(f'/home/**/Workspace/MP5/MP5_agent/agent/task_result_worldmodel/world_model_test_statistic_[{worldmodelstyle}].json', 'w') as f:
                            json.dump(record, f, indent=4)
                        with open(f'/home/**/Workspace/MP5/MP5_agent/agent/task_result_worldmodel/world_model_test_wrongpredict_[{worldmodelstyle}].json', 'w') as f:
                            json.dump(self.record_wrong, f, indent=4)
                        with open(f'/home/**/Workspace/MP5/MP5_agent/agent/task_result_worldmodel/world_model_test_rightpredict_[{worldmodelstyle}].json', 'w') as f:
                            json.dump(self.record_correct, f, indent=4)
                        print(f'{file_path} collection is completed')


    ## use wm for planning
    ## use it before the interaction with env
    def wm_prediction_with_actions(self, state_initial, action_seq, mode=99, task_id=99, every_task_max_retries=99, every_task_max_planning_retries=99):
        planning_traj = []
        count = 0
        cum_reward = 0
        final_state = state_initial
        """ Processes transitions from a task directory and logs them. """
        for i in range(0, len(action_seq), 1): # 0 element is for "task info"
            if i == 0:
                state_0 = state_initial
            else:
                state_0 = predicted_state_1["state 1"]
            action = action_seq[i]
            predicted_state_1 = self.worldmodel_get_prediction(state_0, action, mode)


            if predicted_state_1['success']['success']: 
                count += 1
                cum_reward = count
                final_state = predicted_state_1["state 1"]
                continue
            else:
                return cum_reward, predicted_state_1['success'], count, final_state 
        check_result = {
            "feedback": "",
            "success": True,
            "suggestion": ""
        }
        return cum_reward, check_result, count, final_state 

    def wm_prediction_with_multiple_action_seqs(self, state_initial, multiple_action_seq):
        cum_reward_all = []
        check_result_all = []
        action_num_all = []
        final_state_all = []
        for i in range(0, len(multiple_action_seq), 1): 
            action_seq = multiple_action_seq[i]
            cum_reward, check_result, action_num, final_state = self.wm_prediction_with_actions(state_initial, action_seq)
            if check_result["success"]:
                return action_seq, check_result, final_state
            cum_reward_all.append(cum_reward)
            check_result_all.append(check_result)
            action_num_all.append(action_num)
            final_state_all.append(final_state)
        
        max_reward = max(cum_reward_all)
        max_index = cum_reward_all.index(max_reward)

        action_num_output = action_num_all[max_index]
        action_seq_output = multiple_action_seq[max_index][:action_num_output]
        check_result_output = check_result_all[max_index]
        final_state_output = final_state_all[max_index]

        return action_seq_output, check_result_output, final_state_output


    def update_rules(self, rules_extra):
        self.rules = rules_extra
    

if __name__ == "__main__":
    # model_name = 'gpt-4-turbo'
    model_name = 'gpt-3.5-turbo' # 'gpt-4o-mini' # 'gpt-4o'
    # model_name= "gpt-3.5-turbo"

    
    #rules_dir = '/home/**/Workspace/MP5/MP5_agent/agent/buffer_rules/rules_debug_20240704_135729.json'
    #rules_dir = '/home/**/Workspace/MP5/MP5_agent/agent/buffer_rules/rules_library.json'
    
    # rules_dir = '/home/**/Workspace/MP5/MP5_agent/agent/0_backup/buffer_rules copy 0731/rules_base.json'
    rules_dir = None

    # rules_1 = ['In this context, consider an integer number like 5 and its decimal representation 5.0 to be the same value.']
    buffer = Buffer(worldmodel_mode = 'rules', rules_dir = rules_dir, model_name = model_name)



    ## buffer test
    ##############
    # task_dir = '/home/**/Workspace/MP5/MP5_agent/agent/buffer_traj'
    # buffer.buffer_for_transitions(task_dir)

    ## world model pred test
    ########################
    state_initial = {
            "state_0": {
                "equipment": {
                    "diamond sword": 1.0,
                    "diamond boots": 1.0,
                    "diamond leggings": 1.0,
                    "diamond chestplate": 1.0,
                    "diamond helmet": 1.0,
                    "shield": 1.0
                },
                "inventory": {
                    "diamond sword": 1.0,
                    "air": 0.0,
                    "shears": 1.0,
                    "bucket": 1.0,
                    "wooden pickaxe": 1.0,
                    "diamond pickaxe": 1.0,
                    "dirt": 60.0,
                    "coal": 3.0,
                    "iron ingot": 2,
                    "stick": 1
                },
                "life_stats": {
                    "life": [
                        20.0
                    ],
                    "oxygen": [
                        300.0
                    ],
                    "armor": [
                        20.0
                    ],
                    "food": [
                        20.0
                    ],
                    "saturation": [
                        5.0
                    ],
                    "is_sleeping": False
                },
                "location_stats": {
                    "biome": "plains",
                    "rainfall": [
                        0.4000000059604645
                    ],
                    "temperature": [
                        0.800000011920929
                    ],
                    "is_raining": False,
                    "sky_light_level": [
                        0.1
                    ],
                    "sun_brightness": [
                        0.1
                    ]
                }
            }}
    # with open('/home/**/Workspace/MP5/MP5_agent/agent/buffer_act/action_info_debug_0_1.json', 'r') as f:
    #with open('/home/**/Workspace/MP5/MP5_agent/agent/0_backup/buffer_act copy 0731/action_info_debug_0_2_5.json', 'r') as f:
    with open('/home/**/Workspace/MP5/MP5_agent/agent/0_backup/buffer_act copy 0731/action_info_debug_0_1_5.json', 'r') as f:
        workflow_dict = json.load(f)
    every_task_max_retries = 99
    every_task_max_planning_retries = 99
    check_result = buffer.wm_prediction_with_actions(state_initial, workflow_dict['workflow'], 99, 99, every_task_max_retries, every_task_max_planning_retries)
    print(check_result)
    


