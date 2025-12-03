import numpy as np
from mars.api.utils import *
import random
import itertools

class envWrapper:
    def __init__(self, env) -> None:
        
        self._env = env
        self.id_to_item = [0]*(len(env._world._mat_ids) + len(env._sem_view._obj_ids))
        for name, ind in itertools.chain(env._world._mat_ids.items(), env._sem_view._obj_ids.items()):
            name = str(name)[str(name).find('objects.')+len('objects.'):-2].lower() if 'objects.' in str(name) else str(name)
            self.id_to_item[ind] = name
        self.player_idx = self.id_to_item.index('player')

    def noop(self):
        self._env.step(ACTIONS_NAME.index('noop'))

    def findBlock(self, name):
        ''' 
        how many blocks in the player's field of view
        '''
        fov = self.get_fov()
        block = OBJ2ID[name]
        
        target_mask = fov == block
        
        amount = target_mask.sum()

        return amount

    def findNearstBlock(self, name):
        '''
        find the nearst block in the player's field of view
        '''
        info = self._env.info
        fov = self.get_fov()
        # semantic = info['semantic'][info['player_pos'][0]-info['view'][0]//2:info['player_pos'][0]+info['view'][0]//2+1, info['player_pos'][1]-info['view'][1]//2+1:info['player_pos'][1]+info['view'][1]//2]
        center = np.array([info['view'][0]//2,info['view'][1]//2-1])
        x = np.arange(fov.shape[1])
        y = np.arange(fov.shape[0])
        x1, y1 = np.meshgrid(x,y)
        loc = np.stack((y1, x1),axis=-1)
        manhattan_distances = np.absolute(center-loc).sum(axis=-1)


        fov = self.get_fov()
        
        # player_pos = self._env.info['player_pos']
        # global_view = self._env.info['semantic']
        if name not in OBJ2ID:
            return np.array([-1,-1])
        block = OBJ2ID[name]

        
        # Create a mask for the target value
        target_mask = fov == block

        if not target_mask.any():
            return np.array([-1,-1])

        

        # Apply the mask to the Manhattan distances, set non-targets to a high number
        valid_distances = np.where(target_mask, manhattan_distances, np.inf)
        
        # Find the position of the minimum distance where the target value is located
        min_idx = np.argmin(valid_distances)
        nearest_position_fov = np.unravel_index(min_idx, fov.shape)
        nearest_position = self._env.info['player_pos'] + (np.array(nearest_position_fov) - np.array(center))
        return nearest_position

    def GetToBlock(self, position, block_name):
        '''
        Not get into the block, but get directly adjacent to it.
        '''
        
        # ((-1, 0), (+1, 0), (0, -1), (0, +1))
        pos = self._env.info['player_pos'] # (4,3)
        # pos = (4, 3)
        # position = (8, 2)
        direction_list = []
        left_or_right = position[0] - pos[0]
        up_or_down = position[1] - pos[1]
        if left_or_right < 0:
            direction_list = ['move_left'] * abs(left_or_right)
        elif left_or_right > 0:
            direction_list = ['move_right'] * abs(left_or_right)

        if up_or_down < 0:
            direction_list += ['move_up'] * abs(up_or_down)
        elif up_or_down > 0:
            direction_list += ['move_down'] * abs(up_or_down)

        # make player view towards the goal
        if len(direction_list) <= 2:
            if not self.isFacing(self._env.info['player_pos'], self._env.info['player_facing'], block_name):
                if 'move_left' in direction_list or 'move_right' in direction_list:
                    
                    direction_list.append('move_left')
                    direction_list.append('move_right')
                else:
                    direction_list.append('move_up')
                    direction_list.append('move_down')
        
        if len(direction_list) > 2:
            while True:
                random.shuffle(direction_list)
                if direction_list[-1] == direction_list[-2]:
                    break
        # 对于env处理
        player_pos = self._env.info['player_pos']
        
        for dir in direction_list[:-1]:
            # self._env.step(dir)

        # if self.isSurrounded(player_pos, position):
        #     print("You successfully get to the block")
        #     return True
        # else:
        #     print("You failed to get to the block")
        #     return False
            action = ACTIONS_NAME.index(dir)
            obs, reward, done, info  = self._env.step(action)
            if np.array_equal(player_pos, info['player_pos']):
                barrier_pos = player_pos + MOVE_LIST[dir]
                barrier = info['semantic'][barrier_pos[0], barrier_pos[1]]
                # You meet a xx cannot walkable
                print(f"You cannot reach the block because there is a {ID2OBJ[barrier]} obstacle in the way.")

                return False
            player_pos = info['player_pos']
        return True
    
    
    def getToPos(self, tgt_pos):
        '''
        Not get into the block, but get directly adjacent to it.
        '''
        # if not self._env._world[tgt_pos][1]:
        #     print("The position is not walkable.")
        #     return False
        # assert self._env._world[tgt_pos][1], "The position is not walkable."
        # ((-1, 0), (+1, 0), (0, -1), (0, +1))
        pos = self._env.info['player_pos'] # (4,3)
        # pos = (4, 3)
        # position = (8, 2)
        direction_list = []
        left_or_right = tgt_pos[0] - pos[0]
        up_or_down = tgt_pos[1] - pos[1]
        if left_or_right < 0:
            direction_list = ['move_left'] * abs(left_or_right)
        elif left_or_right > 0:
            direction_list = ['move_right'] * abs(left_or_right)

        if up_or_down < 0:
            direction_list += ['move_up'] * abs(up_or_down)
        elif up_or_down > 0:
            direction_list += ['move_down'] * abs(up_or_down)

        # make player view towards the goal
        if len(direction_list) <= 2:
            # if not self.isFacing(self._env.info['player_pos'], self._env.info['player_facing'], block_name):
            if not np.array_equal(self._env.info['player_pos'] + self._env.info['player_facing'] ,tgt_pos):
                if 'move_left' in direction_list or 'move_right' in direction_list:
                    
                    direction_list.append('move_left')
                    direction_list.append('move_right')
                else:
                    direction_list.append('move_up')
                    direction_list.append('move_down')
        
        if len(direction_list) > 2:
            while True:
                random.shuffle(direction_list)
                if direction_list[-1] == direction_list[-2]:
                    break
        # 对于env处理
        player_pos = self._env.info['player_pos']
        
        for dir in direction_list[:-1]:
            action = ACTIONS_NAME.index(dir)
            obs, reward, done, info  = self._env.step(action)
            if np.array_equal(player_pos, info['player_pos']):
                barrier_pos = player_pos + MOVE_LIST[dir]
                barrier = info['semantic'][barrier_pos[0], barrier_pos[1]]
                # You meet a xx cannot walkable
                print(f"You cannot reach the block because there is a {ID2OBJ[barrier]} obstacle in the way.")

                return False
            player_pos = info['player_pos']
        return True

    def backToPos(self, tgt_pos):
        # if not self._env._world[tgt_pos][1]:
        #     print("The position is not walkable.")
        #     return False
        info = self._env.info
        player_pos = info['player_pos'] # (4,3)
        direction_list = []
        left_or_right = tgt_pos[0] - player_pos[0]
        up_or_down = tgt_pos[1] - player_pos[1]
        if left_or_right < 0:
            direction_list = ['move_left'] * abs(left_or_right)
        elif left_or_right > 0:
            direction_list = ['move_right'] * abs(left_or_right)

        if up_or_down < 0:
            direction_list += ['move_up'] * abs(up_or_down)
        elif up_or_down > 0:
            direction_list += ['move_down'] * abs(up_or_down)

        
        for dir in direction_list: 
            action = ACTIONS_NAME.index(dir)
            barrier_pos = player_pos + MOVE_LIST[dir]
            barrier_id = info['semantic'][barrier_pos[0],barrier_pos[1]]
            obs, reward, done, info  = self._env.step(action)
            if np.array_equal(player_pos, info['player_pos']):
                # obstacle in the way and by pass

                # barrier_pos = player_pos + MOVE_LIST[dir]
                # barrier = info['semantic'][barrier_pos[0], barrier_pos[1]]
                # You meet a xx cannot walkable
                print(f"You cannot reach the block because there is a {ID2OBJ[barrier_id]} obstacle in the way.")

                return False
            player_pos = info['player_pos']
        return True
        
    def followToBlock(self, block_name, all_steps = 10):
        step = 0
        dir = random.choice(list(DIRECTION_LIST.keys()))
        self.exploreUntil(None, dir, 1)
        while step < all_steps and not self.isFacing(self._env.info['player_pos'], self._env.info['player_facing'], block_name):
            block_pos = self.findNearstBlock(block_name)
            if block_pos.sum() < 0:
                self._env.info['task_complete'] = 'failed'
                return False
            pos = self._env.info['player_pos'] 
            left_or_right = block_pos[0] - pos[0]
            up_or_down = block_pos[1] - pos[1]

            if left_or_right == 0 or up_or_down == 0:
                if left_or_right < 0:
                    dir = 'move_left'
                elif left_or_right > 0:
                    dir = 'move_right'
                elif up_or_down < 0:
                    dir = 'move_up'
                elif up_or_down > 0:
                    dir = 'move_down'
            else:
                if random.uniform(0,1) < 0.5:
                    if left_or_right < 0:
                        dir = 'move_left'
                    else:
                        dir = 'move_right'
                else:
                    if up_or_down < 0:
                        dir = 'move_up'
                    else:
                        dir = 'move_down'

            self._env.step(ACTIONS_NAME.index(dir))
            step += 1
        if not self.isFacing(self._env.info['player_pos'], self._env.info['player_facing'], block_name):
            self._env.info['task_complete'] = 'failed'
            return False
        else:
            # self._env.info['task_complete'] = 'success'
            return True

        # self.GetToBlock(block_pos)

        


    
    def isFacing(self, obj1_pos, facing, obj2_name ):

        target = obj1_pos + facing

        if ID2OBJ[self._env.info['semantic'][target[0],target[1]]] == obj2_name :
            return True
        else:
            return False

    
    def interact(self):
        self._env.info['task_complete'] = 'failed'
        
        self._env.step(ACTIONS_NAME.index('do'))

        if self._env.info['task_complete'] == 'success':
            return True
        else:
            return False
        
    def collect(self, name):
        '''
        interact with the block
        '''
        # if name == 'wood':

        #     assert self.isFacing(self._env.info['player_pos'], self._env.info['player_facing'], 'tree')

        # interact with this block
        # pre_num = self.get_inventory(name)
        self._env.info['task_complete'] = 'failed'
        self._env.step(ACTIONS_NAME.index('do'))
        # post_num = self.get_inventory(name)
        # # if post_num > pre_num:
        #     self._env.task_completed == 'success'
        #     return True
        
        # else:
        #     return False

    def attack(self, block_name):
        
        # assert self.isFacing(self._env.info['player_pos'], self._env.info['player_facing'], block_name)
        
        
        self._env.info['task_complete'] = 'failed'
        
        trials = 0
        while block_name not in self.get_fov_types():
            dir = random.choice(list(DIRECTION_LIST.keys()))
            self.exploreUntil(block_name, dir, 5)
            trials += 1
            if trials >= 3:
                return False
            
        for i in range(10):
        
            if self.followToBlock(block_name):
                self._env.step(ACTIONS_NAME.index('do'))
                if self._env.info['task_complete'] == 'success':
                    return True
            

        # while i < 5:
        #     if block_name not in self.get_fov_types():
        #         dir = random.choice(list(DIRECTION_LIST.keys()))
        #         self.exploreUntil(block_name, dir, 5)
        #         trials += 1
            
        #     if self.followToBlock(block_name):
        #         self._env.step(ACTIONS_NAME.index('do'))
        #         i = i + 1
        #         if self._env.info['task_complete'] == 'success':
        #             return True
        #     if trials >= 3:
        #         return False
            
            # else:
            #     return False

            # if not self.followToBlock(block_name):
            #     dir = random.choice(list(DIRECTION_LIST.keys()))
            #     self.exploreUntil(block_name, dir, 5)
            # self.followToBlock(block_name)
            # self._env.step(ACTIONS_NAME.index('do'))
            # if self._env.info['task_complete'] == 'success':
            #     return True

        # if self._env.task_completed == 'success':
        #     return True
        # else:
        #     return False
    
    def exploreUntil(self, block_name, direction, all_steps=10):
        # random walk to make required block in self view, or excceed timeout 则 error （超过100步？）
        step = 0
        # if block_name in self.get_fov_types():
        #     # self._env.info['task_complete'] = 'success'
        #     return True
        choice_dir = list(DIRECTION_LIST.keys())
        if not direction:
            direction = random.choice(choice_dir)
        
        move_dir = DIRECTION_LIST[direction]
        flag = True
        
        player_pos = self._env.info['player_pos']
        while step < all_steps:
            random_dir = random.choice(move_dir)
            # random_num = random.uniform(0,1)
            # if random_num < 0.7:
            #     random_dir = direction
            # else:
            #     random_dir = random.choice(choice_dir)
            

            obs, reward, done, info = self._env.step(ACTIONS_NAME.index(random_dir))
            if np.array_equal(player_pos, info['player_pos']):
                # barrier_pos = player_pos + MOVE_LIST[dir]
                # barrier = info['semantic'][barrier_pos[1], barrier_pos[0]]
                # # You meet a xx cannot walkable
                # print(f"You cannot reach the block because there is a {ID2OBJ[barrier]} obstacle in the way.")
                flag = False
                break
            player_pos = info['player_pos']
            view_type = self.get_fov_types()
            
            if block_name and block_name in view_type:
                flag = True
                break
            step += 1
        
        if flag:
            # self._env.info['task_complete'] = 'success'
            return True
        else:
            self._env.info['task_complete'] = 'failed'
            return False
        # if not self.isFacing(self._env.info['player_pos'], self._env.info['player_facing'], block_name):
        #     self._env.info['task_complete'] = 'failed'
        # else:
        #     self._env.info['task_complete'] = 'success'

    def get_fov(self):
        '''
        Get the player's field of view.
        '''
        pos = self._env.info['player_pos']
        obs = self._env.info['semantic']

        fov_size = np.array([9, 7])
        top_left = np.maximum(pos - fov_size // 2, 0)
        bottom_right = np.minimum(pos + fov_size // 2 + 1, obs.shape)
        fov = obs[top_left[0]:bottom_right[0], top_left[1]:bottom_right[1]]
        pad_top = top_left[0] - pos[0] + fov_size[0] // 2
        pad_bottom = pos[0] + fov_size[0] // 2 + 1 - bottom_right[0]
        pad_left = top_left[1] - pos[1] + fov_size[1] // 2
        pad_right = pos[1] + fov_size[1] // 2 + 1 - bottom_right[1]
        fov = np.pad(fov, ((pad_top, pad_bottom), (pad_left, pad_right)), mode='constant', constant_values=0)
        return fov
    
    def get_fov_types(self):
        '''
        get the object type in the player's field of view
        '''
        fov = self.get_fov()
        types = np.unique(fov)
        type_strings = [self.id_to_item[t] for t in types]
        
        return type_strings
    
    def get_inventory(self, name):
        inventory = self._env.info['inventory']
        return inventory[name]

    def placeBlock(self, name):
        '''
        place a block
        '''
        self._env.info['task_complete'] = 'failed'
        if name == 'sapling':
            name = 'plant'
        if 'table' in name or 'furnace' in name:
            trials = 0
            while trials < 3:
                action = f"place_{name}"
                self._env.step(ACTIONS_NAME.index(action))
                if self._env.info['task_complete'] != 'success':
                    dir = random.choice(list(DIRECTION_LIST.keys()))
                    self.exploreUntil(None, dir, 3)
                    trials += 1
                else:
                    return True
        else:

            action = f"place_{name}"
            self._env.step(ACTIONS_NAME.index(action))
        
    def sleep(self):
        _, _, _, info = self._env.step(ACTIONS_NAME.index('sleep'))
        while info['sleeping']:
            _, _, _, info = self._env.step(ACTIONS_NAME.index('noop'))
        

    
    def craft(self, name):
        self._env.info['task_complete'] = 'failed'
        action = f"make_{name}"
        self._env.step(ACTIONS_NAME.index(action))

    # describe the observation 
    def isSurrounded(self, player_pos, block_pos):
        '''
        check if the player is surrounded by the block
        '''
        for dir in MOVE_LIST.values():
            if np.array_equal(player_pos + dir, block_pos):
                return True
        return False
    def describe_inventory(self):
        info = self._env.info
        result = ""
        
        status_str = "Your status:\n{}".format("\n".join(["- {}: {}/9".format(v, info['inventory'][v]) for v in VITALS]))
        result += status_str + "\n\n"
        
        inventory_str = "\n".join(["- {}: {}".format(i, num) for i,num in info['inventory'].items() if i not in VITALS and num!=0])
        inventory_str = "Your inventory:\n{}".format(inventory_str) if inventory_str else "You have nothing in your inventory."
        result += inventory_str #+ "\n\n"
        
        return result

    def describe_loc(self, ref, P):
        desc = []
        if ref[1] > P[1]:
            desc.append("north")
        elif ref[1] < P[1]:
            desc.append("south")
        if ref[0] > P[0]:
            desc.append("west")
        elif ref[0] < P[0]:
            desc.append("east")

        return "-".join(desc)

    def describe_env(self):
        info = self._env.info
        assert(info['semantic'][info['player_pos'][0],info['player_pos'][1]] == self.player_idx)
        semantic = info['semantic'][info['player_pos'][0]-info['view'][0]//2:info['player_pos'][0]+info['view'][0]//2+1, info['player_pos'][1]-info['view'][1]//2+1:info['player_pos'][1]+info['view'][1]//2]
        center = np.array([info['view'][0]//2,info['view'][1]//2-1])
        result = "You see:\n"
        x = np.arange(semantic.shape[1])
        y = np.arange(semantic.shape[0])
        x1, y1 = np.meshgrid(x,y)
        loc = np.stack((y1, x1),axis=-1)
        dist = np.absolute(center-loc).sum(axis=-1)
        obj_info_list = []
        
        all_dir = list(MOVE_LIST.values())
        facing = info['player_facing']
        result += "Nearby Blocks: \n"
        record_blocks = set()
        for dir in all_dir:
            target = (center[0] + dir[0], center[1] + dir[1])
            target = self.id_to_item[semantic[target]]
            record_blocks.add(target)
            if dir == facing:
                obs = "- {} 1 step at your {} (front).\n".format(target, self.describe_loc(np.array([0,0]),facing))
            else:
                obs = "- {} 1 step at your {}.\n".format(target, self.describe_loc(np.array([0,0]),dir))
            result += obs
        result += '\n'
        
        target = (center[0] + facing[0], center[1] + facing[1])
        target = self.id_to_item[semantic[target]]
        
        result += 'Other Blocks: \n'

        for idx in np.unique(semantic):
            if idx==self.player_idx:
                continue
            if self.id_to_item[idx] in record_blocks:
                continue
            smallest = np.unravel_index(np.argmin(np.where(semantic==idx, dist, np.inf)), semantic.shape)
            obj_info_list.append((self.id_to_item[idx], dist[smallest], self.describe_loc(np.array([0,0]), smallest-center)))

        if len(obj_info_list)>0:
            # status_str = "You see:\n{}".format("\n".join(["- nearest {} {} steps to your {}".format(name, dist, loc) for name, dist, loc in obj_info_list]))

            status_str = "{}".format("\n".join(["- nearest {} {} steps to your {}".format(name, dist, loc) for name, dist, loc in obj_info_list]))
        else:
            # status_str = "You see nothing away from you."
            status_str = ""
        result += status_str + "\n\n"
        # result += obs.strip()
        
        return result
    
    def describe_status(self):
        info = self._env.info
        if info['sleeping']:
            return "You are sleeping, and will not be able take actions until energy is full.\n\n"
        elif info['dead']:
            return "You died.\n\n"
        else:
            return ""
    
    def describe_frame(self):
        try:
            result = ""
            
            # if action is not None:
            #     result+=describe_act(info)
            result+=self.describe_status()
            # result+="\n\n"
            result+=self.describe_env()
            # result+="\n\n"
            result+=self.describe_inventory()
            
            return result
        except:
            return "Error, you are out of the map."

    def describe_action_result(self):
        info = self._env.info
        if info['task_complete'] == 'success':
            return "You successfully complete the action."
        elif info['task_complete'] == 'failed':
            return "You failed to complete the action."
        else:
            return ""


