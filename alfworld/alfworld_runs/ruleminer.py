from utilsextra import *  # Import necessary functions and classes from utils module
import json
import datetime
import tiktoken  # Import tiktoken library

class RuleMiner:
    def __init__(self, io_dir, env_name, model_name="gpt-4o-mini", temperature = 0.3, choice_num = 1):
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
            )  # Initialize the LLM model. max_tokens=1024, TODO
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # Initialize the tokenizer
        
        self.rules = {}
        self.env_name = env_name
        self.io_dir = io_dir
        self.rules_dir = io_dir + '/symbolic_knowledge/'
        self.prompt_dir = io_dir + '/prompts'
        self.fact_dir = io_dir + '/traj_data'

    def _count_tokens(self, text):
        """Counts the number of tokens in a given text.
        
        Args:
            text (str): The text to count tokens for.
        
        Returns:
            int: The number of tokens.
        """
        if isinstance(text, dict):
            text = json.dumps(text)
        return len(self.tokenizer.encode(text))

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
        # find the index of the first '['
        start_index = s.find('[')
        # find the index of the last ']'
        end_index = s.rfind(']')
        
        # check if '[' and ']' are found, and '[' should be before ']'
        if start_index != -1 and end_index != -1 and start_index < end_index:
            # extract and return the substring
            return s[start_index:end_index + 1]
        else:
            # if no matching '[...]' is found, return an empty string or an appropriate value
            return ""

    def _extract_between_curly_brackets(self, s):
        # find the index of the first '['
        start_index = s.find('{')
        # find the index of the last ']'
        end_index = s.rfind('}')
        
        # check if '[' and ']' are found, and '[' should be before ']'
        if start_index != -1 and end_index != -1 and start_index < end_index:
            # extract and return the substring
            return s[start_index:end_index + 1]
        else:
            # if no matching '[...]' is found, return an empty string or an appropriate value
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


    def get_rules_update(self, act_name, tj_buffer, tj_negative, max_retries=5):
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

            total_elements = len(tj_buffer)
            batch_size = 100 # 20
            for i in range(0, total_elements, batch_size):
                # Slicing the list to get the current batch
                truncated_tj_batch = tj_buffer[i:i + batch_size]

                prompt_file = os.path.join(self.prompt_dir, 'rule_improve_system_' + self.env_name + '.txt')
                rule_miner_system = load_text(prompt_file)
                prompt_file = os.path.join(self.prompt_dir, 'rule_improve_query.txt')
                rule_miner_query = load_text(prompt_file).format(transitions=truncated_tj_batch, rules = self.rules.get(act_name, []))
                rule_miner_query += f"\n Mining the rules for '{act_name}'"
                messages = [SystemMessage(content=rule_miner_system), HumanMessage(content=rule_miner_query)]

                rules_candidate = []
                llm_response = self.llm.generate(messages = [messages])
                for generation in llm_response.generations[0]:
                    message_content = generation.message.content
                    message_content = self._extract_between_curly_brackets(message_content) 
                    parsed_data = fix_and_parse_json(message_content)
                    rules_temp0 = parsed_data['final_rules']
                    rules_candidate.extend(rules_temp0)
                self.rules[act_name] = rules_candidate
            return rules_candidate  # Parse the JSON rules and handle errors in formatting.
        except Exception as e:
            log_info(f"Error in Mining Rules: {e}. Retrying...")
            return self.get_rules_update(act_name, tj_buffer, tj_negative, max_retries=max_retries - 1)  # Recursive retry on exception.


    def get_rules_all(self):
        """Attempts to mine rules using the LLM, retrying on failure up to max_retries times.

        Args:
            max_retries (int): Maximum number of retry attempts.

        Returns:
            dict: Parsed rules if successful, or an empty dictionary on failure.
        """
        buffer_pos = load_json_file(os.path.join(self.fact_dir, self.env_name, 'buffer_correct_temp.json'))
        buffer_neg = load_json_file(os.path.join(self.fact_dir, self.env_name, 'buffer_wrong_temp.json'))
        for key, value_neg in buffer_neg.items():
            print(f"start mining transactions from {key}")
            value_pos = buffer_pos.get(key, [])
            merged_list = value_neg + value_pos
            self.get_rules_update(key, merged_list, value_neg)
        with open(os.path.join(self.rules_dir, self.env_name, 'rules_natural_language.json'), 'w') as f:
            json.dump(self.rules, f, indent=4)  # Save the rules to a file for debugging.
        # self.rules = {}

if __name__ == "__main__":

    model_name="gpt-4o-mini"
    temperature=0.3
    io_dir = '/home/sawyer/Workspace/reflexion'
    env_name = 'alfworld'
    miner = RuleMiner(io_dir = io_dir, env_name = env_name, model_name=model_name, temperature=temperature)  # Create a RuleMiner instance

    miner.get_rules_all()
    print()

