from utilsextra import *
import os
import json
import shutil
from stateinfo_transform import *


def LLM_request(request, max_retries = 5):
    llm = ChatOpenAI( model_name="gpt-5-nano", temperature=0) # ! change to gpt-4
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
    def __init__(self, io_dir, env_name, model_name="gpt-4o", temperature=0):
        """ Initializes the buffer with a specific model configuration. """

        self.llm = ChatOpenAI(
            model_name=model_name, 
            temperature=temperature, 
            response_format = { "type": "json_object" }
            )
        
        self.io_dir = io_dir
        self.env_name = env_name
        self.prompt_dir = io_dir + '/prompts'
        self.trajData_dir = io_dir + '/traj_data'
        self.rules_dir = io_dir + '/symbolic_knowledge/'
        self.record_wrong = {}
        self.record_correct = {}

        self.functions_set = []
        self.rule_code_file = os.path.join(self.rules_dir, self.env_name, 'pruned_rules_code.json')
        if self.rule_code_file is None:
            pass
        else:
            self.load_functions_from_file(self.rule_code_file)


    def load_functions_from_file(self, code_file):
        # load functions from file
        with open(code_file, 'r') as f:
            function_strings = json.load(f)
        
        for func_str in function_strings:
            # convert the string形式的函数 to executable function
            exec(func_str, globals())
            # use regex to extract the function name
            func_name = re.search(r'def\s+(\w+)\s*\(', func_str).group(1)
            self.functions_set.append(globals()[func_name])

    def run_all_functions(self, state, action, sg):
        # run all functions in self.functions_set

        for func in self.functions_set:
            feedback, success, suggestion = func(state=state, action=action, scene_graph = sg)
            if not success:  # if the function returns False
                action_result = {
                    "feedback": feedback,
                    "success": success,
                    "suggestion": suggestion
                }
                return action_result
        action_result = {
            "feedback": "You completed the action successfully.",
            "success": True,
            "suggestion": ""
        }
        return action_result
    

    # ! [3. test with code rules] get world code prediction
    def worldcode_get_prediction(self, state, action, sg):
        feedback = "You completed the action successfully."
        act_success = True
        suggestion = ''

        if self.functions_set:
            success = self.run_all_functions(state, action, sg)
            if not success['success']:
                print("!!!!!!!!!rules code predict fail")
                # if rule violation is detected
                act_success = success['success']
                feedback = success['feedback']
                suggestion = success['suggestion']

        action_result = {
            "feedback": feedback,
            "success": act_success,
            "suggestion": suggestion
        }

        return action_result


    # ! [*3. in context learning] 
    def worldmodel_get_prediction(self, state, action, sg=None, with_rules=False, max_retries=5):

        if max_retries == 0:
            log_info("************Failed to get workflow. Consider updating your prompt.************\n\n")
            return {}
        try:
            prompt_file = os.path.join(self.prompt_dir, 'world_model_system_' + self.env_name + '.txt')
            world_model_system = load_text(prompt_file)# .replace("<examples>", examples)
            prompt_file = os.path.join(self.prompt_dir, 'world_model_query.txt')
            world_model_query = load_text(prompt_file).format(
                initial_state=state, 
                action=action
            )
            world_model_query += "\nMake your prediction for 'success'. You should only give the 'success', with out any other information."
                
            messages = [
                SystemMessage(content=world_model_system),
                HumanMessage(content=world_model_query)
            ]

            llm_response = self.llm(messages)
            wm_prediction_dict = llm_response.content
            # ensure the format
            prediction_json = fix_and_parse_json(wm_prediction_dict)
            prediction_json['success']['success'] = self.convert_to_bool(prediction_json['success']['success'])

            if with_rules:
                if sg is not None:
                    success = self.run_all_functions(state, action, sg)
                else:
                    success = self.run_all_functions(state, action)
                prediction_json['success']['success'] = success['success']
                prediction_json['success']['feedback'] = success['feedback']
                prediction_json['success']['suggestion'] = success['suggestion']
                return prediction_json
            return prediction_json

        except Exception as e:
            log_info(f"Error arises in WorldModel prediction part: {e} Trying again!\n\n")
            return self.worldmodel_get_prediction(
                state,
                action,
                max_retries=max_retries - 1
            )

    def string_buffer_for_transitions_pure(self, interval, task_id):
        """ Processes transitions from a task directory and logs them. """
        record_correct_temp = {}
        record_wrong_temp = {}
        for kk in range(interval):
            trajectory_dir = os.path.join(self.trajData_dir, self.env_name, 'buffer_traj', f'traj_{task_id+kk}')
            sg_dir = os.path.join(self.trajData_dir, self.env_name, 'buffer_SG', f'traj_{task_id+kk}')
            files = os.listdir(trajectory_dir)
            # Filter the list to include only JSON files
            json_files = [f for f in files if f.endswith('.json')]
            for json_file in json_files:
                file_path = os.path.join(trajectory_dir, json_file)
                with open(file_path, 'r', encoding='utf-8') as file:
                    # input_str = json.load(file)
                    input_str = file.read()
                sg_str = load_json_file(os.path.join(sg_dir, 'sg_' + json_file))
                
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
                transition_counter = 0
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
                                # add scene graph information at each time step
                                sg_info = sg_str[transition_counter]
                                transition_info = {'initial_state': state, 'action': action, 'action_result': action_result, 'sg_info': sg_info}
                                transition_counter += 1
                                # record_c_w.setdefault(action_keyword, []).append(transition_info)

                                # world model pred collection:
                                predicted_state_1 = self.worldmodel_get_prediction(state=state, action=action)
                                gt = action_result
                                prediction = predicted_state_1['success']['success']

                                if gt != prediction:
                                    # transition_info = {'initial_state': state, 'action': action, 'action_result': action_result}
                                    self.record_wrong.setdefault(action_keyword, []).append(transition_info)
                                    record_wrong_temp.setdefault(action_keyword, []).append(transition_info)
                                    # name_neg = action_keyword+'_negative'
                                    # if name_neg in record:
                                    #     record[name_neg] += 1
                                    # else:
                                    #     record[name_neg] = 1
                                    # transition_info = {'initial_state': state, 'action': action, 'wrong_prediction_result': action_result}
                                    # record_wrong_prediction.setdefault(action_keyword, []).append(transition_info)
                                else:
                                    # transition_info = {'initial_state': state, 'action': action, 'action_result': action_result}
                                    self.record_correct.setdefault(action_keyword, []).append(transition_info)
                                    record_correct_temp.setdefault(action_keyword, []).append(transition_info)
                                    # name_pos = action_keyword+'_positive'
                                    # if name_pos in record:
                                    #     record[name_pos] += 1
                                    # else:
                                    #     record[name_pos] = 1

                                # with open('/home/sawyer/Workspace/reflexion/alfworld_runs/reflexion_run_logs/trajrecord.log', 'a') as wf:
                                #     wf.write(f"\n[State text]: {state_text}")
                                #     wf.write(f"\n[State json]: {state}")
                                #     wf.write(f"\n[Action]: {action}")
                                #     wf.write(f"\n[Action Result]: {action_result}")
                                #     # wf.write(f"\n[Predicted Action Result]: {predicted_state_1}")
                                #     wf.write("\n--------------------------------------------------------\n")
                                break

            with open(os.path.join(self.trajData_dir, self.env_name, 'buffer_wrong_all.json'), 'w') as f:
                json.dump(self.record_wrong, f, indent=4)
            with open(os.path.join(self.trajData_dir, self.env_name, 'buffer_correct_all.json'), 'w') as f:
                json.dump(self.record_correct, f, indent=4)

            with open(os.path.join(self.trajData_dir, self.env_name, 'buffer_wrong_temp.json'), 'w') as f:
                json.dump(record_wrong_temp, f, indent=4)
            with open(os.path.join(self.trajData_dir, self.env_name, 'buffer_correct_temp.json'), 'w') as f:
                json.dump(record_correct_temp, f, indent=4)

            # with open(f'/home/sawyer/Workspace/reflexion/alfworld_runs/buffer_fact/buffer_c_w_taskID{task_id}_interval{interval}.json', 'w') as f:
            #     json.dump(record_c_w, f, indent=4)
            # with open(f'/home/sawyer/Workspace/reflexion/alfworld_runs/buffer_fact/buffer_prediction_record_taskID{task_id}_interval{interval}.json', 'w') as f:
            #     json.dump(record, f, indent=4)
            # with open(f'/home/sawyer/Workspace/reflexion/alfworld_runs/buffer_fact/[fordebug]buffer_wrong_prediction_taskID{task_id}_interval{interval}.json', 'w') as f:
            #     json.dump(record_wrong_prediction, f, indent=4)
        
        # Delete all files and subdirectories in buffer_traj after processing all trajectories
        buffer_traj_dir = os.path.join(self.trajData_dir, self.env_name, 'buffer_traj')
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

        buffer_sg_dir = os.path.join(self.trajData_dir, self.env_name, 'buffer_SG')
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


    def convert_to_bool(self, value):
        # if the value is already a boolean, return it
        if isinstance(value, bool):
            return value
        # if the value is a string, convert it to a boolean
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ["true", "1", "yes"]:
                return True
            elif lower_value in ["false", "0", "no"]:
                return False
        # if not the above cases, keep the original value
        return value

    ## through whole trajectory for buffer
    ## use it after completing/failing a task
    def buffer_for_transitions_pure(self, interval, task_id):
        """ Processes transitions from a task directory and logs them. """
        for kk in range(interval):
            trajectory_dir = f"/home/sawyer/Workspace/MP5/MP5_agent/agent/buffer_traj-trainingset/traj_{task_id+kk}"
            
            files = os.listdir(trajectory_dir)
            # Filter the list to include only JSON files
            json_files = [f for f in files if f.endswith('.json')]

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

        with open(f'/home/sawyer/Workspace/MP5/MP5_agent/agent/buffer_fact/buffer_wrong_taskID{task_id}_interval{interval}.json', 'w') as f:
            json.dump(self.record_wrong, f, indent=4)
        with open(f'/home/sawyer/Workspace/MP5/MP5_agent/agent/buffer_fact/buffer_correct_taskID{task_id}_interval{interval}.json', 'w') as f:
            json.dump(self.record_correct, f, indent=4)
        
        with open(f'/home/sawyer/Workspace/MP5/MP5_agent/agent/buffer_trans_memory/buffer_trans_memory_taskID{task_id}_interval{interval}.json', 'w') as f:
            json.dump(self.memory.transition, f, indent=4)
        print(f'[Stage]buffer_for_transitions--task_id:{task_id}')


    ## through whole trajectory for buffer
    ## use it after completing/failing a task
    def buffer_for_wmtest(self, trajectory_dir, worldmodelstyle):
        """ Processes transitions from a task directory and logs them. """
        record = {}

        for root, dirs, files in os.walk(trajectory_dir):
            for file in files:
                if file.endswith('.json'):  # 查找JSON文件
                    file_path = os.path.join(root, file)

                    with open(file_path, 'r', encoding='utf-8') as file:
                        trajectory = json.load(file)

                    num_steps = len(trajectory) - 3
                    for i in range(1, num_steps, 3): # 0 element is for "task info"
                        state_0 = trajectory[i]
                        action = trajectory[i + 1]
                        action_success = trajectory[i + 2]
                        predicted_state_1 = self.worldmodel_get_prediction(state=state_0, action=action)

                        positive=action_success['success']['success']
                        negative=predicted_state_1['success']['success']
                        if positive != negative: # state info中添加一个action success项，记录上一个action是否成功
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

                        with open(f'/home/sawyer/Workspace/MP5/MP5_agent/agent/task_result_worldmodel/world_model_test_statistic_[{worldmodelstyle}].json', 'w') as f:
                            json.dump(record, f, indent=4)
                        with open(f'/home/sawyer/Workspace/MP5/MP5_agent/agent/task_result_worldmodel/world_model_test_wrongpredict_[{worldmodelstyle}].json', 'w') as f:
                            json.dump(self.record_wrong, f, indent=4)
                        with open(f'/home/sawyer/Workspace/MP5/MP5_agent/agent/task_result_worldmodel/world_model_test_rightpredict_[{worldmodelstyle}].json', 'w') as f:
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

    model_name = 'gpt-4o-mini' # 'gpt-4o-mini' # 'gpt-4o'
    env_name = 'alfworld'
    io_dir = '/home/sawyer/Workspace/reflexion'
    buffer = Buffer(io_dir = io_dir, env_name = env_name, model_name = model_name)
    start_task_id = 0
    current_interval = 1
    buffer.string_buffer_for_transitions_pure(current_interval, start_task_id)
    print("buffer_for_transitions_pure is completed")

