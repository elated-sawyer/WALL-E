from utilsextra import *
import tiktoken  # Import tiktoken library


class Planner:
    def __init__(
        self,
        # openai_key,
        rules_dir=None, 
        traj_memory_dir=None,
        model_name="gpt-4o-mini",
        temperature=0, # default 0
        choice_num=1, # default 1
    ):

        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            n = choice_num,
            response_format = { "type": "json_object" }
        )

        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # Initialize the tokenizer


        if rules_dir is None:
            self.rules = {}
        else:
            self.rules = load_json_file(rules_dir)

        if traj_memory_dir is None:
            self.traj_memory = {}
        else:
            self.traj_memory = load_json_file(traj_memory_dir)
    
    # handle the string or list case of check_result["feedback"] and check_result["suggestion"]
    def _format_feedback_or_suggestion(self, item):
        if isinstance(item, list):
            return "; ".join(item)
        elif isinstance(item, str):
            return item
        else:
            return ""

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

    def _count_tokens(self, text):
        """Counts the number of tokens in a given text.
        
        Args:
            text (str): The text to count tokens for.
        
        Returns:
            int: The number of tokens.
        """

        text = json.dumps(text)
        return len(self.tokenizer.encode(text))

    def get_workflow(self, inital_state, check_result, max_retries=5):

        if max_retries == 0:
            log_info("************Failed to get workflow. Consider updating your prompt.************\n\n")
            return {}

        try:
            rules_act = self.rules
            rules_string = dict_to_prompt(rules_act)
            structured_action_system = load_prompt("structured_action_system_w_rules_w_multisingle").replace("<rules>", rules_string)

            structured_action_query = load_prompt("structured_action_query").format(
                inital_state=inital_state
            )

            if len(check_result) == 0:
                structured_action_query += "\nGive you next step. Remember to follow the response format."
            else:

                feedback = self._format_feedback_or_suggestion(check_result.get("feedback", ""))
                suggestion = self._format_feedback_or_suggestion(check_result.get("suggestion", ""))
                structured_action_query += f"""The previous action failed. 
                The reason for the failure: {feedback}.
                A suggested recommendations: {suggestion}. 
                Re-generate your next action. Remember to follow the response format."""
                
            messages = [
                SystemMessage(content=structured_action_system),
                HumanMessage(content=structured_action_query)
            ]

            token_length = self._count_tokens(structured_action_system) + self._count_tokens(structured_action_query)
            print(f'total token length is {token_length}')           

            llm_response = self.llm(messages)

            workflow_dict = llm_response.content
            prediction_json = fix_and_parse_json(workflow_dict)

            return prediction_json["next action"]
        except Exception as e:
            log_info(f"Error arises in Decision Making part: {e} Trying again!\n\n")

            return self.get_workflow(
                inital_state, 
                check_result, 
                max_retries=max_retries - 1
            )
    

    def update_rules(self, rules_extra):
        self.rules = rules_extra



if __name__ == "__main__":
    model_name = 'gpt-4-turbo'
    # model_name= "gpt-3.5-turbo"

