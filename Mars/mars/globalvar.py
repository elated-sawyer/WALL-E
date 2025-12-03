import yaml, json
from yaml.representer import SafeRepresenter
from yaml.constructor import SafeConstructor
import pathlib
import copy
root = pathlib.Path(__file__).parent


# 定义特殊的字典类
class Inline(dict):
    pass

# 自定义Representer
def inline_dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data, flow_style=True)

# 自定义Constructor
def inline_dict_constructor(loader, node):
    return Inline(loader.construct_mapping(node))

# 注册到PyYAML
yaml.add_representer(Inline, inline_dict_representer)
yaml.add_constructor('tag:yaml.org,2002:map', inline_dict_constructor, SafeConstructor)



def _init():
    global _global_dict
    _global_dict = {}
    
    
def set_value(name, value):
    _global_dict[name] = value
 
def get_value(name, defValue=None):
    try:
        return _global_dict[name]
    except KeyError:
        return defValue

def process(yaml_dict):
    for item, value in yaml_dict.items():
        if item == 'npc_objects' or item == "drink":
            continue
        if isinstance(value, dict):
            for sub_item, sub_value in value.items():
                if isinstance(sub_value, dict):
                    yaml_dict[item][sub_item] = copy.deepcopy(Inline(sub_value))
    return yaml_dict

def save_yaml(filename, yaml_dict=None):
    yaml_dict = process(yaml_dict)
    with open(filename, 'w') as file:
        yaml.dump(yaml_dict, file, sort_keys=False, width=1024)




# def read_yaml(filename):
#     with open(root / filename, 'r') as file:
#         data = yaml.load(file, Loader=yaml.FullLoader)
#         for key, value in data.items():
#             _global_dict[key] = value



# for key, value in yaml.load((root / 'modified.yaml').read_text(), Loader=yaml.FullLoader).items():
#   globals()[key] = value