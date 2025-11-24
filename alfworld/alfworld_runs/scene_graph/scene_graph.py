import copy
import os
import re
import json
from collections import defaultdict

class SceneGraph:
    def __init__(self, initialization_info=None):
        """
        Initialize the SceneGraph object.
        Optionally, initialize the scene based on provided initialization information.
        """
        self.graph = {
            "locations": {},
            "items": {},
            "edges": {}
        }
        self.initial_state = {
            "locations": {},
            "items": {}
        }
        self.current_location = None  # Track the agent's current location

        # If initialization_info is provided, set up the initial scene
        if initialization_info:
            reachable_locations = re.findall(r"\b(?:a\s)?(\w+\s\d+)", initialization_info)
            for location in reachable_locations:
                self.graph["locations"][location] = ['Unexplored'] # 'Unexplored'
    
    def update_graph(self, interaction_info):
        """
        Update the scene graph based on interaction information.
        Also record the initial state of items and locations when they are first discovered (you see).
        """
        lines = interaction_info.split("\n")

        for i, line in enumerate(lines):
            line = line.strip()

            # Handle "go to"
            if line.startswith("> go to"):
                match = re.search(r"go to (\w+\s\d+)", line)
                if match:
                    new_location = match.group(1)
                    
                    # If this is the first move, just set current_location
                    if self.current_location is None:
                        self.current_location = new_location
                    else:
                        # If both current and new locations exist in the graph, create edges
                        if self.current_location in self.graph["locations"] and new_location in self.graph["locations"]:
                            if self.current_location not in self.graph["edges"]:
                                self.graph["edges"][self.current_location] = []
                            if new_location not in self.graph["edges"]:
                                self.graph["edges"][new_location] = []
                            # Add bidirectional edges if not already present
                            if new_location not in self.graph["edges"][self.current_location]:
                                self.graph["edges"][self.current_location].append(new_location)
                            if self.current_location not in self.graph["edges"][new_location]:
                                self.graph["edges"][new_location].append(self.current_location)
                        
                        # Update current location
                        self.current_location = new_location
                continue

            # Handle "you see"
            if "you see" in line:
                # Determine which location we're currently observing
                observed_location = None
                if self.current_location and self.current_location in self.graph["locations"]:
                    observed_location = self.current_location
                else:
                    # If current_location is not set, try to infer from the line
                    for location in self.graph["locations"]:
                        if location in line:
                            observed_location = location
                            break

                if observed_location:
                    if "Unexplored" in self.graph["locations"][observed_location]:
                        self.graph["locations"][observed_location].remove("Unexplored")
                    items = re.findall(r"\b(?:a\s)?(\w+\s\d+)", line.split("you see")[1])
                    for item in items:
                        # If item not in the graph, add it
                        if item not in self.graph["items"]:
                            self.graph["items"][item] = observed_location
                            self.graph["locations"][observed_location].append(item)

                    if not self.graph["locations"][observed_location]:
                        self.graph["locations"][observed_location] = ["No items"]
                    

                    # If this observed_location is not in initial_state yet, add it with the currently observed items
                    if observed_location not in self.initial_state["locations"]:
                        self.initial_state["locations"][observed_location] = []
                        for item in items:

                            ###########################################
                            if item not in self.initial_state["items"]:
                                self.initial_state["items"][item] = observed_location
                                self.initial_state["locations"][observed_location].append(item)

            # Handle "take"
            if line.startswith("> take"):
                match = re.search(r"take (\w+\s\d+) from (\w+\s\d+)", line)
                if match:
                    item = match.group(1)
                    location = match.group(2)
                    if item in self.graph["items"] and location in self.graph["locations"]:
                        if item in self.graph["locations"][location]:
                            self.graph["locations"][location].remove(item)
                            self.graph["items"][item] = "in hand"
                            if not self.graph["locations"][location]:
                                self.graph["locations"][location] = ["No items"]

        return self.graph


    def save_to_json(self, file_path):
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        with open(file_path, "w") as file:
            json.dump({
                "graph": self.graph,
                "initial_state": self.initial_state
            }, file, indent=4)

    def load_from_json(self, file_path):
        """
        Load the scene graph from a JSON file.
        If the file does not exist, do nothing and return.
        """
        if not os.path.exists(file_path):
            print(f"File '{file_path}' does not exist. No changes made to the SceneGraph.")
            return
        
        with open(file_path, "r") as file:
            data = json.load(file)

            self.graph['items'] = copy.deepcopy(data["initial_state"]['items'])
            self.initial_state = copy.deepcopy(data["initial_state"])

            for location, items_in_init in self.initial_state.get("locations", {}).items():
                if location in self.graph["locations"]:
                    self.graph["locations"][location] = items_in_init

        print(f"Scene graph and initial state loaded from '{file_path}'")


    def retrieve_graph(self):
        return self.graph

    def retrieve_initial_state(self):
        return self.initial_state

    def display_graph(self):
        print("Current Scene Graph:")
        print("Locations and their items:")
        for location, items in self.graph["locations"].items():
            print(f"  {location}: {', '.join(items) if items else 'Null'}")
        print("\nItems and their locations:")
        for item, location in self.graph["items"].items():
            print(f"  {item}: {location}")
        print("\nEdges (relationships between locations):")
        for location, connected_locations in self.graph["edges"].items():
            print(f"  {location}: {', '.join(connected_locations)}")

    def display_initial_state(self):
        print("Initial State:")
        print("Locations and their initial items:")
        for location, items in self.initial_state["locations"].items():
            print(f"  {location}: {', '.join(items) if items else 'Null'}")
        print("\nItems and their initial locations:")
        for item, location in self.initial_state["items"].items():
            print(f"  {item}: {location}")
            
    def to_string(self):
        """
        Return the entire scene graph (including initial state) as a JSON-formatted string.
        """

        data = {
            "locations": self.graph["locations"],
            "items": self.graph["items"]
        }
        return json.dumps(data, indent=4)

    def __str__(self):
        """
        When str(SceneGraph_object) is called, return the JSON string representation.
        """
        return self.to_string()



    def search_finding_item(self, query: dict):

        finding_item = query["finding_item"]
        input_locations = query["locations"]

        for loc in self.graph["locations"]:
            for item in self.graph["locations"][loc]:
                name_and_number = item.rsplit(" ", 1)
                if len(name_and_number) == 2:
                    name, number = name_and_number
                    if name == finding_item:
                        return [loc]

        unexplored_locations = [
            loc for loc, items in self.graph["locations"].items()
            if "Unexplored" in items
        ]

        difference = set(input_locations) - set(unexplored_locations)
        if difference:
            return unexplored_locations
        else:
            return input_locations





# Example usage:
if __name__ == "__main__":
    initial_info = (
        "You are in the middle of a room. Looking quickly around you, you see a fridge 1, "
        "a cabinet 1, a countertop 1, a toaster 1, a coffeemachine 1, a countertop 2, "
        "a cabinet 2, a stoveburner 1, a stoveburner 2, a cabinet 3, a cabinet 4, "
        "a microwave 1, a countertop 3, a sink 1, a sink 2, a shelf 1, a shelf 2, "
        "a drawer 1, a drawer 2, a drawer 3, a shelf 3, a stoveburner 3, a stoveburner 4, "
        "and a garbagecan 1."
    )

    sg = SceneGraph(initialization_info = initial_info)
    sg.display_graph()
    sg.load_from_json("/home/sawyer/Workspace/reflexion/alfworld_runs/scene_graph/scene_graph_with_initial_state.json")
    sg.display_graph()
    sg.load_from_json("/home/sawyer/Workspace/reflexion/alfworld_runs/ttt.json")
    sg.display_graph()

    sg.initialize_scene(initial_info)

    # Interactions


    # Interactions
    interaction_info = (
        """
        > go to countertop 1
        On the countertop 1, you see a bread 1, a plate 1, a glassbottle 1, a cellphone 1, a tomato 1, and a butterknife 1.
        > go to countertop 2
        On the countertop 2, you see a cellphone 2, a mug 1, and a spoon 1.
        > take mug 1 from countertop 2
        You pick up the mug 1 from the countertop 2.
        > think: Now I have found a mug (1). Next, I need to go to the fridge (1) and cool it.
        OK.
        > go to fridge 1
        Nothing happens.
        > think: The fridge is closed. I need to open it first to cool the mug.
        OK.
        > open fridge 1
        You open the fridge 1. The fridge 1 is open. In it, you see a bread 2, and a egg 1.
        > cool mug 1 with fridge 1
        Nothing happens.
        > think: It seems that the fridge is not suitable for cooling the mug. I need to find another way to cool the mug or check if there are any other items that can help with my task. However, since the task specifically requires cooling the mug, I will assume I need to find a way to cool it before proceeding.
        OK.
        > think: Since I cannot cool the mug in the fridge, I need to check if there are any other items or methods available in the room to cool the mug. I will look around for any ice or cold water that might help cool the mug.
        OK.
        > go to sink 1
        On the sink 1, you see a pot 1, a houseplant 1, a plate 2, a faucet 1, a papertowelroll 1, a cellphone 3, a spatula 1, a spatula 2, and a glassbottle 2.
        > go to sink 2
        On the sink 2, you see a pot 1, a houseplant 1, a plate 2, a faucet 1, a papertowelroll 1, a cellphone 3, a spatula 1, a spatula 2, and a glassbottle 2.
        > think: It seems that both sinks have similar items and do not provide a way to cool the mug. I will check the other locations for any ice or cold water. Next, I will check the cabinets starting with cabinet 1.
        OK.
        > go to cabinet 1
        On the cabinet 1, you see a glassbottle 1, a cellphone 1, and a plate 1.
        > go to cabinet 2
        On the cabinet 2, you see a cellphone 2, a stoveknob 1, a pan 1, and a spoon 1.
        > go to cabinet 3
        Nothing happens.
        > go to cabinet 3
        Nothing happens.
        > go to cabinet 3
        Nothing happens.
        > go to cabinet 3
        Nothing happens.
        > open cabinet 3
        You open the cabinet 3. The cabinet 3 is open. In it, you see nothing.
        """
    )

    sg.update_graph(interaction_info)

    sg.display_graph()
    sg.display_initial_state()

    sg.save_to_json("/home/sawyer/Workspace/reflexion/alfworld_runs/scene_graph/scene_graph_with_initial_state.json")
    sg.load_from_json("/home/sawyer/Workspace/reflexion/alfworld_runs/scene_graph/scene_graph_with_initial_state.json")
