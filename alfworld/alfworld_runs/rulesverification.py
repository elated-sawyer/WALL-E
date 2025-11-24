from utilsextra import *  
import os
import json
import re
import random
import traceback

def LLM_request(request, max_retries = 5):
    llm = ChatOpenAI( model_name="gpt-4o-mini", temperature=0) # ! original: gpt-4o, gpt-5-nano, gpt-4o-mini
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
    except Exception as e:
        log_info(f"Error arises in WorldModel prediction part: {e} Trying again!\n\n")

        return LLM_request(
            request,
            max_retries=max_retries - 1
        )


class RuleVerifier:
    """ Manages state transitions and logs results for analysis. """
    def __init__(self, env_name, io_dir, with_graph=True, model_name="gpt-4o-mini", temperature=0): # ! original: gpt-4o
        """ Initializes the buffer with a specific model configuration. """

        self.env_name = env_name
        self.io_dir = io_dir
        self.rules_dir = io_dir + '/symbolic_knowledge/'
        self.prompt_dir = io_dir + '/prompts'
        self.fact_dir = io_dir + '/traj_data'
        self.with_graph = with_graph
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)

        # Load functions from file
        self.functions_set = []
        self.functions_set_string = []
        self.load_functions()


    def deduplicate_rules(self, verbose=True):
        unique_rules = []
        seen_contents = set()

        for rule in self.functions_set_string:
            # extract the content after the colon (ignore the numbering difference)
            if ":" not in rule:
                continue  # skip the string that does not match the format
            content_after_colon = rule.split(":", 1)[1].strip()

            # if the content has not been seen, keep the rule
            if content_after_colon not in seen_contents:
                seen_contents.add(content_after_colon)

                unique_rules.append(rule)

        if verbose:
            print(f"[deduplication completed] original number: {len(self.functions_set_string)}, deduplicated number: {len(unique_rules)}")

        self.functions_set_string = unique_rules



    def load_functions(self):
        code_file = os.path.join(self.rules_dir, self.env_name, 'rules_code.json')
        previous_pruned_code_file = os.path.join(self.rules_dir, self.env_name, 'pruned_rules_code.json')
        if not os.path.exists(code_file):
            print(f"No functions found in {code_file}")
        else:
            with open(code_file, 'r') as f:
                self.functions_set_string = json.load(f)
            if os.path.exists(previous_pruned_code_file):
                with open(previous_pruned_code_file, 'r') as f:
                    previous_pruned_functions_set_string = json.load(f)
                    self.functions_set_string += previous_pruned_functions_set_string
                    self.deduplicate_rules()
            else:
                print(f"No previous pruned code found in {previous_pruned_code_file}, start from scratch")
            print(f"Loaded {len(self.functions_set_string)} functions.")
            for func_str in self.functions_set_string:
                # Preprocess function string: replace spaces with underscores in function name
                func_def_match = re.search(r'def\s+([\w\s]+)\s*\(', func_str)
                if func_def_match:
                    original_func_name = func_def_match.group(1)
                    # Replace spaces with underscores in function name
                    new_func_name = original_func_name.replace(' ', '_')
                    # Replace the function name in the string
                    func_str = func_str.replace(f'def {original_func_name}(', f'def {new_func_name}(')
                
                # Execute function string to make it available in globals
                exec(func_str, globals())
                # Extract function name using regex (now without spaces)
                func_name = re.search(r'def\s+(\w+)\s*\(', func_str).group(1)
                self.functions_set.append(globals()[func_name])


    def run_all_functions(self, state, action):
        # run all functions in self.functions_set
        for func in self.functions_set:
            feedback, success, suggestion = func(state=state, action=action)
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


    # record the list of rules that are correctly predicted and the list of rules that are incorrectly predicted
    def functions_verification(self):
        record = {} # key: ruleID; value: list
        record['whole_set'] = []
        # ! verifing with buffer_correct_all.json, only find the rules that are failed
        facts_set = load_json_file(os.path.join(self.fact_dir, self.env_name, 'buffer_correct_all.json'))
        for action, transition_set in facts_set.items():
            for index, transition in enumerate(transition_set):
                # transition['state_0']
                # transition['action']
                # transition['action_result']
                record['whole_set'].append(action + '_' + str(index))
                if transition['action'] is None or transition['initial_state'] is None:
                    continue
                for func in self.functions_set:
                    func_name = func.__name__
                    try:
                        if self.with_graph:
                            feedback, success, suggestion = func(state=transition['initial_state'], action=transition['action'], scene_graph=transition['sg_info'])
                        else:
                            feedback, success, suggestion = func(state=transition['initial_state'], action=transition['action'])
                    except Exception as e:
                        print(f"\n[Error] Function: {func.__name__} | Transition: {transition['action']['name']} | Index: {index}")
                        print(f"Error Type: {type(e).__name__}")
                        print(f"Error Message: {e}")
                        print("Full Traceback:")
                        traceback.print_exc()

                        record[func_name] = record.get(func_name, []) + ['failed']
                        continue
                    if transition['action_result'] == True and success != transition['action_result']:
                        record[func_name] = record.get(func_name, []) + ['failed']
                    # means it did not work
                    else:
                        record[func_name] = record.get(func_name, []) + [str(00)]


        # ! verifing with buffer_wrong_all.json, find the rules that are failedv and can correct the wrong predictions
        facts_set = load_json_file(os.path.join(self.fact_dir, self.env_name, 'buffer_wrong_all.json'))
        for action, transition_set in facts_set.items():
            for index, transition in enumerate(transition_set):
                # transition['state_0']
                # transition['action']
                # transition['action_result']
                record['whole_set'].append(action + '_' + str(index))
                if transition['action'] is None or transition['initial_state'] is None:
                    continue
                for func in self.functions_set:
                    func_name = func.__name__
                    try:
                        if self.with_graph:
                            feedback, success, suggestion = func(state=transition['initial_state'], action=transition['action'], scene_graph=transition['sg_info'])
                        else:
                            feedback, success, suggestion = func(state=transition['initial_state'], action=transition['action'])
                    except Exception as e:
                        # Skip this function if execution fails, continue to next function
                        print(f"Error executing function {func_name} on transition {action}_{index}: {e}")
                        record[func_name] = record.get(func_name, []) + ['failed']
                        continue
                    
                    # the generated rules are accurate, the generated rules only check if the current transition is infeasible
                    # so when the output is true, it cannot be determined if it did not work or passed the rule
                    # only when the output is false can it be determined if it worked
                    if transition['action_result'] == False and success == transition['action_result']:
                        record[func_name] = record.get(func_name, []) + [action + '_' + str(index)]
                    # the generated rules are wrong, some transitions that were originally feasible became infeasible
                    elif transition['action_result'] == True and success != transition['action_result']:
                        record[func_name] = record.get(func_name, []) + ['failed']
                    # means it did not work
                    else:
                        record[func_name] = record.get(func_name, []) + [str(00)]

        verification_result_dir = os.path.join(self.rules_dir, self.env_name, 'verification_result.json')
        with open(verification_result_dir, 'w') as f:
            json.dump(record, f, cls=NumpyEncoder, indent=4)
        # return record


    def replace_rule_number(self, text: str, counter: int) -> str:
        # replace the "# Rule X:" part
        text = re.sub(r"# Rule \d+", f"# Rule {counter}", text)
        # replace the "def Rule_X_" part
        text = re.sub(r"def Rule_\d+_", f"def Rule_{counter}_", text)
        return text


    # will not select duplicate rules, if no rule can cover the uncovered facts, stop further filtering rules and output directly
    def select_rules(self):
        verification_result_dir = os.path.join(self.rules_dir, self.env_name, 'verification_result.json')
        data = load_json_file(verification_result_dir)
        whole_set = set(data['whole_set'])
        uncovered_elements = whole_set.copy()
        selected_rules = []
        # prepare the rule set, filter out all rules, and exclude rules that contain 'failed'
        all_rules = {
            key: set([item for item in value if item != '0'])
            for key, value in data.items() 
            if key != 'whole_set' and 'failed' not in value
        }        

        # use greedy algorithm to select rules
        while uncovered_elements:
            # find the rule that can cover the most uncovered elements
            best_rule = None
            best_covered = 0
            best_covered_set = set()
            
            for rule, items in all_rules.items():
                covered = items.intersection(uncovered_elements)
                if len(covered) > best_covered:
                    best_rule = rule
                    best_covered = len(covered)
                    best_covered_set = covered
            
            if not best_rule:
                break  # no rule can increase coverage, stop
            
            # update the selected rules and uncovered elements
            selected_rules.append(best_rule)
            uncovered_elements -= best_covered_set

        # sort all rules by the number of covered elements
        sorted_rules = sorted(all_rules.items(), key=lambda item: len(item[1]), reverse=True)

        rule_summary = {
            'selected_rules': selected_rules, 
                        'sorted_rules':[(rule, list(items)) for rule, items in sorted_rules]
                        }
        # return the result
        with open(os.path.join(self.rules_dir, self.env_name, 'selected_rules.json'), 'w') as f:
            json.dump(rule_summary, f, cls=NumpyEncoder, indent=4)

        counter = 100
        pruned_functions_set_string = []
        # ! these rules are effective, will be directly used for inference stage
        for rule_index in selected_rules:
            for rule in self.functions_set_string:
                if rule_index in rule:
                    rule = self.replace_rule_number(rule, counter)
                    pruned_functions_set_string.append(rule)
                    counter += 1
        with open(os.path.join(self.rules_dir, self.env_name, 'pruned_rules_code.json'), 'w') as f:
            json.dump(pruned_functions_set_string, f, cls=NumpyEncoder, indent=4)

        counter = 100
        sorted_rules_code = []
        # ! these rules may be effective, but because the current transition data is insufficient, the correcting transition numbers = 0
        for rule_index in sorted_rules:
            for rule in self.functions_set_string:
                if rule_index[0] in rule:
                    rule = self.replace_rule_number(rule, counter)
                    sorted_rules_code.append(rule)
                    counter += 1
        if counter > 200:
        # ! prevent the rules_code.json file from being too large
            with open(os.path.join(self.rules_dir, self.env_name, 'rules_code.json'), 'w') as f:
                json.dump(random.sample(sorted_rules_code, 20), f, cls=NumpyEncoder, indent=4)
        else:
            with open(os.path.join(self.rules_dir, self.env_name, 'rules_code.json'), 'w') as f:
                json.dump(sorted_rules_code, f, cls=NumpyEncoder, indent=4)

        # ! sorted_rules: all rules are sorted by the number of uncovered elements
        # ! pruned_functions_set_string: the selected rules are pruned from the original functions_set_string
        return selected_rules, sorted_rules, pruned_functions_set_string, sorted_rules_code


    # TODO add to buffer.worldmodel_get_prediction
    def run(self, state, action):
        for func in self.functions_set:
            if not func(state=state, action=action):  
                return False


    def rule_code_gen(self, action, rule, max_retries=5):
        # bool = expectedrulecode(state=state_0, action=action)

        if max_retries == 0:
            log_info("************Failed to get workflow. Consider updating your prompt.************\n\n")
            return {}
        try:
            # ! load_text(f"/home/sawyer/Workspace/[wall-e alfworld-final] reflexion/prompts/{prompt}.txt")
            if self.with_graph:
                prompt_file = os.path.join(self.prompt_dir, 'rule_code_gen_system_with_graph_' + self.env_name + '.txt')
            else:
                prompt_file = os.path.join(self.prompt_dir, 'rule_code_gen_system_' + self.env_name + '.txt')
            rule_code_gen_system = load_text(prompt_file)
            prompt_file = os.path.join(self.prompt_dir, 'rule_code_gen_query.txt')
            rule_code_gen_query = load_text(prompt_file).format(rule = rule)
            # rule_code_gen_system = load_prompt("rule_code_gen_system_CC_" + self.env_name) # .replace("<rules>", rules_string)
            # rule_code_gen_query = load_prompt("rule_code_gen_query").format(rule = rule)
            # world_model_query += "\nMake your prediction for 'rules check', 'success' and 'state 1'. You should only give the 'rules check', 'success' and 'state 1', with out any other information."
                
            messages = [
                SystemMessage(content=rule_code_gen_system),
                HumanMessage(content=rule_code_gen_query)
            ]

            llm_response = self.llm(messages)
            response_code = llm_response.content
            # write_task_to_csv( e_metadata)
            # # ensure the format
            # prediction_json = fix_and_parse_json(response_code)
            code_name = rule[:6].replace(' ', '_') + '_' + action
            code_str = response_code.replace("python\n", "", 1)
            code_str = code_str.replace("expected_rule_code", code_name)
            code_str = code_str.strip('```')
            code_str = f"# {rule} \n" + code_str
            return code_str
            # debug #######################
        except Exception as e:
            log_info(f"Error arises in WorldModel prediction part: {e} Trying again!\n\n")

            return self.rule_code_gen(
                action, 
                rule,
                max_retries=max_retries - 1
            )
    
    def rules_code_all(self):
        # ensure output directory exists
        rule_set = load_json_file(os.path.join(self.rules_dir, self.env_name, 'rules_natural_language.json'))
        for action, rules in rule_set.items():
            for rule in rules:
                rule_code = self.rule_code_gen(action, rule)
                print(f'{rule_code}')
                self.functions_set_string.append(rule_code)
        with open(os.path.join(self.rules_dir, self.env_name, 'rules_code.json'), 'w') as f:
            json.dump(self.functions_set_string, f, cls=NumpyEncoder, indent=4)
        self.load_functions()


if __name__ == "__main__":

    
    # Initialize the ruleverifier
    env_name = 'alfworld'
    io_dir = '/home/sawyer/Workspace/reflexion'
    ruleverifier = RuleVerifier(env_name = env_name, io_dir = io_dir)


    # [Stage 1] rules code generation
    #######################
    ruleverifier.rules_code_all()

    # [Stage 2] rules code verification
    #######################
    ruleverifier.functions_verification()

    # [Stage 3] rules selection
    # selected_rules, sorted_rules, pruned_functions_set_string = ruleverifier.select_rules()
    ruleverifier.select_rules()









