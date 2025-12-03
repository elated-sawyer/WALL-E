import argparse, pathlib
import mars
from utils import *
from controller import *
import pygame
import imageio

args = argparse.Namespace()
args.load_world = pathlib.Path("/home/txx/projects_new/CCrafter/test_world/default")
args.gen_world = False
args.seed = 0
args.window = (600,600)

pygame.init()
screen = pygame.display.set_mode(args.window)
clock = pygame.time.Clock()



env = mars.Env(seed= args.seed, args = args, screen=screen, clock=clock)
# obs = env.reset(save=True)
# imageio.imsave(args.record / 'terrian.png', obs)
env.reset()
# imageio.imsave(args.record / 'local_view.png', obs)


obs, reward, done, info = env.step(0)

bot = AgentController(env)
bot._envwapper.describe_frame()
bot.reset()
bot.mine("tree", 2)
bot.place('table')
bot.mine('tree',1)
bot.mine('stone', 1)
bot.craft('wood_pickaxe')



# bot.getToBlock('tree')
# bot.mineBlock('tree')
# bot.getToBlock('tree')
# bot.mineBlock('tree')
# bot.getToBlock('tree')
# bot.mineBlock('tree')
# bot.getToBlock('tree')
# bot.mineBlock('tree')
# env.step(ACTIONS_NAME.index('place_table'))
# env.step(ACTIONS_NAME.index('make_wood_pickaxe'))
# env.step(ACTIONS_NAME.index('make_wood_sword'))

# bot.mineBlock('tree', 2)
# bot.getToBlock('cow')
# bot.attackMob('cow')
# bot.mineBlock('cow')
# bot.followMob('cow')
# bot.attackMob('cow')


# bot.exploreUntil('stone', 'south_west')

# bot.getToBlock('stone')
# bot.mineBlock('stone')


pygame.quit()

