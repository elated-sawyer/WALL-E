import re

def convert_action(action_str):
    # define the conversion rules for actions
    if action_str.startswith('go to'):
        target = action_str.split('go to ')[1]
        return {
            "name": "go to",
            "args": {
                "target": target
            }
        }
    
    elif action_str.startswith('open'):
        target = action_str.split('open ')[1]
        return {
            "name": "open",
            "args": {
                "target": target
            }
        }

    elif action_str.startswith('close'):
        target = action_str.split('close ')[1]
        return {
            "name": "close",
            "args": {
                "target": target
            }
        }

    elif action_str.startswith('take'):
        match = re.match(r'take (.+) from (.+)', action_str)
        if match:
            obj, source = match.groups()
            return {
                "name": "take",
                "args": {
                    "obj": obj,
                    "source": source
                }
            }

    elif action_str.startswith('put'):
        match = re.match(r'put (.+) in/on (.+)', action_str)
        if match:
            obj, target = match.groups()
            return {
                "name": "put",
                "args": {
                    "obj": obj,
                    "target": target
                }
            }

    elif action_str.startswith('clean'):
        match = re.match(r'clean (.+) with (.+)', action_str)
        if match:
            obj, tool = match.groups()
            return {
                "name": "clean",
                "args": {
                    "obj": obj,
                    "tool": tool
                }
            }

    elif action_str.startswith('heat'):
        match = re.match(r'heat (.+) with (.+)', action_str)
        if match:
            obj, tool = match.groups()
            return {
                "name": "heat",
                "args": {
                    "obj": obj,
                    "tool": tool
                }
            }

    elif action_str.startswith('cool'):
        match = re.match(r'cool (.+) with (.+)', action_str)
        if match:
            obj, tool = match.groups()
            return {
                "name": "cool",
                "args": {
                    "obj": obj,
                    "tool": tool
                }
            }

    elif action_str.startswith('use'):
        obj = action_str.split('use ')[1]
        return {
            "name": "use",
            "args": {
                "obj": obj
            }
        }

    return None  # if no matching pattern is found



if __name__ == "__main__":
    # example test
    example_action = 'take cd 2 from dresser 1'
    example_action = "clean mug 4 with dishsponge 1 and soapbottle 1"
    converted_action = convert_action(example_action)
    print(converted_action)
