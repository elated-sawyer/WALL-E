import re
from collections import defaultdict

def extract_item_in_hand(text):
    # initialize item_in_hand
    item_in_hand = {"item_name": None, "status": None}
    
    # process the string line by line
    lines = text.split("\n")
    
    for i, line in enumerate(lines):
        # process 'take' operation
        line = line.strip()
        if line.startswith("> take"):
            if i+1 < len(lines) and "Nothing happens" not in lines[i+1]:
                match = re.search(r"take (\w+\s\d+) from", line)
                if match:
                    item_in_hand["item_name"] = match.group(1)
                    item_in_hand["status"] = "normal"
        
        # process 'put' operation
        elif line.startswith("> put"):
            if i+1 < len(lines) and "Nothing happens" not in lines[i+1]:
                item_in_hand["item_name"] = None
                item_in_hand["status"] = None
        
        # process 'cool', 'heat', 'clean' operation
        elif any(line.startswith(f"> {action}") for action in ["cool", "heat", "clean"]):
            if i+1 < len(lines) and "Nothing happens" not in lines[i+1] and item_in_hand["item_name"] is not None:
                if line.startswith("> cool"):
                    item_in_hand["status"] = "cooled"
                elif line.startswith("> heat"):
                    item_in_hand["status"] = "heated"
                elif line.startswith("> clean"):
                    item_in_hand["status"] = "cleaned"

    return item_in_hand


def process_env_history(history_str):
    task_start_idx = history_str.find("Here is the task:")
    input_str = history_str[task_start_idx:]
    newline_index = input_str.find('\n')
    state_text = input_str[newline_index + 1:]
    return state_text

def items_in_locations(text):
    # Step 1: Initialize variables
    target_info = defaultdict(list)
    
    # Step 2: Extract reachable locations from the first line
    first_line = text.split("\n")[0]
    lines = text.split("\n")
    if first_line == '':
        first_line = text.split("\n")[1]
        lines = text.split("\n")[1:]

    reachable_locations = re.findall(r"\b(?:a\s)?(\w+\s\d+)", first_line)

    # Step 3: Process each line to extract information
    
    current_location = None
    
    # for line in lines[1:]:
    for i, line in enumerate(lines[1:]):
        line = line.strip()
        # Check if the line contains "you see"
        if "you see" in line:
            # Find which location this line is referring to
            for location in reachable_locations:
                if location in line:
                    current_location = location
                    break
            
            # Extract items seen at the current location
            items = re.findall(r"\b(?:a\s)?(\w+\s\d+)", line.split("you see")[1])
            if current_location:
                target_info[current_location].extend(items)
        
        # Handle "take" actions
        if line.startswith("> take"):
            match = re.search(r"take (\w+\s\d+) from (\w+\s\d+)", line)
            if match:
                item = match.group(1)
                location = match.group(2)
                if item in target_info[location]:
                    if "Nothing happens" not in lines[i + 2]:
                        target_info[location].remove(item)
        
        # Handle "put" actions
        if line.startswith("> put"):
            match = re.search(r"put (\w+\s\d+) in/on (\w+\s\d+)", line)
            if match:
                item = match.group(1)
                location = match.group(2)
                if "Nothing happens" not in lines[i + 2]:
                    target_info[location].append(item)

    return dict(target_info)


def extract_current_position(text):
    # initialize current_position
    current_position = {"location_name": None, "status": None}
    
    # process the string line by line
    lines = text.split("\n")
    
    for i, line in enumerate(lines):
        line = line.strip()
        # process 'go to' operation
        if line.startswith("> go to"):
            if i+1 < len(lines) and "Nothing happens" not in lines[i+1]:
                match = re.search(r"go to (\w+\s\d+)", line)
                if match:
                    current_position["location_name"] = match.group(1)
                    if "closed" in lines[i+1]:
                        current_position["status"] = "closed"
                    else:
                        current_position["status"] = "null"

        # process 'open' operation
        elif line.startswith("> open"):
            if i+1 < len(lines) and "Nothing happens" not in lines[i+1]:
                match = re.search(r"open (\w+\s\d+)", line)
                if match and match.group(1) in lines[i+1]:
                    current_position["location_name"] = match.group(1)
                    current_position["status"] = "open"

    return current_position


def reachable_locations(text):
    
    first_line = text.split("\n")[0]
    if first_line == '':
        first_line = text.split("\n")[1]
    reachable_locations = re.findall(r"\b(?:a\s)?(\w+\s\d+)", first_line)

    return reachable_locations



def extract_target_item(text):
    # Define the item list
    item_list = ["alarmclock","butterknife","box","fork","statue","book","dishsponge","handtowel","plunger","laptop",
                 "tennisracket","baseballbat","remotecontrol","bowl","cd","mug","pencil","wateringcan","glassbottle",
                 "peppershaker","saltshaker","soapbar","soapbottle","vase","watch","cloth","egg","knife","pot",
                 "pan","plate","spatula","bread","lettuce","potato","tomato","apple","cup","keychain","pillow",
                 "toiletpaper","winebottle","tissuebox","spraybottle","cellphone","candle","creditcard","newspaper","ladle"]

    # Split the input text into lines
    lines = text.splitlines()

    # Initialize target_item to None
    target_item = None

    # Iterate over each line in the text
    for line in lines:
        line = line.strip()
        # Check if the line starts with "Your task is to: "
        if line.startswith("Your task is to: "):
            # Extract the task string after "Your task is to: "
            task_string = line[len("Your task is to: "):]

            # Split the task string into words
            words = task_string.split()

            # Check if any word in the task string matches an item in item_list
            for word in words:
                if word in item_list:
                    target_item = word
                    break

            # If no match is found, raise an error with the current line
            if target_item is None:
                raise ValueError(f"No matching item found in line: {line}")

        # If target_item is found, break out of the loop
        if target_item:
            break

    return target_item


def state_info_transformation(text):
    state_info = defaultdict(list)
    state_info['target_item'] = extract_target_item(text)
    state_info['reachable_locations'] = reachable_locations(text)
    state_info['items_in_locations'] = items_in_locations(text)
    state_info['item_in_hand'] = extract_item_in_hand(text)
    state_info['current_position'] = extract_current_position(text)
    return state_info



if __name__ == "__main__":


    # example string
    text = """You are in the middle of a room. Looking quickly around you, you see a cabinet 10, a cabinet 9, a cabinet 8, a cabinet 7, a cabinet 6, a cabinet 5, a cabinet 4, a cabinet 3, a cabinet 2, a cabinet 1, a coffeemachine 1, a countertop 3, a countertop 2, a countertop 1, a diningtable 1, a drawer 6, a drawer 5, a drawer 4, a drawer 3, a drawer 2, a drawer 1, a fridge 1, a garbagecan 1, a microwave 1, a sinkbasin 1, a stoveburner 4, a stoveburner 3, a stoveburner 2, a stoveburner 1, and a toaster 1.
    Your task is to: heat some egg and put it in diningtable.
    > open fridge 1
    You open the fridge 1. The fridge 1 is open. In it, you see a lettuce 2, a mug 2, and a potato 3.
    > go to countertop 1
    On the countertop 1, you see a bread 1, a fork 1, and a saltshaker 1.
    > go to countertop 2
    On the countertop 2, you see nothing.
    > go to countertop 3
    On the countertop 3, you see a bowl 1, a butterknife 1, a egg 2, a kettle 2, a plate 1, a sink 1, and a spatula 2.
    > take egg 2 from countertop 3
    You pick up the egg 2 from the countertop 3.
    > go to microwave 1
    The microwave 1 is closed.
    > heat egg 2 with microwave 1
    You heat the egg 2 using the microwave 1.
    > go to diningtable 1
    On the diningtable 1, you see a apple 2, a bread 3, a egg 1, a kettle 1, a knife 1, a mug 1, a papertowelroll 1, a peppershaker 2, a potato 1, a soapbottle 1, and a spatula 1.
    > put egg 2 in/on diningtable 1
    You put the egg 2 in/on the diningtable 1.
    """
    text = """You are in the middle of a room. Looking quickly around you, you see a cabinet 10, a cabinet 9, a cabinet 8, a cabinet 7, a cabinet 6, a cabinet 5, a cabinet 4, a cabinet 3, a cabinet 2, a cabinet 1, a coffeemachine 1, a countertop 3, a countertop 2, a countertop 1, a diningtable 1, a drawer 6, a drawer 5, a drawer 4, a drawer 3, a drawer 2, a drawer 1, a fridge 1, a garbagecan 1, a microwave 1, a sinkbasin 1, a stoveburner 4, a stoveburner 3, a stoveburner 2, a stoveburner 1, and a toaster 1.
    Your task is to: heat some egg and put it in diningtable.
    > open fridge 1
    You open the fridge 1. The fridge 1 is open. In it, you see a lettuce 2, a mug 2, and a potato 3.
    > go to countertop 1
    On the countertop 1, you see a bread 1, a fork 1, and a saltshaker 1.
    > go to countertop 2
    On the countertop 2, you see nothing.
    > go to countertop 3
    On the countertop 3, you see a bowl 1, a butterknife 1, a egg 2, a kettle 2, a plate 1, a sink 1, and a spatula 2.
    > take egg 2 from countertop 3
    You pick up the egg 2 from the countertop 3.
    > go to microwave 1
    The microwave 1 is closed.
    > heat egg 2 with microwave 1
    You heat the egg 2 using the microwave 1.
    """
    text = """You are in the middle of a room. Looking quickly around you, you see a cabinet 10, a cabinet 9, a cabinet 8, a cabinet 7, a cabinet 6, a cabinet 5, a cabinet 4, a cabinet 3, a cabinet 2, a cabinet 1, a coffeemachine 1, a countertop 3, a countertop 2, a countertop 1, a diningtable 1, a drawer 6, a drawer 5, a drawer 4, a drawer 3, a drawer 2, a drawer 1, a fridge 1, a garbagecan 1, a microwave 1, a sinkbasin 1, a stoveburner 4, a stoveburner 3, a stoveburner 2, a stoveburner 1, and a toaster 1.
    Your task is to: heat some egg and put it in diningtable.
    > open fridge 1
    You open the fridge 1. The fridge 1 is open. In it, you see a lettuce 2, a mug 2, and a potato 3.
    > go to countertop 1
    On the countertop 1, you see a bread 1, a fork 1, and a saltshaker 1.
    > go to countertop 2
    On the countertop 2, you see nothing.
    > go to countertop 3
    On the countertop 3, you see a bowl 1, a butterknife 1, a egg 2, a kettle 2, a plate 1, a sink 1, and a spatula 2.
    > take egg 2 from countertop 3
    You pick up the egg 2 from the countertop 3.
    """

    text = """
    You are in the middle of a room. Looking quickly around you, you see a cabinet 6, a cabinet 5, a cabinet 4, a cabinet 3, a cabinet 2, a cabinet 1, a coffeemachine 1, a countertop 3, a countertop 2, a countertop 1, a drawer 3, a drawer 2, a drawer 1, a fridge 1, a garbagecan 1, a microwave 1, a shelf 3, a shelf 2, a shelf 1, a sinkbasin 1, a stoveburner 4, a stoveburner 3, a stoveburner 2, a stoveburner 1, and a toaster 1.
    Your task is to: heat some mug and put it in cabinet.
    > think: To solve the task, I need to find a mug, then heat it with the microwave, and finally put it in/in/on a cabinet.
    OK.
    > think: First, I need to find a mug. A mug is more likely to appear in/in/on the fridge (1), countertop (1-3), drawer (1-3), cabinet (1-6), or in/on the dining table. I can check one by one, starting with the fridge (1).
    OK.
    > open fridge 1
    Nothing happens.
    > go to countertop 1
    On the countertop 1, you see a creditcard 1, and a potato 2.
    > go to countertop 2
    On the countertop 2, you see a butterknife 1, a knife 1, a peppershaker 2, a spoon 1, a tomato 1, a vase 3, and a vase 2.
    > go to countertop 3
    On the countertop 3, you see a butterknife 3, a butterknife 2, a cellphone 2, a creditcard 2, a dishsponge 3, a glassbottle 3, a houseplant 1, a knife 3, a knife 2, a pan 2, a saltshaker 2, a soapbottle 3, a spoon 3, a statue 1, and a tomato 2.
    > go to drawer 1
    The drawer 1 is closed.
    > open drawer 1
    You open the drawer 1. The drawer 1 is open. In it, you see a cellphone 1, a spatula 1, and a spoon 2.
    > go to drawer 2
    The drawer 2 is closed.
    > open drawer 2
    You open the drawer 2. The drawer 2 is open. In it, you see a fork 2, and a fork 1.
    > go to drawer 3
    The drawer 3 is closed.
    > open drawer 3
    You open the drawer 3. The drawer 3 is open. In it, you see a spatula 2.
    > think: I haven't found a mug yet. I should check the cabinets next, starting with cabinet 1.
    OK.
    > go to cabinet 1
    On the cabinet 1, you see a vase 1.
    > go to cabinet 2
    The cabinet 2 is closed.
    > open cabinet 2
    You open the cabinet 2. The cabinet 2 is open. In it, you see a dishsponge 1, and a glassbottle 1.
    > go to cabinet 3
    On the cabinet 3, you see nothing.
    > go to cabinet 4
    On the cabinet 4, you see a mug 1, and a soapbottle 1.
    > think: Now I find a mug (1). Next, I need to take it.
    OK.
    > take mug 1 from cabinet 4
    You pick up the mug 1 from the cabinet 4.
    > think: Now I have the mug (1). Next, I need to go to the microwave (1) and heat it.
    OK.
    > go to microwave 1
    The microwave 1 is closed.
    > open microwave 1
    You open the microwave 1. The microwave 1 is open. In it, you see a cup 1, and a egg 1.
    > think: I need to remove the items in/in/on the microwave before I can heat the mug. I will take the cup and the egg out first.
    OK.
    > take cup 1 from microwave 1
    Nothing happens.
    > take egg 1 from microwave 1
    Nothing happens.
    > It seems that I cannot take the items out of the microwave. I will need to put the mug in/in/on the microwave without removing the other items first.
    Nothing happens.
    > It seems that I cannot interact with the items in/in/on the microwave directly. I will need to find a way to heat the mug without removing the other items first.
    Nothing happens.
    > It seems that I cannot interact with the items in/in/on the microwave directly, and I cannot remove them either. I need to find another way to heat the mug.
    Nothing happens.
    > It seems that I cannot heat the mug in/in/on the microwave because there are already items inside that I cannot remove. I will need to find an alternative way to heat the mug or check if there are other heating options available.
    Nothing happens.
    > think: Since I cannot use the microwave to heat the mug due to the items inside, I should check if there are any other heating options available in/in/on the room. The stove burners might be a viable option. I can check the stove burners next.
    OK.
    > go to stoveburner 1
    On the stoveburner 1, you see a pot 1.
    > go to stoveburner 2
    On the stoveburner 2, you see a pan 1.
    > go to stoveburner 3
    On the stoveburner 3, you see a pot 1.
    > go to stoveburner 4
    On the stoveburner 4, you see a pan 1.
    > think: I have checked all the stove burners, but I haven't found a way to heat the mug. I need to find another method to heat it or check if there are any other items in/in/on the room that can help me. I should check the countertop again for any heating items or alternatives.
    OK.
    > go to countertop 1
    On the countertop 1, you see a creditcard 1, and a potato 2.
    > go to countertop 2
    On the countertop 2, you see a butterknife 1, a knife 1, a peppershaker 2, a spoon 1, a tomato 1, a vase 3, and a vase 2.
    > go to countertop 3
    On the countertop 3, you see a butterknife 3, a butterknife 2, a cellphone 2, a creditcard 2, a dishsponge 3, a glassbottle 3, a houseplant 1, a knife 3, a knife 2, a pan 2, a saltshaker 2, a soapbottle 3, a spoon 3, a statue 1, and a tomato 2.
    > think: I have checked all the countertops and found no heating items. Since I cannot heat the mug in/in/on the microwave or in/on the stove burners, I need to consider other options. I should check the remaining cabinets for any heating items or alternatives. I will check cabinet 5 next.
    OK.
    > go to cabinet 5
    The cabinet 5 is closed.
    > open cabinet 5
    You open the cabinet 5. The cabinet 5 is open. In it, you see a peppershaker 1.
    > go to cabinet 6
    The cabinet 6 is closed.
    """



    # call the function and output the result
    state_info = state_info_transformation(text)
    print(state_info)