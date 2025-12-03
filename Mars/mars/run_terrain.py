import argparse
import pathlib, os, json
import imageio
import numpy as np

import mars

import random
import constants
from itertools import permutations

def main():
  boolean = lambda x: bool(['False', 'True'].index(x))
  parser = argparse.ArgumentParser()
  parser.add_argument('--seed', type=int, default=32)
  parser.add_argument('--amount', type=int, default=2)
  parser.add_argument('--cols', type=int, default=2)
  parser.add_argument('--area', nargs=2, type=int, default=(64, 64))
  parser.add_argument('--size', type=int, default=1024)
  parser.add_argument('--filename', type=str, default='terrain4.png')
  parser.add_argument('--gen_world', type=boolean, default=False)
  # parser.add_argument('--default', type=boolean, default=True)
  parser.add_argument('--change_terrain', type=boolean, default=True)
  parser.add_argument('--terrian_kind', type=str, default='individual', choices=['permutation', 'individual', 'default'])
  parser.add_argument('--terrain_constraints', type=int, default=1)
  parser.add_argument('--change_npc', type=boolean, default=False)
  parser.add_argument('--npc_objects', type=list, default=['cow','zombie', 'skeleton'])
  # parser.add_argument('--change_objects', type=list, default=['cow', 'zombie', 'skeleton'])
  parser.add_argument('--change_drink', type=boolean, default=False)
  parser.add_argument('--change_walkable', type=boolean, default=False)
  parser.add_argument('--drink', type=list, default=['water', 'lava'])
  parser.add_argument('--change_achievement', type=boolean, default=False)

  args = parser.parse_args()


  # # process random generate world
  # terrain_material = constants.terrain_materials
  # changeable = ['coal', 'iron', 'diamond', 'water', 'tree', 'player']
  # terrain_neighbor = {}
  # name2name = {}
  # default_neighbor = constants.default_material_neighbour
  # if args.change_terrain:
  #   if args.terrian_kind == 'permutation':
      
  #     while True:
  #       flag = True
  #       shuffled_materials = random.sample(constants.terrain_materials, len(constants.terrain_materials))
  #       name2name = {item: shuffled_materials[idx] for idx, item in enumerate(constants.terrain_materials)}
  #       name2name['player'] = 'player'
  #       # check if satisfy the constraints
  #       constraints = constants.material_neighbour_2
  #       for key, value in default_neighbor.items():
  #         mod_key, mod_value = name2name[key], name2name[value]
  #         if mod_key in constraints and mod_value not in constraints[mod_key]:
            
  #           print(f'Error: {mod_key} -> {mod_value} is not allowed')
  #           flag = False
  #           break
  #       if flag:
  #         break
  #     # print the name2name
  #     print('Name2Name:')
  #     for key, value in name2name.items():
  #       print(f'  {key}: {value}')
      
  #     # print the modified terrain_neighbor
  #     print('Modified Terrain Neighbor:')
  #     for key, value in default_neighbor.items():
  #       print(f'  {name2name[key]}: {name2name[value]}')
  #   elif args.terrian_kind == 'individual':
  #     for item in changeable:
  #       terrain_neighbor[item] = random.choice(terrain_material)

  #       # print the terrain_neighbor
  #       print('Terrain Neighbor:')
  #       for key, value in terrain_neighbor.items():
  #         print(f'  {key}: {value}')
    
    
    # 如果要重新创建一个世界
  gen_world = args.gen_world
  if args.gen_world:

    if not os.path.exists(args.record):
      os.makedirs(args.record)
    config = {k: str(v) if isinstance(v, pathlib.PurePath) else v for k, v in vars(args).items()}
    with open(args.record / 'config.json', 'w') as file:
      json.dump(config, file)
  
  # else:
    # 直接读取世界
  with open(args.record / 'config.json', 'r') as f:
    config = json.load(f)
  
  # Override args with values from the config if they exist
  for key, value in config.items():
      if hasattr(args, key):
          if key == 'record':
            value = pathlib.Path(value)
          setattr(args, key, value)
  
  args.gen_world = gen_world

  env = mars.Env(args.area, args.area, args.size, seed=args.seed, args=args)
  
  
  images = []
  for index in range(args.amount):
    images.append(env.reset())
    diamonds = env._world.count('diamond')
    print(f'Map: {index:>2}, diamonds: {diamonds:>2}')

  rows = len(images) // args.cols
  strips = []
  for row in range(rows):
    strip = []
    for col in range(args.cols):
      try:
        strip.append(images[row * args.cols + col])
      except IndexError:
        strip.append(np.zeros_like(strip[-1]))
    strips.append(np.concatenate(strip, 1))
  grid = np.concatenate(strips, 0)
  # grid =strips


  imageio.imsave(args.filename, grid)
  print('Saved', args.filename)


if __name__ == '__main__':
  main()
