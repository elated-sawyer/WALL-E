import re
from collections import defaultdict

def items_in_locations(text):
    # Step 1: Initialize variables
    target_info = defaultdict(list)
    
    # Step 2: Extract reachable locations from the first line
    first_line = text.split("\n")[0]
    reachable_locations = re.findall(r"\b(?:a\s)?(\w+\s\d+)", first_line)

    # Step 3: Process each line to extract information
    lines = text.split("\n")
    current_location = None
    
    # for line in lines[1:]:
    for i, line in enumerate(lines[1:]):
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
Nothing happens.
"""

text = "You are in the middle of a room. Looking quickly around you, you see a cabinet 16, a cabinet 15, a cabinet 14, a cabinet 13, a cabinet 12, a cabinet 11, a cabinet 10, a cabinet 9, a cabinet 8, a cabinet 7, a cabinet 6, a cabinet 5, a cabinet 4, a cabinet 3, a cabinet 2, a cabinet 1, a coffeemachine 1, a countertop 2, a countertop 1, a diningtable 1, a drawer 5, a drawer 4, a drawer 3, a drawer 2, a drawer 1, a fridge 1, a garbagecan 1, a microwave 1, a safe 1, a sinkbasin 1, a stoveburner 4, a stoveburner 3, a stoveburner 2, a stoveburner 1, and a toaster 1.\nYour task is to: cool some pan and put it in stoveburner.\n> think: To solve the task, I need to find and take a pan, then cool it with fridge, then put it in stoveburner.\nOK.\n> think: First I need to find a pan. An pan is more likely to appear in stoveburner (1-4), sinkbasin (1), diningtable (1), countertop (1-2), cabinet (1-16), drawer (1-5). I can check one by one, starting with stoveburner 1.\nOK.\n>go to stoveburner 1\nOn the stoveburner 1, you see nothing.\n>go to stoveburner 2\nOn the stoveburner 2, you see a pot 1.\n> go to stoveburner 3\nOn the stoveburner 3, you see a pan 1.\n> take pan 1 from stoveburner 3\n> think: Now I find a pan (1). Next, I need to take it.\nOK.\nYou pick up the pan 1 from the stoveburner 3.\n> think: Now I take a pan (1). Next, I need to go to a fridge (1) and cool it.\nOK.\n> go to fridge 1\nThe fridge 1 is closed.\n> cool pan 1 with fridge 1\nYou cool the pan 1 using the fridge 1.\n> think: Now I cool a pan (1). Next, I need to put it in/on stoveburner 1.\nOK.\n>go to stoveburner 1\nOn the stoveburner 1, you see nothing.\n> put pan 1 in/on stoveburner 1\nYou put the pan 1 in/on the stoveburner 1.\n"

# call the function and output the result
target_info = items_in_locations(text)
print(target_info)
