from graphviz import Digraph
import copy
import pathlib


# terr_items = {
#             'tree': 3,
#             'stone': 2738,
#             'coal': 207,
#             'iron': 85,
#             'diamond': 2,
#             'water': 3206,
#             'lava': 171,
#             'grass': 6492,
#             'sand': 809
#         }
inv_items = {
            'wood': 0,
            'stone': 0,
            'coal': 0,
            'iron': 0,
            'diamond': 0,
        }
MAX_INF = 100000
class Node:
    def __init__(self, name, content, require, leaves) -> None:
        self.name = name
        
        # self.source = source
        # self.sourceText = sourceText
        
        self.require = set(require)
        self.leaves = set(leaves)
        self.children = []
        self.parents = []
        self.visited = False
        self.contents = content
        self.parent_op = ''
        # self.cycle = None
        self.toroot = None
        self.root = None
        # self.terr_items = {item: 0 for item in }
        
    
    def add_child(self, child):
        self.children.append(child)
    
    def add_parent(self, parent):
        self.parents.append(parent)
    
    def set_visited(self):
        self.visited = True
    
    def clear_visited(self):
        self.visited = False


def is_ancestor(ancestor, descendant):
    visited = set()

    def dfs(node):
        visited.add(node)
        if node == ancestor:
            return True
        for parent in node.parents:
            if parent not in visited and dfs(parent):
                return True
        return False
    # if ancestor in descendant.parents:
    #     return False
    return dfs(descendant)
    
def vis_tree(nodes, save_graph=False, file_name=None):

    

    dot = Digraph(comment='Graph', format='png')

    # Add nodes
    for node_name, node_class in nodes.items():
        if node_class.root:
            label = f'{node_name}\n{node_class.parent_op}\n{node_class.toroot}\nROOT'
        else:
            label = f'{node_name}\n{node_class.parent_op}\n{node_class.toroot}'
        dot.node(node_name, label=label)

    # Add edges
    for node_name, node_class in nodes.items():
        # for child in node_class.children:
        #     # if not is_ancestor(child, node_class):
        #     dot.edge(node_name, child.name)
        for parent in node_class.parents:
            # if not is_ancestor(parent, node_class):
            dot.edge(parent.name, node_name)

    

    # save the tree as a png file
    if save_graph:
        if not file_name:
            file_name = f'./tech_tree.png'
        dot.render(file_name)


def conv_energy(env_rules):
    # 提取出所有关于health、food、thirst的值
    health_inc = list()
    health_dec = list()
    food_inc = list()
    food_dec = list()
    thirst_inc = list()
    thirst_dec = list()
    # flag_health = True
    for obj, value in env_rules.npc_objects.items():

        if value['closable_health_damage_func'] == 1 :
            health_inc.append(obj)
        
        if value['eat_health_damage_func'] == 1 :
            health_inc.append(obj)

        if value['arrow_damage_func'] == 1:
            health_inc.append(obj)
            
        if value['closable_health_damage_func'] == -1:
            health_dec.append(obj)

        if value['eat_health_damage_func'] == -1:
            health_dec.append(obj)

        if value['arrow_damage_func'] == -1:
            health_dec.append(obj)

        if value['inc_food_func'] == 1:
            food_inc.append(obj)
        
        if value['inc_food_func'] == -1:
            food_dec.append(obj)

        if value['inc_thirst_func'] == 1:
            thirst_inc.append(obj)
        
        if value['inc_thirst_func'] == -1:
            thirst_dec.append(obj)

    for obj, value in env_rules.drink.items():
        if value['inc_damage_func'] == 1:
            health_inc.append(obj)
        if value['inc_damage_func'] == -1:
            health_dec.append(obj)

        if value['inc_drink_func'] == 1:
            thirst_inc.append(obj)
        if value['inc_drink_func'] == -1:
            thirst_dec.append(obj)

        if value['inc_food_func'] == 1:
            food_inc.append(obj)
        if value['inc_food_func'] == -1:
            food_dec.append(obj)

    for obj, value in env_rules.walkable_effect.items():
        if value['walk_health'] == 1:
            health_inc.append(obj)
        if value['walk_health'] == -1:
            health_dec.append(obj)

    # if len(health_inc) > 0 and len(health_dec) > 0 and len(thirst_inc) > 0 and len(thirst_dec) > 0 and len(food_inc) > 0 and len(food_dec) > 0:
    if -4 < len(health_inc) - len(health_dec) <= 0 and len(thirst_inc) > 0 and len(food_inc) > 0:
    # if -2 <= len(health_inc) - len(health_dec) <= -2 and 0 < len(thirst_inc) - len(thirst_dec) <= 2 and 0 < len(food_inc) - len(food_dec) <= 3:
    
        print("Consistent with conservation of energy!!")
        return True
    else:
        print("NOT consistent with conservation of energy!!")
        return False
    
    
def check(env_rules, filename, terr_items=None):

    if not conv_energy(env_rules):
        return False
    
    achievements = dict()
    # for item in constants.achievements:
    #     value = '_'.join(item.split('_')[1:])
    #     if value not in achievements:
    #         achievements[value] = item
    

    nodes = dict()

    for item in env_rules.collect.items():
        key, value = item
        node_name = f"mine_{key}"
        for k, v in value['receive'].items():
            
            achieve_name = f"has_{k}"
            if achieve_name not in achievements:
                achievements[achieve_name] = list()
                
                
            achievements[achieve_name].append(node_name)
            


            
        require_raw = list(value['require'].keys())
        require = list()
        for req in require_raw:
            if req not in env_rules.terrain:
                require.append(f"has_{req}")

        # require.append(f"walk_to_{key}")

        # walk_req = f"walk_to_{key}"
        # nodes[walk_req] = Node(walk_req, walk_req, [], [])

        if key not in env_rules.terrain:
            require.append(f"has_{key}")
        
        if type(value['leaves']) != list:
            leaves_raw = [value['leaves']]
        else:
            leaves_raw = value['leaves']

        leaves = list()
        for leave in leaves_raw:
            if isinstance(leave, dict):
                leave = leave['material']
            if leave not in env_rules.terrain:
                # leaves.append(f"pick_{leave}")
                # leaves.append(f"collect_{leave}")
                achieve_name = f"nearby_{leave}"
                if achieve_name not in achievements:
                    achievements[achieve_name] = list()
                achievements[achieve_name].append(node_name)

        node = Node(node_name, item, require, leaves )
        nodes[node_name] = node
        # node_name = f"collect_{value['receive'].keys()}"
        # require = value['require']
        # require.update(key)
        # node = Node(node_name, value)
        # nodes[node_name] = node


    for item in env_rules.make.items():
        key, value = item
        node_name = f"make_{key}"

        achieve_name = f"has_{key}"
        if achieve_name not in achievements:
            achievements[achieve_name] = list()
        achievements[achieve_name].append(node_name)

        require_raw = list(value['uses'].keys())
        require = list()
        for req in require_raw:
            require.append(f"has_{req}")
        
        for nearby in value['nearby']:
            if nearby not in env_rules.terrain:
                require.append(f"nearby_{nearby}")
        
        node = Node(node_name, item, require, [])
        nodes[node_name] = node


    for item in env_rules.place.items():
        key, value = item
        node_name = f"place_{key}"

        achieve_name = f"nearby_{key}"
        if achieve_name not in achievements:
            achievements[achieve_name] = list()
            achievements[achieve_name].append(node_name)

        require_raw = list(value['uses'].keys())
        require = list()
        for req in require_raw:
            require.append(f"has_{req}")
        
        for where in value['where']:
            if where not in env_rules.terrain:
                require.append(f"nearby_{where}")



        node = Node(node_name,item,require, [])
        nodes[node_name] = node

    
    

    for achi_name, achi_req in achievements.items():
        if achi_name not in nodes:
            node = Node(achi_name, achi_req, [], [])
            nodes[achi_name] = node
            node.require = set(achi_req)
            if len(node.require) > 1:
                node.parent_op = 'OR'


    root_nodes = dict()

    for key, value in nodes.items():

        for require in value.require:
            if require not in nodes:
                nodes[key].parent_op = 'IMPOSSIBLE'
                return False
            else:
                nodes[key].add_parent(nodes[require])
                nodes[require].add_child(nodes[key])
                
        if len(value.require) == 0:
            nodes[key].root = True
            root_nodes[key] = nodes[key]
        
            

    vis_tree(nodes, True, filename / 'Tech_tree')



    valid = lambda x: env_rules.walkable_effect[x]['walkable'] and not env_rules.walkable_effect[x]['dieable'] and env_rules.walkable_effect[x]['walk_health'] > -1
    collectable = lambda x: x in env_rules.collect.keys()
    def process_walkable():
        stack = set()
        
        walk_req = {item: list() for item in env_rules.collect.keys()}

        def dfs_walk(item, req):
            
            if valid(item):
                if item in req:
                    req.remove(item)
                return True
            
            
            if item in stack:
                req.remove(item)
                req.append('ERROR')
                return False
            
            stack.add(item)
            # 不能被collect
            if item not in list(env_rules.collect.keys()):
                stack.remove(item)
                req.append('ERROR')
                return False
            lev_item = env_rules.collect[item]['leaves']['material']
            
            
            req.append(lev_item)
            # flag, req = dfs_walk(lev_item)
            if dfs_walk(lev_item, req):
                
                stack.remove(item)
                return True
            
            
            stack.remove(item)
            # req = ['ERROR']
            return False
        
        for item, value in walk_req.items():
            value.append(item)
            dfs_walk(item, value)
                # print(f"cannot walk to {item}!!")
                # return False, walk_req
        return walk_req

    walk_req = process_walkable()


    walk_req_link = []
    walkto_req_link = dict()
    
    for key, value in env_rules.terrain_neighbour.items():
        if key != 'player':
            # name = f"walk_{value}_to_{key}"
            # walk_req_link.append(name)

            if key != 'tree':

                walkto_req_link[key] = [env_rules.terrain_neighbour['player'], env_rules.terrain_neighbour['tree'], value, key]
            else:
                walkto_req_link[key] = [env_rules.terrain_neighbour['player'], value, key]
        
                # walk_req_link.append(f"walk_{env_rules.terrain_neighbour['tree']}_to_{value}")
            # else:
            #     walkto_req_link[key] = [env_rules.terrain_neighbour['tree'], value]
                # walk_req_link.append(f"walk_{env_rules.terrain_neighbour['player']}_to_{value}")

    # # walk_req_link.append(f"walk_{env_rules.terrain_neighbour['player']}_to_{value}")
    # walk_req_link.append(f"walk_{env_rules.terrain_neighbour['player']}_to_{value}")

    player_terr = env_rules.terrain_neighbour['player']
    if not valid(player_terr) :
        if not collectable(player_terr):
            print(f"Terrain has problem!!! You cannot walk to this place [{player_terr}]!!")
            return False
    
        if collectable(player_terr) and not nodes[f'mine_{player_terr}'].root:
            print(f"Terrain has problem!!! You cannot walk to this place [{player_terr}]!!")
            return False
    

    walk_req_link = set()
    walk_req_mine = dict()
    for key, key_walk_req in walkto_req_link.items():
        pre = 0
        post = 1
        while True:
            if post >= len(key_walk_req):
                break
            if post == len(key_walk_req) - 1 and collectable(key_walk_req[post]):
                if not valid(key_walk_req[pre]):
                    walk_req_link.add(f"walk_{key_walk_req[pre]}_to_{key_walk_req[post]}")
                break
            if not valid(key_walk_req[pre]) and not valid(key_walk_req[post]):
                walk_req_link.add(f"walk_{key_walk_req[pre]}_to_{key_walk_req[post]}")
                pre = post
                post = post + 1

            elif valid(key_walk_req[pre]) and not valid(key_walk_req[post]):
                pre = post
                post = post + 1
            elif not valid(key_walk_req[pre]):
                walk_req_link.add(f"walk_{key_walk_req[pre]}_to_{key_walk_req[post]}")
                post = post + 1

            else:
                pre = post + 1
                post = pre + 1
            
            
            
            # if post >= len(key_walk_req):
            #     break
            # if post == len(key_walk_req) - 1:
            #     if not valid(key_walk_req[pre]):
                    
            #         walk_req_link.add(f"walk_{key_walk_req[pre]}_to_{key_walk_req[post]}")
            #         if key_walk_req[pre] not in walk_req_mine:
            #             walk_req_mine[key_walk_req[pre]] = list()
            #         walk_req_mine[key_walk_req[pre]].append(key_walk_req[post])
                    
            # if valid(key_walk_req[pre]) and not valid(key_walk_req[post]):
                
            #     if not collectable(key_walk_req[post]):
            #         pre = pre
            #         post = post + 2
            #     else:
            #         pre = post
            #         post = post + 1
                
            # elif valid(key_walk_req[pre]) and valid(key_walk_req[post]):
            #     pre = pre + 2
            #     post = post + 2
            
            # elif not valid(key_walk_req[pre]) and valid(key_walk_req[post]):
            #     pre = pre
            #     post = post + 1
            
            # elif not valid(key_walk_req[pre]) and not valid(key_walk_req[post]):
            #     if not collectable(key_walk_req[post]):
            #         pre = post
            #         post = post + 2
            #     else:
            #         walk_req_link.add(f"walk_{key_walk_req[pre]}_to_{key_walk_req[post]}")
            #         if key_walk_req[pre] not in walk_req_mine:
            #             walk_req_mine[key_walk_req[pre]] = list()
            #         walk_req_mine[key_walk_req[pre]].append(key_walk_req[post])
            #         pre = post
            #         post = post + 1

   
    visited_pairs = set()
    for name in walk_req_link:
        
        in_item, to_item = name.split('_')[1], name.split('_')[-1] 
        if in_item == to_item:
            continue

        if not valid(in_item):
            # 如果可以挖走
            if collectable(to_item):
                post_cond = f"mine_{to_item}"
            else:
                post_cond = f"place_stone"

            if in_item in walk_req and 'ERROR' not in walk_req[in_item]:
                pre_cond = f"mine_{in_item}"
                if is_ancestor(nodes[post_cond], nodes[pre_cond]):
                    print(f"Terrain has problem!!! You cannot first {post_cond} before {pre_cond}")
                    pre_cond = f"place_stone"
                    stack = copy.deepcopy(walk_req['stone'])
                    stack_item = "stone"
                else:
                    stack = copy.deepcopy(walk_req[in_item])
                    stack_item = in_item
            else:
                if in_item in env_rules.place['stone']['where']:
                    pre_cond = "place_stone"
                    if post_cond != pre_cond and is_ancestor(nodes[post_cond], nodes[pre_cond]):
                        print(f"Terrain has problem!!! You cannot first {post_cond} before {pre_cond}!!")
                        return False
                    else:
                        stack = copy.deepcopy(walk_req['stone'])
                        stack_item = 'stone'
                else:
                    print(f"Terrain has problem!!! You cannot place stone in {in_item}")
                    return False
            if stack:
                if 'ERROR' in stack:
                    print(f"Terrain has problem!!! You cannot walk to this place [{stack_item}]!!")
                    return False
                while stack:
                   
                    pre = stack.pop(0)
                    # 和 toitem的关系
                    if post_cond == f"mine_{pre}":
                        break
                    else:
                        if is_ancestor(nodes[post_cond], nodes[f"mine_{pre}"]):
                            print(f"Terrain has problem!!! When you walk to this place [{in_item}], you cannot first mine_{to_item} then mine_{pre}!!")
                            return False
    
        
    def to_root(graph):
        visited = set()
        stack = set()

        def dfs(node):
            if node.root or node.toroot:
                node.toroot = True
                return True
            if node in stack:
                node.toroot = False
                # stack.remove(node)# TODO
                return False
            if node in visited:
                node.toroot = True # TODO
                # stack.remove(node)
                return True

            visited.add(node)
            stack.add(node)

            
            node_flag = 0
           
            
            for parent in node.parents:
                if dfs(parent):
                    node_flag += 1
                    if node.parent_op == 'OR':
                        node.toroot = True
                        # stack.remove(node) # TODO
                        return True
                else:
                    node_flag -= 1
                    if node.parent_op != 'OR':
                        node.toroot = False
                        # stack.remove(node) # TODO
                        return False
                    
            stack.remove(node)
            # node.cycle = False
            # return False
            if node_flag == len(node.parents):
                node.toroot = True
                return True
            else:
                node.toroot = False
                return False
            
        for node_name, node_class in graph.items():
            if node_class.toroot == None:
                if dfs(node_class):
                    node_class.toroot = True
                else:
                    node_class.toroot = False
                    print(f"{node_class.name} cannot achieve!!")
                    return False

        return True

    to_root_flag = to_root(nodes)

    # # simplify the tree
    # # if one node has been current node's ancestor, then it need to be removed from the parents
    # for key, value in nodes.items():
    #     all_parents = copy.copy(value.parents)
    #     if value.parent_op == "AND":
    #         for parent in all_parents:
    #             value.parents.remove(parent)
    #             if not is_ancestor(parent, value):
    #                 value.parents.append(parent)
    if not to_root_flag:
        print("There is something cannot achieve!!!")
        return False
    def amount_satisfy(root_nodes):


        visited = set()



        # dfs root node
        def dfs(node):
            if node not in visited:
                visited.add(node)
                if 'mine' in node.name:
                    item = node.name.split('_')[-1]
                    num = terr_items[item]
                    terr_items[item] = 0

                    leave = node.contents[1]['leaves']['material']
                    
                    if leave in terr_items:
                        if leave == item:
                            terr_items[leave] = MAX_INF
                        else:
                            terr_items[leave] += num 
                    
                    for child in node.children:
                        inv_item = child.name.split('_')[-1]
                        
                        if inv_item in inv_items and inv_item in node.contents[1]['receive']:
                            if isinstance(node.contents[1]['receive'][inv_item], dict):
                                inv_items[inv_item] += 0.5 * num * node.contents[1]['receive'][inv_item].get('probability', 1)
                            else:
                                inv_items[inv_item] += 0.5 * num
                        # for leave in leaves:
                        if 'mine' in child.name:
                            if leave in terr_items:
                                terr_items[leave] -= num
                            if item in inv_items:
                                inv_items[item] += 0.1 * num
                            if len(walk_req[item]) > 0:
                                for acq in walk_req[item]:
                                    if acq in inv_items:
                                        inv_items[acq] += 0.1 * num
                                leave = nodes[f'mine_{walk_req[item][-1]}'].contents[1]['leaves']['material']
                                terr_items[leave] += 0.1 * num
                            else:
                                leave = node.contents[1]['leaves']['material']
                                if leave in terr_items:
                                    terr_items[leave] += 0.1 * num

                        if child.parent_op == "OR" or len(child.parents) == 1 or set(child.parents).issubset(set(visited)):
                            dfs(child)
                        # if child.parent_op == "OR" or len(child.parents) == 1:
                        #     # visited.add(child)
                        #     dfs(child, visited)
                            
                        # elif set(child.parents).issubset(set(visited)):
                        #     # dfs(child)
                        #     dfs(child, visited)
                
                elif 'has' in node.name and node.name.split('_')[-1] in inv_items:
                    item = node.name.split('_')[-1]
                    num = inv_items[item]

                    for child in node.children:
                        if child.parent_op == "OR" or len(child.parents) == 1 or  set(child.parents).issubset(set(visited)):
                            if 'place_stone' == child.name:
                                terr_items['stone'] += 1
                                
                            for each_item, item_req in child.contents[1]['uses'].items():
                            # req = child.contents[1]['uses'][item]

                                inv_items[each_item] -= item_req
                            dfs(child)
                        
                elif 'nearby' in node.name:
                    for child in node.children:
                        if child.parent_op == "OR" or len(child.parents) == 1 or  set(child.parents).issubset(set(visited)):
                            if 'make' in child.name:
                                for each_item, item_req in child.contents[1]['uses'].items():
                                # req = child.contents[1]['uses'][item]

                                    inv_items[each_item] -= item_req
                            dfs(child)
                
                else:
                    
                    for child in node.children:

                        if child.parent_op == "OR" or len(child.parents) == 1 or set(child.parents).issubset(set(visited)):
                            if node.name == 'place_stone' and 'mine' in child.name:
                                inv_items['stone'] -= 4
                                if valid('stone'):
                                    terr_items['stone'] += 4
                                else:
                                    inv_items['stone'] += 4
                                    if len(walk_req['stone']) > 0:
                                        for acq in walk_req['stone']:
                                            if acq in inv_items:
                                                inv_items[acq] += 4
                                        leave = nodes[f'mine_{acq}'].contents[1]['leaves']['material']
                                        terr_items[leave] += 4
                                    else:
                                        leave = nodes[f'mine_stone'].contents[1]['leaves']['material']
                                        if leave in terr_items:
                                            terr_items[leave] += 4
                            dfs(child)
        
        # while len(visited) != len(nodes):
        for _, root_node in root_nodes.items():
            
            dfs(root_node)
        assert len(visited) == len(nodes)



        for key, value in inv_items.items():
            if value < 0:
                print(f"The material {key} is not enough!!")
                
                return False
        return True
        
        
    if terr_items:
        if not amount_satisfy(root_nodes):
            return False
        
        # inv_values = inv_items.values()

        
        # has_negative = any(value < 0 for value in inv_values)
        # if has_negative:
        #     print("地形材料不符合数量")
        #     return False

    # vis_tree(nodes, True, 'Tech_tree_cycle')
    # vis_tree(nodes, True, filename / 'Tech_tree2')
    return True


