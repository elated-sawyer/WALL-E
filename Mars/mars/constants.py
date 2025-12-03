import pathlib

import ruamel.yaml

root = pathlib.Path(__file__).parent
yaml = ruamel.yaml.YAML(typ='safe', pure=True)

# contraints = dict()
# data_yaml = dict()

# for key, value in yaml.load((root / 'data.yaml').read_text()).items():
#   # data_yaml[key] = value
#   globals()[key] = value

global _world_yaml 


_world_yaml = {}
# _constraints = {}

for key, value in yaml.load((root / 'meta_constraints.yaml').read_text()).items():
  globals()[key] = value
  # contraints[key] = value

# def modified(modified):
#   if modified:

# for key, value in yaml.load((root / 'data.yaml').read_text()).items():
#   globals()[key] = value

def read_world(filename):

  for key, value in yaml.load(filename.read_text()).items():
    globals()[key] = value
    _world_yaml[key] = value


# for key, value in yaml.load((root / 'techTree.yaml').read_text()).items():
#   globals()[key] = value