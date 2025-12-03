
from mars.api.envWrapper import *
import random
# import crafter.constants as constants
class AgentController:
    def __init__(self, env):
        self._envwapper = envWrapper(env)
    
    def reset(self):
        self._see_table = False
        self._see_furnace = False
        self.table_pos = np.array([-1, -1])
        self.furnace_pos = np.array([-1, -1])
        
        if 'table' in self._envwapper.get_fov_types():
            self._see_table = True
            self.table_pos = self._envwapper.findNearstBlock('table')
        if 'furnace' in self._envwapper.get_fov_types():
            self._see_furnace = True
            self.furnace_pos = self._envwapper.findNearstBlock('furnace')
        
    def noop(self):
        self._envwapper.noop()
    
    # go to the nearestblock
    def getToBlock(self, block_name):
        return self.followMob(block_name)

    def mine(self, block_name):
        assert block_name in BLOCK_NAME, "The block is not valid."
        self._envwapper.interact()

    def mine(self, block_name, amount):
        have_num = 0
        explore_times = 0
        while have_num < amount:
            self._envwapper._env.info['task_complete'] = 'failed'
            if block_name not in self._envwapper.get_fov_types():
                random_dir = random.choice(list(DIRECTION_LIST.keys()))
                self.exploreUntil(block_name, random_dir, 10)
                explore_times += 1

            
            if self.getToBlock(block_name):
                if not self._envwapper.interact():
                    return False
                else:
                    have_num += 1
                    continue
            else:
                random_dir = random.choice(list(DIRECTION_LIST.keys()))
                self.exploreDirection(random_dir, 5)
                explore_times += 1

                if self.getToBlock(block_name):
                    if not self._envwapper.interact():
                        return False
                    else:
                        have_num += 1
                        continue
           
            if explore_times >= 3:
                print(f"Could not find {block_name}")
                return False

            # random_dir = random.choice(list(DIRECTION_LIST.keys()))
            # if self.exploreUntil(block_name, random_dir, 10):

            #     if self.getToBlock(block_name):
            #         if not self._envwapper.interact():
            #             return False
            #         else:
            #             have_num += 1
            #     else:
            #         random_dir = random.choice(list(DIRECTION_LIST.keys()))
            #         self.exploreDirection(None, random_dir, 10)
            # else:
            #     explore_times += 1
            # if explore_times > 3:
            #     print(f"Could not find {block_name}")
            #     return False
            
    
    def attack(self, creature, amount):
        assert creature in ['zombie', 'cow', 'skeleton', 'plant'], "The creature is not valid."
        for i in range(amount):
            self._envwapper.attack(creature)
            if self._envwapper._env.info['task_complete'] == "failed":
                return False
 
    def eat(self, creature):
        assert creature in ['zombie', 'cow', 'skeleton', 'plant'], "The creature is not valid."
        self._envwapper.interact()

    def collect(self):
        self._envwapper.interact()
    def attackMob(self):
        self._envwapper.interact()
    def drink(self):
        self._envwapper.interact()

    def interactWithBlock(self):
        self._envwapper.interact()
    # def mineBlock(self, block_name):
    #     self._envwapper.collect(block_name)

    # mine block in the world
    def mineBlock_temp(self, block_name, amount):
        # first find the nearst block
        find_amount = self._envwapper.findBlock(block_name)
        
        if find_amount < amount:
            if find_amount == 0:
                print(f"Could not find {block_name}")
                return False
            else:
                print(f"You found {find_amount} {block_name}, but unfortunately you did not find enough {block_name}.")
                return False
        
        # collect_name = constants.collect[block_name]['receive'].keys()

        # origin_amount = self._envwapper.get_inventory(block_name)
        for i in range(amount):
            position = self._envwapper.findNearstBlock(block_name)
            if self._envwapper.GetToBlock(position):
                
                if not self._envwapper.collect(position):
                    return False

            else:
                print("Could not get to the block")
                return False
            
        return True
            
        


    def attackMob(self, block_name):
        # player look at the Mob (zombie / cow / sketelon)
        return self._envwapper.attack(block_name)

    def followMob(self, block_name):
        return self._envwapper.followToBlock(block_name)

    
    def exploreUntil(self, block_name, direction, all_steps=10):
        assert block_name in BLOCK_NAME, "The block is not valid."
        # random walk to make required block in self view, or excceed timeout 则 error 
        return self._envwapper.exploreUntil(block_name, direction, all_steps)
        
    def exploreDirection(self, direction, steps):
        self._envwapper.exploreUntil(None, direction, steps)    

    def sleep(self):
        self._envwapper.sleep()

    def wake_up(self):
        self._envwapper.wakeUp()
    
    def place(self, block):
        assert block in ['stone', 'table', 'furnace', 'sapling'], "The block is not valid."
        if self._see_table and 'furnace' in block :
            # if "furace" in block:
                # if need place furnace, walk to the table
            # if not self._envwapper.backToPos(self._player_pos):
            #     return False
            # find the table block
            pos = self._envwapper._env.info['player_pos']
            table_pos = self.table_pos

            if self._envwapper.isSurrounded(pos, table_pos):
                self._envwapper.placeBlock('furnace')
                if self._envwapper._env.info['task_complete'] == 'success':
                    self._see_furnace = True
                    self.furnace_pos = self._envwapper.findNearstBlock('furnace')
                return True
            # the surrounding blocks of the table
            for candidate_pos in MOVE_LIST:
                furnace_pos = (table_pos[0]+candidate_pos[0], table_pos[1]+candidate_pos[1])
                if self._envwapper.getToPos(furnace_pos):
                    self._envwapper.placeBlock('furnace')
                    if self._envwapper._env.info['task_complete'] == 'success':
                        self._see_furnace = True
                        self.furnace_pos = self._envwapper.findNearstBlock('furnace')
                    return True

        else:
            self._envwapper.placeBlock(block)
            if block == 'table' and self._envwapper._env.info['task_complete'] == 'success':
                self._see_table = True
                self.table_pos = self._envwapper.findNearstBlock('table')
            if block == 'furnace' and self._envwapper._env.info['task_complete'] == 'success':
                self._see_furnace = True
                self.furnace_pos = self._envwapper.findNearstBlock('furnace')

    def craft(self, tool):
        tool = tool.replace(' ', '_')
        self._envwapper._env.info['task_complete'] = 'failed'
        assert tool in ['wood_pickaxe', 'stone_pickaxe', 'iron_pickaxe', 'wood_sword', 'stone_sword', 'iron_sword'], "The tool is not valid."
        if self._see_table and not self._see_furnace:
            table_pos = self.table_pos
            pos = self._envwapper._env.info['player_pos']
            if self._envwapper.isSurrounded(pos, table_pos):
                self._envwapper.craft(tool)
                return True
            for candidate_pos in list(MOVE_LIST.values()):
                tgt_pos = (table_pos[0]+candidate_pos[0], table_pos[1]+candidate_pos[1])
                if self._envwapper.backToPos(tgt_pos):
                    self._envwapper.craft(tool)
                    return True
        elif self._see_table and self._see_furnace:
            # if not self._envwapper.backToPos(self._player_pos):
            #     return False
            table_pos = self.table_pos
            furnace_pos = self.furnace_pos
            pos = self._envwapper._env.info['player_pos']
            if self._envwapper.isSurrounded(pos, table_pos) and self._envwapper.isSurrounded(pos, furnace_pos):
                self._envwapper.craft(tool)
                return True
            
            dir_array = np.array(list(MOVE_LIST.values()))
            close_table = np.array(table_pos) + dir_array
            close_table_set = set([tuple(x) for x in close_table])
            close_furnace = np.array(furnace_pos) + dir_array
            close_furnace_set = set([tuple(x) for x in close_furnace])

            # intersection of the surrounding blocks of the table and the furnace
            intersection = close_table_set & close_furnace_set

            for intersection in intersection:
                if self._envwapper.backToPos(intersection):
                    self._envwapper.craft(tool)
                    return True
                
        elif self._see_furnace and not self._see_table:
            
            furnace_pos = self.table_pos
            pos = self._envwapper._env.info['player_pos']
            if self._envwapper.isSurrounded(pos, furnace_pos):
                self._envwapper.craft(tool)
                return True
            for candidate_pos in list(MOVE_LIST.values()):
                tgt_pos = (furnace_pos[0]+candidate_pos[0], furnace_pos[1]+candidate_pos[1])
                if self._envwapper.backToPos(tgt_pos):
                    self._envwapper.craft(tool)
                    return True

        else:
            self._envwapper.craft(tool)


    def place_stone(self):
        self._envwapper.placeBlock('stone')

    def place_table(self):
        self._envwapper.placeBlock('crafting_table')

    def place_furnace(self):
        self._envwapper.placeBlock('furnace')
    
    def place_plant(self):
        self._envwapper.placeBlock('plant')
    
    def make_wood_pickaxe(self):
        self._envwapper.craft('wood_pickaxe')
    
    def make_stone_pickaxe(self):
        self._envwapper.craft('stone_pickaxe')
    
    def make_iron_pickaxe(self):
        self._envwapper.craft('iron_pickaxe')
    
    def make_wood_sword(self):
        self._envwapper.craft('wood_sword')
    
    def make_stone_sword(self):
        self._envwapper.craft('stone_sword')
    
    def make_iron_sword(self):
        self._envwapper.craft('iron_sword')