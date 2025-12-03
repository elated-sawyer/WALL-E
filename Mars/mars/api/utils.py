import numpy as np
BLOCK_NAME = ['stone', 'tree', 'iron', 'coal', 'diamond', 'water', 'lava', 'plant', 'zombie', 'sketelon', 'cow', 'grass']
ID2OBJ= {
    0: "boundary",
    1: 'water',
    2: 'grass',
    3: 'stone',
    4: 'path',
    5: 'sand',
    6: 'tree',
    7: 'lava',
    8: 'coal',
    9: 'iron',
    10: 'diamond',
    11: 'table',
    12: 'furnace',
    13: 'player',
    14: 'cow',
    15: 'zombie',
    16: 'skeleton',
    17: 'arrow',
    18: 'plant',
    19: 'ripe-plant'
}
WORLD_OBJECT = [
    "cow",
    "zombie",
    "skeleton",
    "arrow",
    "plant",
    "ripe-plant"
]
OBJ2ID = {v: k for k, v in ID2OBJ.items()}
VITALS = ["health","food","drink","energy"]
ACTIONS_NAME = [
    'noop',
    'move_left',
    'move_right',
    'move_up',
    'move_down',
    'do',
    'sleep',
    'place_stone',
    'place_table',
    'place_furnace',
    'place_plant',
    'make_wood_pickaxe',
    'make_stone_pickaxe',
    'make_iron_pickaxe',
    'make_wood_sword',
    'make_stone_sword',
    'make_iron_sword'
  ]

MOVE_LIST = {
    'move_left': (-1,0),
    'move_right': (1,0),
    'move_up': (0,1),
    'move_down': (0,-1),
    'move_up_left': (-1,1),
    'move_up_right': (1,1),
    'move_down_left': (-1,-1),
    'move_down_right': (1,-1)
}

DIRECTION_LIST = {
    'west': ['move_left'],
    'east': ['move_right'],
    'north': ['move_up'],
    'south': ['move_down'],
    'north-west': ['move_left', 'move_up'],
    'north-east': ['move_right', 'move_up'],
    'south-west': ['move_left', 'move_down'],
    'south-east': ['move_right', 'move_down']
}


def get_fov_types(info):
    pos = info['player_pos']
    obs = info['semantic']

    fov_size = np.array([9, 7])
    top_left = np.maximum(pos - fov_size // 2, 0)
    bottom_right = np.minimum(pos + fov_size // 2 + 1, obs.shape)
    fov = obs[top_left[0]:bottom_right[0], top_left[1]:bottom_right[1]]
    pad_top = top_left[0] - pos[0] + fov_size[0] // 2
    pad_bottom = pos[0] + fov_size[0] // 2 + 1 - bottom_right[0]
    pad_left = top_left[1] - pos[1] + fov_size[1] // 2
    pad_right = pos[1] + fov_size[1] // 2 + 1 - bottom_right[1]
    fov = np.pad(fov, ((pad_top, pad_bottom), (pad_left, pad_right)), mode='constant', constant_values=0)
    types = np.unique(fov)
    type_strings = [ID2OBJ[t] for t in types if t != 13]
    
    return type_strings