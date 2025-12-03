import argparse
import pathlib, os, json
import numpy as np
try:
  import pygame
except ImportError:
  print('Please install the pygame package to use the GUI.')
  raise
from PIL import Image
import imageio
import mars
import random
import mars.constants as constants
from datetime import datetime
import mars.globalvar as save_yaml

import cv2
import mars.check_techTree as check_techTree
def main():
  boolean = lambda x: bool(['False', 'True'].index(x))
  parser = argparse.ArgumentParser()
  parser.add_argument('--seed', type=int, default=None)
  parser.add_argument('--area', nargs=2, type=int, default=(64, 64))
  parser.add_argument('--view', type=int, nargs=2, default=(9, 9))
  parser.add_argument('--length', type=int, default=1000)
  parser.add_argument('--health', type=int, default=9)
  parser.add_argument('--window', type=int, nargs=2, default=(600, 600))
  parser.add_argument('--size', type=int, nargs=2, default=(0, 0))
  parser.add_argument('--record', type=pathlib.Path, default="myworld/test1")
  parser.add_argument('--fps', type=int, default=3)
  parser.add_argument('--wait', type=boolean, default=True)
  parser.add_argument('--death', type=str, default='quit', choices=[
      'continue', 'reset', 'quit'])
  parser.add_argument('--gen_world', type=boolean, default=True)
  # parser.add_argument('--default', type=boolean, default=True)
  parser.add_argument('--change_terrain', type=boolean, default=False)
  parser.add_argument('--terrian_kind', type=str, default='individual', choices=['permutation', 'individual', 'default'])
  parser.add_argument('--terrain_constraints', type=int, default=2)
  parser.add_argument('--change_npc', type=boolean, default=False) # original: True
  parser.add_argument('--npc_objects', type=list, default=['cow','zombie', 'skeleton','plant'])
  # parser.add_argument('--change_objects', type=list, default=['cow', 'zombie', 'skeleton'])
  parser.add_argument('--change_drink', type=boolean, default=False) # original: True
  parser.add_argument('--drink', type=list, default=['water', 'lava'])
  parser.add_argument('--change_walkable', type=boolean, default=False) # original: True
  
  parser.add_argument('--change_achievement', type=boolean, default=False)
  parser.add_argument('--collect_id', type=int, default=1)
  parser.add_argument('--revive', type=boolean, default=False)


  args = parser.parse_args()

  keymap = {
      pygame.K_a: 'move_left',
      pygame.K_d: 'move_right',
      pygame.K_w: 'move_up',
      pygame.K_s: 'move_down',
      pygame.K_SPACE: 'do',
      pygame.K_TAB: 'sleep',

      pygame.K_r: 'place_stone',
      pygame.K_t: 'place_table',
      pygame.K_f: 'place_furnace',
      pygame.K_p: 'place_plant',

      pygame.K_1: 'make_wood_pickaxe',
      pygame.K_2: 'make_stone_pickaxe',
      pygame.K_3: 'make_iron_pickaxe',
      pygame.K_4: 'make_wood_sword',
      pygame.K_5: 'make_stone_sword',
      pygame.K_6: 'make_iron_sword',
  }
  
  print('Actions:')
  for key, action in keymap.items():
    print(f'  {pygame.key.name(key)}: {action}')


  size = list(args.size)
  size[0] = size[0] or args.window[0]
  size[1] = size[1] or args.window[1]


  # timestamp = datetime.now().strftime("%Y%m%d%H%M")
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
  # constants.read_world(constants / 'data.yaml')
  args.load_world = args.record
  if args.gen_world:
    while True:
      
      env = mars.Env(
          area=args.area, view=args.view, length=args.length, seed=args.seed, args = args)
      
      
      env = mars.Recorder(env, args.record)
      obs = env.reset()
      
      terr_items = dict()
      for item,_ in constants.collect.items():
          print(f"{item} exists: {env._world.count(item)}")
          terr_items[item] = env._world.count(item)
      
      if check_techTree.check(constants, args.record, terr_items=terr_items):
        break
  else:
    env = mars.Env(
        area=args.area, view=args.view, length=args.length, seed=args.seed, args = args)

    env = mars.Recorder(env, args.record)
    obs = env.reset()


    terr_items = dict()
    for item,_ in constants.collect.items():
        print(f"{item} exists: {env._world.count(item)}")
        terr_items[item] = env._world.count(item)
    # assert check_techTree.check(constants, args.record, terr_items=terr_items)
  
   
  imageio.imsave(args.record / 'terrian.png', obs)



  

  # if args.regen_world:
  #   change_techTree.change_env_world(args.record / 'config.yaml', env._world.random)

  achievements = set()
  duration = 0
  return_ = 0
  was_done = False
  # print('Diamonds exist:', env._world.count('diamond'))
  # print('Coal exists:', env._world.count('coal'))
  # print('Iron exists:', env._world.count('iron'))



  # save_yaml.save_yaml(args.record / 'save_yaml.yaml')


  pygame.init()
  screen = pygame.display.set_mode(args.window)
  clock = pygame.time.Clock()
  running = True
  Tohuman = 'Hi, xiaojuan'
  while running:

    # Rendering.
    image = env.render(size)
    if size != args.window:
      image = Image.fromarray(image)
      image = image.resize(args.window, resample=Image.NEAREST)
      image = np.array(image)

    # # 确保图像是 uint8 类型
    # if image.dtype != np.uint8:
    #     image = image.astype(np.uint8)
    # if image.shape[2] == 3:  # 只有当图像是三通道的时候才需要转换
    #     image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    # 使用 OpenCV 在图像上加文字
    image = np.ascontiguousarray(image, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    # if Tohuman != '':
    #   print(Tohuman)
    cv2.putText(image, Tohuman, (50, 50), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

    surface = pygame.surfarray.make_surface(image.transpose((1, 0, 2)))
    screen.blit(surface, (0, 0))
    pygame.display.flip()
    clock.tick(args.fps)

    # Keyboard input.
    action = None
    pygame.event.pump()
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False
      elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        running = False
      elif event.type == pygame.KEYDOWN and event.key in keymap.keys():
        action = keymap[event.key]
    if action is None:
      pressed = pygame.key.get_pressed()
      for key, action in keymap.items():
        if pressed[key]:
          break
      else:
        if args.wait and not env._player.sleeping:
          continue
        else:
          action = 'noop'

    # Environment step.
    _, reward, done, info = env.step(env.action_names.index(action))
    duration += 1
    # Tohuman = info['Tohuman']
    # Achievements.
    unlocked = {
        name for name, count in env._player.achievements.items()
        if count > 0 and name not in achievements}
    for name in unlocked:
      achievements |= unlocked
      total = len(env._player.achievements.keys())
      print(f'Achievement ({len(achievements)}/{total}): {name}')
    if env._step > 0 and env._step % 100 == 0:
      print(f'Time step: {env._step}')
    if reward:
      print(f'Reward: {reward}')
      return_ += reward
    print("reward: ", info['all_reward'])

    # Episode end.
    if done and not was_done:
      was_done = True
      print('Episode done!')
      print('Duration:', duration)
      print('Return:', return_)
      if args.death == 'quit':
        running = False
      if args.death == 'reset':
        print('\nStarting a new episode.')
        env.reset()
        achievements = set()
        was_done = False
        duration = 0
        return_ = 0
      if args.death == 'continue':
        pass

  pygame.quit()
  


if __name__ == '__main__':
  main()
