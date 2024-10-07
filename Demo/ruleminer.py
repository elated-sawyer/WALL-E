from utilsextra import * 
import json
import datetime
# import tiktoken
import argparse

class RuleMiner:
    def __init__(self, rules_dir=None, model_name="gpt-4o-mini", rule_save_dir = None, temperature = 0, choice_num = 1):
        """Initializes the RuleMiner instance with a specific model configuration.
        
        Args:
            model_name (str): The name of the model to use for rule mining.
            temperature (int): The randomness of the model's responses.
        """
        self.llm = ChatOpenAI(
            model_name=model_name, 
            temperature=temperature,
            response_format = { "type": "json_object" },
            n = choice_num
            ) 
        # self.tokenizer = tiktoken.get_encoding("cl100k_base")

        self.rule_save_dir = rule_save_dir
        
        if rules_dir is None:
            self.rules = {}
        else:
            self.rules = load_json_file(rules_dir)

    # def _count_tokens(self, text):
    #     """Counts the number of tokens in a given text.
        
    #     Args:
    #         text (str): The text to count tokens for.
        
    #     Returns:
    #         int: The number of tokens.
    #     """
    #     if isinstance(text, dict):
    #         text = json.dumps(text)
    #     return len(self.tokenizer.encode(text))

    def _truncate_tj_buffer(self, tj_buffer, max_tokens):
        """Truncates the tj_buffer to ensure its token count does not exceed the max_tokens limit.
        
        Args:
            tj_buffer (list): The buffer containing transition data.
            max_tokens (int): The maximum allowed tokens.
        
        Returns:
            list: The truncated buffer.
        """
        truncated_buffer = []
        current_tokens = 0
        
        for item in tj_buffer:
            item_tokens = self._count_tokens(item)
            if current_tokens + item_tokens > max_tokens:
                break
            truncated_buffer.append(item)
            current_tokens += item_tokens
        
        return truncated_buffer

    def _extract_between_brackets(self, s):
        start_index = s.find('[')
        end_index = s.rfind(']')
        
        if start_index != -1 and end_index != -1 and start_index < end_index:
            return s[start_index:end_index + 1]
        else:
            return ""

    def _extract_between_curly_brackets(self, s):
        start_index = s.find('{')
        end_index = s.rfind('}')
        if start_index != -1 and end_index != -1 and start_index < end_index:
            return s[start_index:end_index + 1]
        else:
            return ""

    def _write_to_json(self, file_path, new_data):
        """Append new data to the existing JSON file, handling potential I/O errors."""
        try:
            # Check if file exists and has content; if not, initialize with an empty list
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
            except (IOError, json.JSONDecodeError):
                data = []

            data.append(new_data)  # Append new data to the existing data

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            print(f"An error occurred while writing to the file: {e}")


    def get_rules_update_multistage(self, act_name, tj_buffer, tj_negative, task_id=99, max_retries=5):
        """Attempts to mine rules using the LLM, retrying on failure up to max_retries times.

        Args:
            max_retries (int): Maximum number of retry attempts.

        Returns:
            dict: Parsed rules if successful, or an empty dictionary on failure.
        """
        if max_retries == 0:
            log_info("Failed to get rules after maximum retries. Consider updating your prompt.")
            return {}
        try:
            file_path = self.rule_save_dir

            total_elements = len(tj_buffer)
            batch_size = 100 # 20
            for i in range(0, total_elements, batch_size):
                # Slicing the list to get the current batch
                truncated_tj_batch = tj_buffer[i:i + batch_size]


                # stage 1: rule addition
                ##################
                # transition_checker_system = load_prompt("rule_miner_system")  # Load the system's part of the prompt.
                # transition_checker_query = load_prompt("rule_miner_query").format(transitions=truncated_tj_batch)  # Load and format the query prompt.
                transition_checker_system = load_prompt("rule_addition_system")  # Load the system's part of the prompt.
                transition_checker_query = load_prompt("rule_addition_query").format(
                    transitions=truncated_tj_batch, 
                    rules = self.rules.get(act_name, [])
                    )  # Load and format the query prompt.
                messages = [SystemMessage(content=transition_checker_system), HumanMessage(content=transition_checker_query)]

                rules_temp0 = []
                llm_response = self.llm.generate(messages = [messages])
                for generation in llm_response.generations[0]:
                    message_content = generation.message.content
                    message_content = self._extract_between_curly_brackets(message_content) 
                    parsed_data = fix_and_parse_json(message_content)
                    rules_temp0.extend(parsed_data['new_rules'])
                rules_candidate = rules_temp0


                # stage 2: rule improvement
                ##################
                transition_checker_system = load_prompt("rule_improvement_system")  # Load the system's part of the prompt.
                transition_checker_query = load_prompt("rule_improvement_query").format(
                    transitions = truncated_tj_batch, 
                    rules = rules_candidate+self.rules.get(act_name, [])
                    )  # Load and format the query prompt.
                messages = [SystemMessage(content=transition_checker_system), HumanMessage(content=transition_checker_query)]

                rules_temp1 = []
                llm_response = self.llm.generate(messages = [messages])
                for generation in llm_response.generations[0]:
                    message_content = generation.message.content
                    message_content = self._extract_between_curly_brackets(message_content) 
                    parsed_data = fix_and_parse_json(message_content)
                    rules_temp1.extend(parsed_data['final_rules'])
                rules_candidate = rules_temp1
                print(f'rules_eva:{rules_candidate}')

                # # stage 3: final critic
                # ##################
                # transition_checker_system = load_prompt("rule_3_generalcritic_system")  # Load the system's part of the prompt.
                # transition_checker_query = load_prompt("rule_3_generalcritic_query").format(
                #     rules = rules_final
                #     )  # Load and format the query prompt.
                # messages = [SystemMessage(content=transition_checker_system), HumanMessage(content=transition_checker_query)]

                # llm_response = self.llm.generate(messages = [messages])
                # for generation in llm_response.generations[0]:
                #     message_content = generation.message.content
                #     message_content = self._extract_between_curly_brackets(message_content) 
                #     rules_temp2 = fix_and_parse_json(message_content)
                #     rules_final = rules_temp2['ordered_rules']
                # print(f'rules_final:{rules_final}')

                # # stage 3: final critic
                # ##################
                # transition_checker_system = load_prompt("rule_1_YY_system")  # Load the system's part of the prompt.
                # transition_checker_query = load_prompt("rule_1_YY_query").format(
                #     rules = rules_candidate,
                #     transitions = tj_negative
                #     )  # Load and format the query prompt.
                # messages = [SystemMessage(content=transition_checker_system), HumanMessage(content=transition_checker_query)]

                # llm_response = self.llm.generate(messages = [messages])
                # for generation in llm_response.generations[0]:
                #     message_content = generation.message.content
                #     message_content = self._extract_between_curly_brackets(message_content) 
                #     rules_temp2 = fix_and_parse_json(message_content)
                #     rules_golden = rules_temp2['selected_rules']
                # print(f'rules_golden:{rules_golden}')

                # # stage 4: final critic
                # ##################
                # transition_checker_system = load_prompt("rule_4_deleteduplication_system")  # Load the system's part of the prompt.
                # transition_checker_query = load_prompt("rule_4_deleteduplication_query").format(
                #     rules = rules_candidate
                #     )  # Load and format the query prompt.
                # messages = [SystemMessage(content=transition_checker_system), HumanMessage(content=transition_checker_query)]

                # llm_response = self.llm.generate(messages = [messages])
                # for generation in llm_response.generations[0]:
                #     message_content = generation.message.content
                #     message_content = self._extract_between_curly_brackets(message_content) 
                #     rules_temp3 = fix_and_parse_json(message_content)
                #     rules_candidate = rules_temp3['final_rules']

                # print(f'rules_candidate:{rules_candidate}')

                # rules_all = {'golden rules':rules_golden, 'rules_candidate':rules_candidate}

                self.rules[act_name] = rules_candidate

                # with open(f'/home/**/Workspace/**/agent/buffer_rules/rules_debug_oneshot_taskID{task_id}_actname{act_name}_batch{i}.json', 'w') as f:
                #     json.dump(parsed_data, f, indent=4)  # Save the rules to a file for debugging.
                # with open(f'/home/**/Workspace/**/agent/buffer_rules/rules_debug_oneshot_finalrules_taskID{task_id}_actname{act_name}.json', 'w') as f:
                #     json.dump(rules_final, f, indent=4)  # Save the rules to a file for debugging.
            return rules_candidate  # Parse the JSON rules and handle errors in formatting.
        except Exception as e:
            log_info(f"Error in Mining Rules: {e}. Retrying...")
            return self.get_rules_update_multistage(act_name, tj_buffer, tj_negative, task_id, max_retries=max_retries - 1)  # Recursive retry on exception.


    def get_rules_temp(self, buffer_traj, task_id=99):
        """Attempts to mine rules using the LLM, retrying on failure up to max_retries times.

        Args:
            max_retries (int): Maximum number of retry attempts.

        Returns:
            dict: Parsed rules if successful, or an empty dictionary on failure.
        """
        for key, value in buffer_traj.items():
            print(f"start mining transactions from {key}")
            self.get_rules_update_multistage(key, value, value, task_id)

        # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.rule_save_dir
        # with open(f'/home/**/Workspace/reflexion/alfworld_runs/buffer_rules/rules_debug_taskID{task_id}_time{timestamp}.json', 'w') as f:
        #     json.dump(self.rules, f, indent=4)  # Save the rules to a file for debugging.
        with open(file_path, 'w') as f:
            json.dump(self.rules, f, indent=4)  # Save the rules to a file for debugging.
        # self.rules = {}


def get_args():
    parser = argparse.ArgumentParser(description="Run Rule Miner script.")
    parser.add_argument("--model_name", type=str, default="gpt-4-turbo", help="Name of the model to use.")
    parser.add_argument("--temperature", type=float, default=0.3, help="Temperature for model generation.")
    parser.add_argument("--buffer", type=str, required=True, help="Path to the buffer JSON file.")
    parser.add_argument("--rule_save_dir", type=str, required=True, help="File to save rules.")
    
    return parser.parse_args()



if __name__ == "__main__":
    # Parse command line arguments
    args = get_args()

    # Create a RuleMiner instance with parsed arguments
    miner = RuleMiner(model_name=args.model_name, temperature=args.temperature, rule_save_dir=args.rule_save_dir)

    # Load the positive and negative buffers
    buffer = load_json_file(args.buffer)

    # Mine rules
    mined_rules = miner.get_rules_temp(buffer)
    
    # Print the mined rules
    print(mined_rules)





# # Debug

# if __name__ == "__main__":
#     # Example usage:
#     model_name="gpt-4o"
#     # model_name="gpt-4"
#     temperature=0.5
#     # rules_dir = None
#     rule_save_dir = 'Demo/rule_save_dir/rules_debug.json'
#     miner = RuleMiner(model_name=model_name, temperature=temperature, rule_save_dir = rule_save_dir)  # Create a RuleMiner instance
    
#     # buffer = load_json_file('/home/**/Workspace/**/agent/buffer_fact copy 0703/buffer_correct.json')
#     buffer = load_json_file('Demo/buffer_fact/traj_demo.json')

#     mined_rules = miner.get_rules_temp(buffer)  # Mine rules
#     print(mined_rules)  # Print the mined rules
