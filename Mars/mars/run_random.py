import argparse
import pathlib, os, json
import time
import imageio
import pygame
import numpy as np
from PIL import Image
import mars
import constants
import random
from datetime import datetime
import globalvar as save_yaml

def main():
  boolean = lambda x: bool(['False', 'True'].index(x))
  parser = argparse.ArgumentParser()
  parser.add_argument('--seed', type=int, default=0)
  # 整个地形图的大小
  parser.add_argument('--area', nargs=2, type=int, default=(64, 64))
  # 每个episode的长度
  parser.add_argument('--length', type=int, default=10000)

  # parser.add_argument('--health', type=int, default=9)
  # Record 保存在哪里
  parser.add_argument('--record', type=pathlib.Path, default="create_world/world_high7")

  
  parser.add_argument('--episodes', type=int, default=1)

  # 渲染窗口的大小？
  parser.add_argument('--size', type=int, nargs=2, default=(0, 0))
  parser.add_argument('--window', type=int, nargs=2, default=(600, 600))
  parser.add_argument('--fps', type=int, default=5)
  parser.add_argument('--gen_world', type=boolean, default=False)
  # parser.add_argument('--default', type=boolean, default=True)
  parser.add_argument('--change_terrain', type=boolean, default=True)
  parser.add_argument('--terrian_kind', type=str, default='individual', choices=['permutation', 'individual', 'default'])
  parser.add_argument('--terrain_constraints', type=int, default=1)
  parser.add_argument('--change_npc', type=boolean, default=False)
  parser.add_argument('--npc_objects', type=list, default=[])
  # parser.add_argument('--change_objects', type=list, default=['cow', 'zombie', 'skeleton'])
  parser.add_argument('--change_drink', type=boolean, default=False)

  parser.add_argument('--drink', type=list, default=[])
  parser.add_argument('--change_achievement', type=boolean, default=False)
  # parser.add_argument('--outdir', default='logdir/debug')
  args = parser.parse_args()

  # 保证生成相同的随机数列
  # [3.1,3.2]
  # next time: [3.1,3.2]
  # random = np.random.RandomState(args.seed)


  timestamp = datetime.now().strftime("%Y%m%d%H%M")
  # args.record = args.record / timestamp

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
  
  # save_yaml._init()

  # save_yaml.set_value('seed', args.seed)
  # save_yaml.set_value('change_terrain', args.change_terrain)
  # save_yaml.set_value('terrian_kind', args.terrian_kind)
  # save_yaml.set_value('change_objects', args.change_objects)
  # save_yaml.set_value('change_drink', args.change_drink)

  # # process random generate world
  # terrain_material = constants.terrain_materials
  # changeable = ['coal', 'iron', 'diamond', 'water', 'tree', 'player']
  # terrain_neighbor = {}
  # name2name = {}
  # default_neighbor = constants.default_material_neighbour
  # terrain_materials_mark = list()

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

      
  #     save_yaml.set_value('name2name', name2name)
  #     # print the modified terrain_neighbor
  #     print('Modified Terrain Neighbor:')
  #     for key, value in default_neighbor.items():
  #       print(f'  {name2name[key]}: {name2name[value]}')

  #   elif args.terrian_kind == 'individual':
  #     while True:
  #       for item in changeable:
  #         terrain_neighbor[item] = random.choice(terrain_material)

  #         if item not in terrain_materials_mark:
  #           terrain_materials_mark.append(item)
  #         if terrain_neighbor[item] not in terrain_materials_mark:
  #           terrain_materials_mark.append(terrain_neighbor[item])

  #       # check terrain_materials_mark contain all the terrain_material
  #       if len(terrain_materials_mark) == len(terrain_material):
  #         break

  #       # print the terrain_neighbor
  #       print('Terrain Neighbor:')
  #       for key, value in terrain_neighbor.items():
  #         print(f'  {key}: {value}')
  #       # global_save_yaml['terrain_neighbor'] = terrain_neighbor
  #       save_yaml.set_value('terrain_neighbor', terrain_neighbor)
    
  # # else:
  #   save_yaml['name2name'] = {}
  #   save_yaml['terrain_neighbor'] = {}
    

  # # process change objects' food
  # food_setting = dict()
  # random_number = lambda: int(random.choice([1, -1]))
  # for item in args.change_objects:
  #   if item not in food_setting:
  #     food_setting[item] = dict()
  #   food_setting[item]['inc_food_func'] = random_number()
  
  # save_yaml.set_value('food', food_setting)

  # process change drink: water, lava (drinkable / damageable / walkable)
  # drink_setting = dict()
  # random_number = lambda: int(random.choice([1, -1]))
  # random_bool = lambda: bool(random.choice([True, False]))

  
  # for item in args.change_drink:
  #   if item not in drink_setting:
  #     drink_setting[item] = dict()

  #   while True:
  #     drink_setting[item]['walkable'] = random_bool()
  #     drink_setting[item]['dieable'] = random_bool()
  #     if drink_setting[item]['dieable'] and not drink_setting[item]['walkable']:
  #       continue
  #     else:
  #       break
  #   if not drink_setting[item]['dieable']:
      
  #     drink_setting[item]['inc_drink_func'] = random_number()
  #     drink_setting[item]['inc_damage_func'] = random_number()
    
  # save_yaml.set_value('drink', drink_setting)




  env = mars.Env(area=args.area, length=args.length, seed=args.seed, args=args)

  
  env = mars.Recorder(env, args.record, save_video=True)


  pygame.init()
  screen = pygame.display.set_mode(args.window)
  clock = pygame.time.Clock()
  

  for _ in range(args.episodes):
    
    id = 0
    start = time.time()
    obs = env.reset()
    imageio.imsave(args.record / 'terrian.png', obs)
    # filename = args.record / f'{0:06d}.png'
    # imageio.imsave(filename, obs)

    size = list(args.size)
    size[0] = size[0] or args.window[0]
    size[1] = size[1] or args.window[1]
    


    print('')
    print(f'Reset time: {1000*(time.time()-start):.2f}ms')
    print('Coal exist:    ', env._world.count('coal'))
    print('Iron exist:    ', env._world.count('iron'))
    print('Diamonds exist:', env._world.count('diamond'))

    start = time.time()
    done = False
    # actions = [1,3,3,3,5,1,1,5,1,5,8,4,4,4,4,4,4,4,1,1,1,1,1,4,4,4,1,1,1,2,2,2,2,3,1,1,1]
    actions = [3,5,4,4,4,4]
    # actions = [5,5,5,5,5,5,5]
    while not done:

      # Rendering.
      image = env.render(size)
      if size != args.window:
        image = Image.fromarray(image)
        image = image.resize(args.window, resample=Image.NEAREST)
        image = np.array(image)
      surface = pygame.surfarray.make_surface(image.transpose((1, 0, 2)))
      screen.blit(surface, (0, 0))
      pygame.display.flip()
      clock.tick(args.fps)


      # action = random.randint(0, env.action_space.n)
      if id >= len(actions):
        action = random.randint(0, env.action_space.n)
      else:
        action = actions[id]
      obs, reward, done, info = env.step(action)
      # filename = args.record / f'{id:06d}.png'
      # imageio.imsave(filename, obs)
      id += 1
    duration = time.time() - start
    step = env._step
    print(f'Step time: {1000*duration/step:.2f}ms ({int(step/duration)} FPS)')
    print('Episode length:', step)

  pygame.quit()
if __name__ == '__main__':
  main()
