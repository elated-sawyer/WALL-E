import os
import json
import pandas as pd

def count_items_in_locations(directory):
    item_location_count = {}
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            with open(file_path, "r") as f:
                data = json.load(f)
            initial_items = data.get("initial_state", {}).get("items", {})
            for item, location in initial_items.items():
                location = location[:-2]
                key = (item, location)
                item_location_count[key] = item_location_count.get(key, 0) + 1

    items = sorted(set([k[0] for k in item_location_count.keys()]))
    locations = sorted(set([k[1] for k in item_location_count.keys()]))
    df = pd.DataFrame(0, index=items, columns=locations)

    for (item, location), count in item_location_count.items():
        df.at[item, location] = count
    
    return df

if __name__ == "__main__":
    directory = "/home/sawyer/Workspace/reflexion/alfworld_runs/scene_graph"  # 存放scene_graph.json文件的文件夹
    df = count_items_in_locations(directory)

    df.to_csv("/home/sawyer/Workspace/reflexion/alfworld_runs/scene_graph/item_location_distribution.csv")
    print("/home/sawyer/Workspace/reflexion/alfworld_runs/scene_graph/item_location_distribution.csv has been saved.")



