import numpy as np

import mars.constants as constants
from . import engine

# import globalvar as save_yaml


class Object:

  def __init__(self, world, pos):
    self.world = world
    self.pos = np.array(pos)
    self.random = world.random
    self.inventory = {'health': 0}
    self.removed = False
    self.leaves = None
    self.class_dict = {
    # 'beef': Beef,
    # 'bone': Bone,
    # 'rotten_flesh': Rotten_Flesh,
    'arrow': Arrow,
    'cow': Cow,
    'zombie': Zombie,
    'skeleton': Skeleton,
    'plant': Plant,
    'fence': Fence,


}
    
    
    

  def npc(self, player):
    
    class_name = self.__class__.__name__.lower()
    self.cooldown = 5
    self.reload = 0

    # self.default()


    # if class_name in constants.npc_objects:
      
      # # random sample
      # random_bool = lambda: bool(self.random.choice([True, False]))
      # random_number = lambda: int(self.random.choice([1, -1]))
    self.eatable_flag = constants.npc_objects[class_name]['eatable']
    self.defeatable_flag =  constants.npc_objects[class_name]['defeatable']
    self.attackable_flag = constants.npc_objects[class_name]['attackable']
    self.closable_flag = constants.npc_objects[class_name]['closable']
    self.arrowable_flag = constants.npc_objects[class_name]['arrowable']
    self.canwalk = constants.npc_objects[class_name]['can_walk']
    self.inc_food_func = constants.npc_objects[class_name]['inc_food_func']
    self.closable_health_damage_func = constants.npc_objects[class_name]['closable_health_damage_func']
    self.eat_health_damage_func = constants.npc_objects[class_name]['eat_health_damage_func']
    self.arrow_damage_func = constants.npc_objects[class_name]['arrow_damage_func']
    self.inc_thirst_func = constants.npc_objects[class_name]['inc_thirst_func']
    self.player = player
    
    
    


    assert  (self.eatable_flag + self.defeatable_flag) == 1

    
    # npc_setting = dict()
    # npc_setting['eatable'] = self.eatable_flag
    # npc_setting['defeatable'] = self.defeatable_flag
    # npc_setting['attackable'] = self.attackable_flag
    # npc_setting['arrowable'] = self.arrowable_flag
    # npc_setting['closable'] = self.closable_flag
    # npc_setting['health_damage_func'] = self.health_damage_func
    # npc_setting['arrow_damage_func'] = self.arrow_damage_func
    # npc_setting['inc_food_func'] = self.inc_food_func
    # npc_setting['inc_thirst_func'] = self.inc_thirst_func

    # save_yaml.set_value(class_name, npc_setting)
    # if self.arrowable_flag:
    #   self.closable_flag = False
    # if self.attackable_flag == True:
      
    # assert (self.attackable_flag + self.closeable_flag + self.unclosable_flag) <= 1


  @property
  def texture(self):
    raise 'unknown'

  @property
  def walkable(self):
    return constants.walkable

  @property
  def health(self):
    return self.inventory['health']

  @health.setter
  def health(self, value):
    self.inventory['health'] = max(0, value)

  @property
  def all_dirs(self):
    return ((-1, 0), (+1, 0), (0, -1), (0, +1))

  
  # def default(self):
  #   pass


  def move(self, direction):
    direction = np.array(direction)
    target = self.pos + direction
    # if object is player
    

    if self.is_free(target):
      self.world.move(self, target)
      
      self.event = 'I successfully moved.'
      self.action_result = 'I executed successfully. '
      return True
    
    self.event = 'I failed to move.'
    self.action_result = 'I failed to execute. '
    return False

  def is_free(self, target, materials=None):
    materials = self.walkable if materials is None else materials
    material, obj = self.world[target]
    return obj is None and material in materials

  def distance(self, target):
    if hasattr(target, 'pos'):
      target = target.pos
    return np.abs(target - self.pos).sum()

  def toward(self, target, long_axis=True):
    if hasattr(target, 'pos'):
      target = target.pos
    offset = target - self.pos
    dists = np.abs(offset)
    if (dists[0] > dists[1] if long_axis else dists[0] <= dists[1]):
      return np.array((np.sign(offset[0]), 0))
    else:
      return np.array((0, np.sign(offset[1])))

  def random_dir(self):
    return self.all_dirs[self.random.randint(0, 4)]

  # 是否是可食用的，即便可食用，吃完后也可能会对player的生命状态造成影响
  def eatable(self):
    class_name = self.__class__.__name__.lower()
    if self.eatable_flag:
      if self.health <= 0:
        # print("eatable_flag")
        self.player.task_completed = 'success'
        self.player.inventory['food'] += self.inc_food_func * 6
        self.player.inventory['drink'] += self.inc_thirst_func
        self.player.inventory['health'] += self.eat_health_damage_func * 2
        # get the class name
        
        # if 'kill_' + class_name not in self.player.achievements:
        #   self.player.achievements['kill_' + class_name] = 0
        # self.player.achievements['kill_' + class_name] += 1
        if 'kill_' + class_name not in self.player.achievements:
          self.player.achievements['kill_' + class_name] = 0
        self.player.achievements['kill_' + class_name] += 1
        self.player.event += f"{class_name} died. "
        # self.player.action_result = 'I executed successfully. '
        self.player.hunger = 0
        if self.inc_thirst_func != 0:
          self.player.thirst = 0
      else:
        self.player.task_completed = 'failed'
        self.player.event += f"{class_name} is not dead yet. "
        # self.player.action_result = 'I failed to execute. '

  def defeatable(self):
    class_name = self.__class__.__name__.lower()
    if self.defeatable_flag:
      if self.health <= 0:
        # print("defeatable_flag")
        self.player.task_completed = 'success'
        
        if 'kill_' + class_name not in self.player.achievements:
          self.player.achievements['kill_' + class_name] = 0
        self.player.achievements['kill_' + class_name] += 1
        self.player.event += f"{class_name} died. "
        # if 'eat_' + class_name not in self.player.achievements:
        #   self.player.achievements['eat_' + class_name] = 0
        # self.player.achievements['eat_' + class_name] += 1
      else:
        self.player.task_completed = 'failed'
        self.player.event += f"{class_name} is not dead yet. "
    
  # 是否会有攻击行为
  def attackable(self):
    if self.attackable_flag:
      dist = self.distance(self.player)
      if dist <= 1:
        if self.cooldown:
          self.cooldown -= 1
        else:
          if self.player.sleeping:
            damage = 7
          else:
            damage = 2
          self.player.health += self.closable_health_damage_func * damage
          self.cooldown = 5
        

  def closable(self):
    if not self.arrowable_flag:
      if self.closable_flag:
        dist = self.distance(self.player)
        if dist <= 8 and self.random.uniform() < 0.9:
          self.move(self.toward(self.player, self.random.uniform() < 0.8))
        else:
          self.move(self.random_dir())
      elif self.canwalk:
        if self.random.uniform() < 0.5:
          direction = self.random_dir()
          self.move(direction)
    
      
  # 是否会放箭【其中包括了会closable】
  def arrowable(self):
    if self.arrowable_flag:
      self.reload = max(0, self.reload - 1)
      dist = self.distance(self.player.pos)
      if dist <= 5 and self.random.uniform() < 0.5:
        self._shoot(self.toward(self.player))
      elif dist <= 8 and self.random.uniform() < 0.3:
        self.move(self.toward(self.player, self.random.uniform() < 0.6))
      elif self.random.uniform() < 0.2:
        self.move(self.random_dir())

      return True

  def _shoot(self, direction):
    if self.reload > 0:
      return
    if direction[0] == 0 and direction[1] == 0:
      return
    pos = self.pos + direction
    if self.is_free(pos, Arrow.walkable):
      self.world.add(Arrow(self.world, pos, direction, self.arrow_damage_func))
      self.reload = 4
      
  # # 无害的
  # def unclosable(self):
  #   if self.unclosable_flag:
  #     if self.random.uniform() < 0.5:
  #       direction = self.random_dir()
  #       self.move(direction)

  def update(self):
    if self.health <= 0:
      self.world.remove(self)
      # if self.leaves:
      #   Leaves = self.class_dict[self.leaves](self.world, self.pos, self.player)
      #   self.world.add(Leaves)
      # please follow specific leaves to create class, e.g., cow leaves is beef
      
      # self.world[self.pos] = self.leaves

    self.arrowable()
    self.closable()
    self.attackable()

class Player(Object):

  def __init__(self, world, pos):
    super().__init__(world, pos)
    self.facing = (0, 1)
    self.inventory = {
        name: info['initial'] for name, info in constants.items.items()}
    self.achievements = {name: 0 for name in constants.achievements}
    self.action = 'noop'
    self.sleeping = False
    self._last_health = self.health
    self._hunger = 0
    self._thirst = 0
    self._fatigue = 0
    self._recover = 0
    self.task_completed = '' # success / failed
    # self._change_life_func = {item: 1 for item in constants.changeable_life_states}
    # if change_life_stats:
    #   for item in constants.changeable_life_states:
    #     self._change_life_func[item] = world.random.choice([1, -1])
    self.event = 'Nothing happened. '
    self.action_result = ''
    self.block_interact = ''
      

  @property
  def texture(self):
    if self.sleeping:
      return 'player-sleep'
    return {
        (-1, 0): 'player-left',
        (+1, 0): 'player-right',
        (0, -1): 'player-up',
        (0, +1): 'player-down',
    }[tuple(self.facing)]

  # @property
  # def walkable(self):
  #   # player_walkable = constants.walkable 
  #   player_walkable = []
  #   for item in constants.walkable_effect:
  #     if constants.walkable_effect[item]['walkable']:
  #       player_walkable.append(item)
  
  #   return player_walkable

  def update(self):
    target = (self.pos[0] + self.facing[0], self.pos[1] + self.facing[1])
    material, obj = self.world[target]
    action = self.action
    if self.sleeping:
      if self.inventory['energy'] < constants.items['energy']['max']:
        action = 'sleep'
      else:
        self.sleeping = False
        self.task_completed = 'success'
        self.achievements['wake_up'] += 1
    if action == 'noop':
      pass
    elif action.startswith('move_'):
      self._move(action[len('move_'):])
    elif action == 'do' and obj:
      self._do_object( obj)
    elif action == 'do':
      self._do_material(target, material)
    elif action == 'sleep':
      if self.inventory['energy'] < constants.items['energy']['max']:
        self.sleeping = True
        self.task_completed = 'success'
    elif action.startswith('place_'):
      self._place(action[len('place_'):], target, material)
    elif action.startswith('make_'):
      self._make(action[len('make_'):])
    self._update_life_stats()
    self._degen_or_regen_health()
    for name, amount in self.inventory.items():
      maxmium = constants.items[name]['max']
      self.inventory[name] = max(0, min(amount, maxmium))
    # This needs to happen after the inventory states are clamped
    # because it involves the health water inventory count.
    self._wake_up_when_hurt()

  def _update_life_stats(self):
    # self._hunger += self._change_life_func['hunger'] * (0.5 if self.sleeping else 1)
    self._hunger += 0.5 if self.sleeping else 1
    if self._hunger > 25:
      self._hunger = 0
      self.inventory['food'] -= 1
    self._thirst += 0.5 if self.sleeping else 1
    if self._thirst > 20:
      self._thirst = 0
      self.inventory['drink'] -= 1
    if self.sleeping:
      self._fatigue = min(self._fatigue - 1, 0)
    else:
      self._fatigue += 1
    if self._fatigue < -10:
      self._fatigue = 0
      self.inventory['energy'] += 1
    if self._fatigue > 30:
      self._fatigue = 0
      self.inventory['energy'] -= 1

  def _degen_or_regen_health(self):
    necessities = (
        self.inventory['food'] > 0,
        self.inventory['drink'] > 0,
        self.inventory['energy'] > 0 or self.sleeping)
    if all(necessities):
      self._recover += 2 if self.sleeping else 1
    else:
      self._recover -= 0.5 if self.sleeping else 1
    if self._recover > 25:
      self._recover = 0
      self.health += 1
    if self._recover < -15:
      self._recover = 0
      self.health -= 1

  def _wake_up_when_hurt(self):
    if self.health < self._last_health:
      if self.sleeping:
        self.task_completed = 'failed'
      self.sleeping = False
      
    self._last_health = self.health

  def _move(self, direction):
    directions = dict(left=(-1, 0), right=(+1, 0), up=(0, -1), down=(0, +1))
    self.facing = directions[direction]
    self.move(self.facing)
    material = self.world[self.pos][0]
    if material in constants.walkable_effect:
      if constants.walkable_effect[material]['dieable']:
        self.health = 0
      else:
        self.health += constants.walkable_effect[material]['walk_health'] 
    # for item in constants.drink:
    #   if self.world[self.pos][0] == item:
        
    #     if constants.drink[item]['dieable']:
    #       self.health = 0
    #     else:
    #       self.health += constants.drink[item]['inc_damage_func'] * 2

  def _do_object(self, obj):
    self.action_result = 'I executed successfully. '
    self.block_interact = obj.__class__.__name__.lower()
    self.event = 'I interacted with {} in front of me. '.format(obj.__class__.__name__.lower())
    damage = max([
        1,
        self.inventory['wood_sword'] and 2,
        self.inventory['stone_sword'] and 3,
        self.inventory['iron_sword'] and 5,
    ])
    if isinstance(obj, Plant):
      if obj.ripe:
        obj.grown = 0
        self.inventory['food'] += obj.inc_food_func * 4
        self.inventory['drink'] += obj.inc_thirst_func * 2
        self.inventory['health'] += obj.eat_health_damage_func 
        self.achievements['eat_plant'] += 1
        self.event += 'I ate a ripe plant. '
    

    elif isinstance(obj, Fence):
      self.world.remove(obj)
      self.inventory['fence'] += 1
      self.achievements['collect_fence'] += 1
      self.event += 'I collected a fence. '

    elif isinstance(obj, Object) and not isinstance(obj, Arrow):
      obj.health -= damage

      obj.eatable()
      obj.defeatable()


    # if isinstance(obj, Zombie):
    #   obj.health -= damage

    #   # obj.eatable(True)

    #   if obj.health <= 0:
    #     self.achievements['defeat_zombie'] += 1


    # if isinstance(obj, Skeleton):
    #   obj.health -= damage

    #   # obj.eatable(True)

    #   if obj.health <= 0:
    #     self.achievements['defeat_skeleton'] += 1

    
    # if isinstance(obj, Cow):
    #   obj.health -= damage

    #   # obj.eatable(True)

    #   if obj.health <= 0:
    #     self.inventory['food'] += self._change_life_func['food'] * 6
    #     self.achievements['eat_cow'] += 1
    #     # TODO: Keep track of previous inventory state to do this in a more
    #     # general way.
    #     self._hunger = 0

  def _do_material(self, target, material):
    self.action_result = 'I failed to execute. '
    self.block_interact = material
    self.event = 'I failed to mine {} block in front of me. '.format(material)
    info = constants.collect.get(material)
    if not info:
      self.task_completed = 'failed'
      
      return
    for name, amount in info['require'].items():
      if self.inventory[name] < amount:
        self.task_completed = 'failed'
        return
    self.event = f"I successfully mined {material} block in front of me. "
    self.action_result = 'I executed successfully. '
    if material in constants.drink: ## TODO 
      # TODO: Keep track of previous inventory state to do this in a more
      # general way.
      # self._thirst = 0
      self.inventory['drink'] += constants.drink[material]['inc_drink_func']
      self.inventory['food'] += constants.drink[material]['inc_food_func']
      self.inventory['health'] += constants.drink[material]['inc_damage_func']

    
    self.world[target] = info['leaves']['material']
    self.event += f"After mining, the remaining block is {info['leaves']['material']} "
    # if material == 'tree':
    #   # 此时挖出的僵尸最好是同一种属性 TODO
    #   self.world.add(Zombie(self.world, target, self))
    # print(info['leaves']['object'])
    if info['leaves']['object'] and len(info['leaves']['object'])>0:
      obj_prob = info['leaves']['object']
      obj_name = list(obj_prob.keys())[0]
      probablity = list(obj_prob.values())[0]
      if self.random.uniform() <= probablity:
        obj = self.class_dict[obj_name](self.world, target, self)
        self.world.add(obj) 
        self.event += f"and a {obj_name} appeared. "
      else:
        self.event += f". "
    
    # if self.random.uniform() <= info.get('probability', 1):
    random_num = self.random.uniform()
    pre_prob = 0
    for name, amount in info['receive'].items():
      if isinstance(amount, dict):
        amount_num = amount['amount']
        
        post_prob = pre_prob + amount.get('probability', 1)
        
        if pre_prob < random_num <= post_prob:
          self.inventory[name] += amount_num
          if f"collect_{name}" in self.achievements:
            self.achievements[f'collect_{name}'] += 1
          self.event += f"I collected {amount_num} {name}. "
        pre_prob = post_prob
      else:
        self.inventory[name] += amount
        self.achievements[f'collect_{name}'] += 1
        self.event += f"I collected {amount} {name}. "
    
    # print("do_material")
    self.task_completed = 'success'

    
  def _place(self, name, target, material):
    self.event = f"I failed to place {name} in front of me. "
    self.action_result = 'I failed to execute. '
    if self.world[target][1]:
      self.task_completed = 'failed'
      
      return
    info = constants.place[name]
    if material not in info['where']:
      self.task_completed = 'failed'
      
      return
    if any(self.inventory[k] < v for k, v in info['uses'].items()):
      self.task_completed = 'failed'
      return
    for item, amount in info['uses'].items():
      self.inventory[item] -= amount
    if info['type'] == 'material':
      self.world[target] = name
    elif info['type'] == 'object':
      cls = {
          'fence': Fence,
          'plant': Plant,
      }[name]
      self.world.add(cls(self.world, target, self))
    self.achievements[f'place_{name}'] += 1
    self.event = f"I used {amount} {info['uses']} to successfully place {name} in front of me."
    # self.event = f"I successfully placed {name} in front of me. "
    # print("place_material")
    self.task_completed = 'success'
    self.action_result = 'I executed successfully. '

  def _make(self, name):
    nearby, _ = self.world.nearby(self.pos, 1)
    info = constants.make[name]
    self.event = f"I failed to make {name}. "
    self.action_result = 'I failed to execute. '
    if not all(util in nearby for util in info['nearby']):
      self.task_completed = 'failed'
      return
    if any(self.inventory[k] < v for k, v in info['uses'].items()):
      self.task_completed = 'failed'
      return
    for item, amount in info['uses'].items():
      self.inventory[item] -= amount
    self.inventory[name] += info['gives']
    self.achievements[f'make_{name}'] += 1
    self.event = f"I made {name}. "
    # print("make_material")
    self.task_completed = 'success'
    self.action_result = 'I executed successfully. '


class Cow(Object):

  def __init__(self, world, pos, player, eatable_flag = True):
    super().__init__(world, pos)


    
    self.npc(player)
    self.health = 3
    self.leaves = 'beef'
  
  # @property
  # def left(self):
  #   return self.health <= 0


  @property
  def texture(self):
      return 'cow'
  
  @property
  def walkable(self):
    walkable = constants.walkable 
    # player_walkable = []
    # for item in constants.walkable_effect:
    #   if constants.walkable_effect[item]['walkable']:
    #     player_walkable.append(item)
    walkable.append(constants.name2name[constants.terrain_neighbour['tree']])
    return walkable


  # def default(self):
  #   self.inc_food_func = 1
  #   self.inc_thirst_func = 0
  #   self.closable_health_damage_func = -1
  #   self.eat_health_damage_func = 0
  #   self.arrow_damage_func = -1
  #   self.eatable_flag = True
  #   self.defeatable_flag = False
  #   self.attackable_flag = False
  #   self.closable_flag = False
  #   self.arrowable_flag = False
  # def update(self):
  #   if self.health <= 0:
  #     self.world.remove(self)

  #   self.arrowable()
  #   self.closable()
  #   self.attackable()
    
    # if self.random.uniform() < 0.5:
    #   direction = self.random_dir()
    #   self.move(direction)
    
  

class Zombie(Object):

  def __init__(self, world, pos, player):
    super().__init__(world, pos)

    


    self.npc(player=player)

    self.health = 5
    self.cooldown = 0
    self.leaves = 'rotten_flesh'

  @property
  def texture(self):
    return 'zombie'

  # def default(self):
  #   self.inc_food_func = 1
  #   self.inc_thirst_func = 0
  #   self.closable_health_damage_func = -1
  #   self.eat_health_damage_func = 0
  #   self.arrow_damage_func = -1
  #   self.eatable_flag = False
  #   self.defeatable_flag = True
  #   self.attackable_flag = True
  #   self.closable_flag = True
  #   self.arrowable_flag = False
    # self.unclosable_flag = False
  # def update(self):
  #   if self.health <= 0:
  #     self.world.remove(self)
    
    
  #   self.arrowable()
  #   # dist = self.distance(self.player)
  #   # if dist <= 8 and self.random.uniform() < 0.9:
  #   #   self.move(self.toward(self.player, self.random.uniform() < 0.8))
  #   # else:
  #   #   self.move(self.random_dir())
  #   self.closable()
  #   # dist = self.distance(self.player)
  #   # if dist <= 1:
  #   #   if self.cooldown:
  #   #     self.cooldown -= 1
  #   #   else:
  #   #     if self.player.sleeping:
  #   #       damage = 7
  #   #     else:
  #   #       damage = 2
  #   #     self.player.health -= self.player._change_life_stats['zombie_damage'] * damage
  #   #     self.cooldown = 5
  #   self.attackable()


class Skeleton(Object):

  def __init__(self, world, pos, player, arrowable_flag=True, defeatable_flag=True):
    super().__init__(world, pos)


    

    self.npc(player=player)
    self.health = 3
    self.reload = 0
    self.leaves = 'bone'
    

  @property
  def texture(self):
    return 'skeleton'

  @property
  def walkable(self):
    walkable = constants.walkable  
    walkable.append(constants.name2name['path'])
    return walkable
  # def default(self):
  #   self.inc_food_func = 1
  #   self.inc_thirst_func = 0
  #   self.closable_health_damage_func = -1
  #   self.eat_health_damage_func = 0
  #   self.arrow_damage_func = -1
  #   self.eatable_flag = False
  #   self.defeatable_flag = True
  #   self.attackable_flag = False
  #   self.closable_flag = False
  #   self.arrowable_flag = True
  
    # self.unclosable_flag = False
  # def update(self):
  #   if self.health <= 0:
  #     self.world.remove(self)
    
    
  #   self.arrowable()
  #   self.closable()
  #   self.attackable()

    

    # self.reload = max(0, self.reload - 1)
    # dist = self.distance(self.player.pos)
    # if dist <= 3:
    #   moved = self.move(-self.toward(self.player, self.random.uniform() < 0.6))
    #   if moved:
    #     return
    # if dist <= 5 and self.random.uniform() < 0.5:
    #   self._shoot(self.toward(self.player))
    # elif dist <= 8 and self.random.uniform() < 0.3:
    #   self.move(self.toward(self.player, self.random.uniform() < 0.6))
    # elif self.random.uniform() < 0.2:
    #   self.move(self.random_dir())

  # def _shoot(self, direction):
  #   if self.reload > 0:
  #     return
  #   if direction[0] == 0 and direction[1] == 0:
  #     return
  #   pos = self.pos + direction
  #   if self.is_free(pos, Arrow.walkable):
  #     self.world.add(Arrow(self.world, pos, direction))
  #     self.reload = 4


class Arrow(Object):

  def __init__(self, world, pos, facing, arrow_damage_func):
    super().__init__(world, pos)
    self.facing = facing
    self.arrow_damage_func = arrow_damage_func

  @property
  def texture(self):
    return {
        (-1, 0): 'arrow-left',
        (+1, 0): 'arrow-right',
        (0, -1): 'arrow-up',
        (0, +1): 'arrow-down',
    }[tuple(self.facing)]

  @engine.staticproperty
  def walkable():
    return constants.walkable + ['water', 'lava']

  def update(self):
    target = self.pos + self.facing
    material, obj = self.world[target]
    if obj:
      if isinstance(obj, Player):
        obj.health += self.arrow_damage_func * 2
      else:
        obj.health -= 2
      self.world.remove(self)
    elif material not in self.walkable:
      self.world.remove(self)
      if material in ['table', 'furnace']:
        self.world[target] = 'path'
    else:
      self.move(self.facing)

class Plant(Object):

  def __init__(self, world, pos, player):
    super().__init__(world, pos)
    self.npc(player=player)
    self.health = 1
    self.grown = 0

  @property
  def texture(self):
    if self.ripe:
      return 'plant-ripe'
    else:
      return 'plant'

  @property
  def ripe(self):
    return self.grown > 30
  

  def update(self):
    self.grown += 1
    objs = [self.world[self.pos + dir_][1] for dir_ in self.all_dirs]
    if any(isinstance(obj, (Zombie, Skeleton, Cow)) for obj in objs):
      self.health -= 1
    if self.health <= 0:
      self.world.remove(self)
    else:
      # 成熟的食人花
      if self.ripe:
        self.arrowable()
        self.closable()
        if self.attackable_flag:
          dist = self.distance(self.player)
          if dist <= 1:
            if self.cooldown:
              self.cooldown -= 1
            else:
                damage = 1
                self.player.health += self.closable_health_damage_func * damage
                self.cooldown = 5


  # def default(self):

  #   self.inc_food_func = 1
  #   self.inc_thirst_func = 0
  #   self.closable_health_damage_func = 0
  #   self.eat_health_damage_func = 0
  #   self.arrow_damage_func = 0
  #   self.eatable_flag = True
  #   self.defeatable_flag = False
  #   self.attackable_flag = False
  #   self.closable_flag = False
  #   self.arrowable_flag = False

    # self.inc_food_func = 1
    # self.inc_thirst_func = 0
    # self.arrow_damage_func = -1
    # self.eatable_flag = True
    # self.defeatable_flag = False
    # self.attackable_flag = False
    # self.closable_flag = False
    # self.arrowable_flag = False
  


class Fence(Object):

  def __init__(self, world, pos):
    super().__init__(world, pos)

  @property
  def texture(self):
    return 'fence'

  def update(self):
    pass


# class Beef(Object):

#   def __init__(self, world, pos, player, inc_food_func=1):
#     super().__init__(world, pos)
#     self.health = 0
#     self.npc(player=player)
#     # self.player = player
#   # @property
#   # def left(self):
#   #   return self.health <= 0

#   @property
#   def texture(self):
#       return 'beef'



# class Bone(Object):

#   def __init__(self, world, pos, player):
#     super().__init__(world, pos)
#     self.health = 0
#     self.npc(player=player)

#   @property
#   def texture(self):
#       return 'bone'
  
#   def update(self):
#     pass
#   # def update(self):
#   #   if self.health <= 0:
#   #     self.world.remove(self)

#   #   self.arrowable()
#   #   self.closable()
#   #   self.attackable()
    
#     # if self.random.uniform() < 0.5:
#     #   direction = self.random_dir()
#     #   self.move(direction)
    

# class Rotten_Flesh(Object):

#   def __init__(self, world, pos, player):
#     super().__init__(world, pos)
#     self.health = 0
#     self.npc(player=player)

#   @property
#   def texture(self):
#       return 'rotten_flesh'
  
#   def update(self):
#     pass
#   # def update(self):
#   #   if self.health <= 0:
#   #     self.world.remove(self)

#   #   self.arrowable()
#   #   self.closable()
#   #   self.attackable()
    
#     # if self.random.uniform() < 0.5:
#     #   direction = self.random_dir()
#     #   self.move(direction)
    


