import functools

import numpy as np
import opensimplex

from . import constants
from . import objects


def generate_world(world, player):
  simplex = opensimplex.OpenSimplex(seed=world.random.randint(0, 2 ** 31 - 1))
  tunnels = np.zeros(world.area, bool)
  for x in range(world.area[0]):
    for y in range(world.area[1]):
      _set_material(world, (x, y), player, tunnels, simplex)
  for x in range(world.area[0]):
    for y in range(world.area[1]):
      _set_object(world, (x, y), player, tunnels)


def _set_material(world, pos, player, tunnels, simplex):
  x, y = pos
  simplex = functools.partial(_simplex, simplex)
  uniform = world.random.uniform
  start = 4 - np.sqrt((x - player.pos[0]) ** 2 + (y - player.pos[1]) ** 2)
  start += 2 * simplex(x, y, 8, 3)
  start = 1 / (1 + np.exp(-start))
  water = simplex(x, y, 3, {15: 1, 5: 0.15}, False) + 0.1
  water -= 2 * start
  mountain = simplex(x, y, 0, {15: 1, 5: 0.3})
  mountain -= 4 * start + 0.3 * water

  cave_cond = simplex(x, y, 6, 7) > 0.15
  horizonal_tunnel_cond = simplex(2 * x, y / 5, 7, 3) > 0.4
  vertical_tunnel_cond = simplex(x / 5, 2 * y, 7, 3) > 0.4
  coal_cond = simplex(x, y, 1, 8) > 0
  iron_cond = simplex(x, y, 2, 6) > 0.2
  diamond_cond = mountain > 0.18 
  lava_cond = mountain > 0.3 and simplex(x, y, 6, 5) > 0.15
  
  conditions = {
    'cave': cave_cond,
    'horizonal_tunnel': horizonal_tunnel_cond,
    'vertical_tunnel': vertical_tunnel_cond,
    
    'diamond': diamond_cond,
    'iron': iron_cond,
    'coal': coal_cond,
    'lava': lava_cond,
    
    
    # 'lava': lava_cond,
    

}


  # world.terrian_change = {}
  # terrian_change = {}
  # terrian_change['coal'] = 'grass'
  # terrian_change['iron'] = 'grass'
  # terrian_change['diamond'] = 'grass'
  # terrian_change['water'] = 'sand'
  # terrian_change['tree'] = 'grass'

  if start > 0.5:
    # world[x, y] = 'grass'
    world[x, y] = world._name2name[world._terrain_neighbor['player']]
  elif mountain > 0.15:
    if (simplex(x, y, 6, 7) > 0.15 and mountain > 0.3):  # cave
      world[x, y] = world._name2name['path']
    elif simplex(2 * x, y / 5, 7, 3) > 0.4:  # horizonal tunnle
      world[x, y] = world._name2name['path']
      tunnels[x, y] = True
    elif simplex(x / 5, 2 * y, 7, 3) > 0.4:  # vertical tunnle
      world[x, y] = world._name2name['path']
      tunnels[x, y] = True
    elif simplex(x, y, 1, 8) > 0 and uniform() > 0.85: 
      world[x, y] = world._name2name['coal']
    elif simplex(x, y, 2, 6) > 0.4 and uniform() > 0.70:
      world[x, y] = world._name2name['iron']
    # elif mountain > 0.18 and uniform() > 0.994:
    elif mountain > 0.18 and uniform() > 0.884:
      world[x, y] = world._name2name['diamond']
    elif mountain > 0.3 and simplex(x, y, 6, 5) > 0.35:
      world[x, y] = world._name2name['lava']
    else:
      world[x, y] = world._name2name['stone']
      for obj, cond in conditions.items():
        if cond:
            # and world._terrain_neighbor[obj] != 'stone
            if obj in world._terrain_neighbor :
              world[x, y] = world._name2name[world._terrain_neighbor[obj]]
            
        # else:
        #     world[x, y] = 'stone'
      # # if coal_simplex or iron_simplex:
      # #   world[x, y] = 'lava'
      # # if iron_simplex > 0.4:
      # #   world[x, y] = 'lava'
      # else:
      #   world[x, y] = 'stone'


  elif 0.25 < water <= 0.35 and simplex(x, y, 4, 9) > -0.2:
    # world[x, y] = 'sand'
    world[x, y] = world._name2name[world._terrain_neighbor['water']]
  elif 0.3 < water:
    world[x, y] = world._name2name['water']
  else:  # grassland
    if simplex(x, y, 5, 7) > 0 and uniform() > 0.8:
      world[x, y] = world._name2name['tree']
    else:
      # world[x, y] = 'grass'
      world[x, y] = world._name2name[world._terrain_neighbor['tree']]
      # if uniform() > 0.8:
      #   world[x, y] = world._name2name[world._terrain_neighbor['tree']]
      # else:
      #   world[x, y] = 'grass'


def _set_object(world, pos, player, tunnels):
  x, y = pos
  uniform = world.random.uniform
  dist = np.sqrt((x - player.pos[0]) ** 2 + (y - player.pos[1]) ** 2)
  material, _ = world[x, y]
  # if material not in constants.walkable:
  #   pass
  if dist > 3 and material == world._name2name[world._terrain_neighbor['tree']] and uniform() > 0.985:
    world.add(objects.Cow(world, (x, y),  player))
  # elif dist > 10 and uniform() > 0.993:
  elif dist > 10 and uniform() > 0.998 and material in constants.walkable:
    world.add(objects.Zombie(world, (x, y), player))
  elif material == world._name2name['path'] and tunnels[x, y] and uniform() > 0.95:
    world.add(objects.Skeleton(world, (x, y), player))


def _simplex(simplex, x, y, z, sizes, normalize=True):
  if not isinstance(sizes, dict):
    sizes = {sizes: 1}
  value = 0
  for size, weight in sizes.items():
    if hasattr(simplex, 'noise3d'):
      noise = simplex.noise3d(x / size, y / size, z)
    else:
      noise = simplex.noise3(x / size, y / size, z)
    value += weight * noise
  if normalize:
    value /= sum(sizes.values())
  return value