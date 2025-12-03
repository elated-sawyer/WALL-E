import mars.constants as constants
import random
import mars.globalvar as save_yaml
# collect modifed 
import copy, json
import mars.check_techTree as check_techTree


# collect_require_items = ['tree', 'stone', 'coal', 'iron', 'diamond']

# require_options = constants.require

# option_picked = {option: False for option in require_options}


# random_req =  random.sample(require_options, k=len(items))
def deepcopy_dict(d):
    if isinstance(d, dict):
        return {k: deepcopy_dict(v) for k, v in d.items()}
    else:
        return d
    
def deepcopy_list(l):
    if isinstance(l, list):
        return [deepcopy_list(i) for i in l]
    else:
        return l


# place achievement


def change_env_world(args, random):

    random_bool = lambda: bool(random.choice([True, False]))
    random_number = lambda: int(random.choice([1, -1]))
    random_number_null = lambda: int(random.choice([1, -1, 0]))
    # load json
    # with open(parafile, 'r') as file:
    #     params = json.load(file)
    # params = save_yaml.read_yaml(para_file)
    # if not params['regen_world']:
    #     return
    save_yaml._init()
    
    constants.read_world(constants.root / "data.yaml")
    
    

    save_yaml._global_dict = copy.deepcopy(constants._world_yaml)
    
    
    
    
    # save_yaml.set_value('name2name', name2name)
    # save_yaml.set_value('terrain_neighbor', terrain_neighbor)
    if args.change_terrain:
        # change_terrain
        terrain_material = constants.terrain_materials
        
        if args.terrain_constraints == 1:
            constraints = constants.materials_neighbour_1
        elif args.terrain_constraints == 2:
            constraints = constants.materials_neighbour_2
        const = {
            "const1": constants.materials_neighbour_1,
            "const2":constants.materials_neighbour_2
        }
        if args.terrian_kind == 'permutation':
              
            # while True:
                # flag1 = True
                # flag2 = True
            shuffled_materials = random.choice(constants.terrain_materials, len(constants.terrain_materials),replace=False)
            name2name = {item: str(shuffled_materials[idx]) for idx, item in enumerate(constants.terrain_materials)}
            name2name['player'] = 'player'
                # check if satisfy the constraints
                # constraints = constants.material_neighbour_2
                # for key, value in default_neighbor.items():
                #     mod_key, mod_value = name2name[key], name2name[value]
                #     if mod_key in constraints and mod_value not in constraints[mod_key]:
                        
                #         print(f'Error: {mod_key} -> {mod_value} is not allowed')
                #         flag1 = False
                #         break
                #     if args.terrain_constraints == 2:
                #         if mod_key in constraints and mod_value in constraints[mod_key] and mod_value not in const['const1']:
                #             flag2 = False
                # if flag1 and not flag2:
                #     break
            # print the name2name
            print('Name2Name:')
            for key, value in name2name.items():
                print(f'  {key}: {value}')

            save_yaml.set_value('name2name', name2name)
            # print the modified terrain_neighbor
            print('Modified Terrain Neighbor:')
            for key, value in constants.terrain_neighbour.items():
                mod_key, mod_value = name2name[key], name2name[value]
                # if mod_key in constraints:
                constants.terrain_neighbour[mod_key] = mod_value
                print(f'  {name2name[key]}: {name2name[value]}')
                if mod_key in save_yaml._global_dict['collect'] and mod_key != 'water' and mod_key !='lava' and mod_key != 'player' and mod_value not in ['coal', 'iron', 'diamond', 'tree']:
                    save_yaml._global_dict['collect'][mod_key]['leaves']['material'] = str(mod_value)
            save_yaml.set_value('terrain_neighbor', constants.terrain_neighbour)
           
        elif args.terrian_kind == 'individual':
            while True:
                # flag1 = True
                # flag2 = True
                terrain_materials_mark = list()
                for item, neighbor in constants.terrain_neighbour.items():
                    constants.terrain_neighbour[item] = str(random.choice(terrain_material))

                    if item not in terrain_materials_mark:
                        terrain_materials_mark.append(item)
                    if constants.terrain_neighbour[item] not in terrain_materials_mark:
                        terrain_materials_mark.append(constants.terrain_neighbour[item])

                    # check terrain_materials_mark contain all the terrain_material
                    

                    # check 是否符合条件1 or 2
                    # for key, value in terrain_neighbor.items():
                    #     if value not in constraints[key]:
                    #         flag1 = False
                    #     if args.terrain_constraints == 2:
                    #         if value in constraints[key] and value not in const['const1']:
                    #             flag2 = False
                    
                
            
                if len(terrain_materials_mark) == len(terrain_material + ['player']):
                    break
        

            # print the terrain_neighbor
            print('Terrain Neighbor:')
            for key, value in constants.terrain_neighbour.items():
                print(f'  {key}: {value}')
                if key in save_yaml._global_dict['collect'] and key != 'water' and key !='lava' and value not in ['coal', 'iron', 'diamond', 'tree'] :
                    save_yaml._global_dict['collect'][key]['leaves']['material'] = str(value)
            
            save_yaml.set_value('terrain_neighbour', constants.terrain_neighbour)
                
    
    # change npc objects
    if args.change_npc:
        while True:
            nothing = 0
            harm = 0
            npc_obj = constants.npc_objects
            arrowable = None
            if "skeleton" in args.npc_objects:
                arrowable = random.choice(args.npc_objects)
                npc_obj[arrowable]['arrowable'] = True
                npc_obj[arrowable]['arrow_damage_func'] = random_number_null()
            
            for obj in args.npc_objects:
                
                npc_setting = npc_obj[obj]
                if obj != arrowable:
                    npc_setting['arrowable'] = False
                    npc_setting['arrow_damage_func'] = 0
                npc_setting['eatable'] = random_bool()
                npc_setting['defeatable'] = not npc_setting['eatable']
                # npc_setting['attackable'] = random_bool()
                # npc_setting['arrowable'] = random_bool()
                npc_setting['closable'] = random_bool()
                
                npc_setting['can_walk'] = random_bool()
                
                npc_setting['closable_health_damage_func'] = random_number_null()

                if npc_setting['closable_health_damage_func'] == 1 or  npc_setting['closable_health_damage_func'] == -1:
                    npc_setting['attackable'] = True
                else:
                    npc_setting['attackable'] = False
                
                if npc_setting['eatable']:
                    npc_setting['eat_health_damage_func'] = random_number_null()
                    npc_setting['inc_food_func'] = random_number_null()
                    npc_setting['inc_thirst_func'] = random_number_null()
                else:
                    npc_setting['eat_health_damage_func'] = 0
                    npc_setting['inc_food_func'] = 0
                    npc_setting['inc_thirst_func'] = 0
                # npc_setting['eat_health_damage_func'] = random_number_null()
                # npc_setting['inc_food_func'] = random_number_null()
                # npc_setting['inc_thirst_func'] = random_number_null()
                # npc_setting['arrow_damage_func'] = random_number_null()
                
                if npc_setting['closable']:
                    npc_setting['can_walk'] = True
                
            # npc_obj[obj] = npc_setting
                if npc_setting['closable_health_damage_func'] == 0 and npc_setting['eat_health_damage_func'] == 0 and npc_setting['arrow_damage_func'] == 0 and npc_setting['inc_food_func'] == 0 and npc_setting['inc_thirst_func'] == 0:
                    nothing += 1
                if npc_setting['closable_health_damage_func'] == -1 and npc_setting['eat_health_damage_func'] == -1 and npc_setting['arrow_damage_func'] == -1 and npc_setting['inc_food_func'] == -1 and npc_setting['inc_thirst_func'] == -1:
                    harm += 1

            if nothing < 2 and harm == 0:
                break
                
               
        
        save_yaml.set_value('npc_objects', npc_obj)
    
    
    # change drink

    if args.change_drink:
        drink_setting = constants.drink
        

        for item in args.drink:
            

            # while True:
            #     drink_setting[item]['walkable'] = random_bool()
            #     drink_setting[item]['dieable'] = random_bool()
            #     if drink_setting[item]['dieable'] and not drink_setting[item]['walkable']:
            #         continue
            #     else:
            #         break

            # if not drink_setting[item]['dieable']:
            
            drink_setting[item]['inc_drink_func'] = random_number()
            drink_setting[item]['inc_damage_func'] = random_number_null()
            drink_setting[item]['inc_food_func'] = random_number_null()

        save_yaml.set_value('drink', drink_setting)


    
    if args.change_walkable:
        # set dieable
        all_terrain = list(constants.walkable_effect.keys())
        all_terrain.remove(constants.terrain_neighbour['player'])
        if constants.terrain_neighbour['tree'] in all_terrain:
            all_terrain.remove(constants.terrain_neighbour['tree'])
        dieable_terrain = random.choice(all_terrain)
        for item, value in constants.walkable_effect.items():
            # cannot walk on tree
            if item == 'tree':
                continue

            if item == constants.terrain_neighbour['player']:
                value['walkable'] = True
                value['dieable'] = False
                value['walk_health'] = 0
                continue

            if item == constants.terrain_neighbour['tree']:
                value['walk_health'] = 0
                value['walkable'] = True
                value['dieable'] = False
                continue
            if item == dieable_terrain:
                value['walk_health'] = 0
                value['walkable'] = True
                value['dieable'] = True

            if item in list(constants.drink.keys()):
                while True:
                    value['dieable'] = random_bool()
                    value['walkable'] = random_bool()
                    # value['walk_health'] = random_number_null()
                    if value['dieable'] and not value['walkable']:
                        continue

                    if value['dieable']:
                        value['walk_health'] = 0
                    else:
                        if value['walkable']:
                            value['walk_health'] = random_number_null()
                        
                        break
            else:
                value['walkable'] = random_bool()
                if value['walkable']:
                    value['walk_health'] = random_number_null()
        save_yaml.set_value('walkable_effect', constants.walkable_effect)

        walkable_list = []
        for item, value in constants.walkable_effect.items():
            if value['walkable'] and not value['dieable']:
                walkable_list.append(item)

        save_yaml.set_value('walkable', walkable_list)
        
        

    if args.change_achievement:
        # adv_items = list()
        # collect achievement
        collect_str = f"collect_{args.collect_id}"
        collect_name_to_constraints = {
            'collect_1': constants.collect_achievements_1,
            'collect_2': constants.collect_achievements_2,
            'collect_3': constants.collect_achievements_3,
        }
        collect_achievements = collect_name_to_constraints[collect_str]
        
        while True:
            picked_adv = [{'wood_pickaxe': 1}, {'stone_pickaxe': 1}, {'iron_pickaxe': 1}, {}]
            picked_adv_list = {str(option): False for option in picked_adv}
            pick_item_list = {str(option): False for option in constants.collect_items}
            

            for ent_str, cond in collect_achievements.items():
                ents = ent_str.split('/')
                for key, value in collect_achievements[ent_str].items():
                    
                    if key == "leaves":
                        for leave_kind, leave_value in value.items():
                            for each_ent in ents:
                                
                                res = random.choice(leave_value)
                                if isinstance(res, dict):
                                    constants.collect[each_ent][key][leave_kind] = res
                                else:
                                    constants.collect[each_ent][key][leave_kind] = str(res)
                                
                    else:
                        if '[any]' in key:
                            for each_ent in ents:
                                key_rev = key.replace('[any]', '')
                                res = random.choice(value)
                            
                                # constants.collect[each_ent][key].update({k: v for d in res for k, v in d.items()})
                                constants.collect[each_ent][key_rev] = copy.deepcopy(constants.collect[each_ent][key_rev])
                                constants.collect[each_ent][key_rev].update(res)
                        else:
                            if key == 'receive[all]':
                                key = key.replace('[all]', '')
                            for each_ent in ents:
                                res = random.choice(value)

                                constants.collect[each_ent][key] = res
                                if key == 'require':
                                    if str(res) in picked_adv_list:
                                        picked_adv_list[str(res)] = True
                                if key == 'receive':
                                    if len(res) > 0:

                                        if str(list(res.keys())[0]) in pick_item_list:
                                            pick_item_list[str(list(res.keys())[0])] = True
            if args.collect_id == 2 and all(picked_adv_list.values()):
                # choose those not exist in pick_item_list
                # 有多少是False，哪些是False的在pick_item_list里面
                no_picked = [key for key, value in pick_item_list.items() if not value]
                # 
                choose_collect = list(constants.collect.keys())
                choose_collect.remove('water')
                choose_collect.remove('lava')
                terr_base_item = random.choice(choose_collect, size=len(no_picked), replace=False)
                
                for pick, terr_item in zip(no_picked, terr_base_item):
                    pick_item_dict = {pick: {'amount': 1, 'probability': 0.5}}
                    item = list(constants.collect[terr_item]['receive'].keys())[0]
                    pick_item_dict.update({item: {'amount': 1, 'probability': 0.5}})
                    constants.collect[terr_item]['receive'] = pick_item_dict

                break

                # for item in constants.collect_items:
                #     if not pick_item_list[item]:
                #         pick_item_list[item] = True
                #         break

            else:       
                if all(picked_adv_list.values()) and all(pick_item_list.values()):
                    # print(f'All options are picked')
                    break 
        



        # set 可燃性
        
        while True:
            
            true_ignitablity = list()
            false_ignitablity = list()
            constraint_ing = 0
            for item in constants.ignitability:
                constants.ignitability[item] = random_bool()
                if constants.ignitability[item] == True:
                    constraint_ing += 1
                    true_ignitablity.append(item)
                else:
                    constraint_ing -= 1
                    false_ignitablity.append(item)
            # 限制：必须要有可燃物，也要有不可燃物
            if constraint_ing == len(constants.ignitability) or constraint_ing == -len(constants.ignitability):
                continue
            else:
                break

        
        save_yaml.set_value('ignitability', constants.ignitability)

        # place achievement
        for ent_str, cond in constants.place_achievements.items():
            ents = ent_str.split('/')
            for key, value in constants.place_achievements[ent_str].items():
                option_picked_flag = False
                if '[all]' in key:
                    option_picked_flag = True
                    key = key.replace('[all]', '')
                while True:
                    option_picked = {str(option): False for option in value}
                    for each_ent in ents:
                        
                        if each_ent == 'table' and key == 'uses':
                            choice = random.choice(true_ignitablity)
                            res = next((item for item in value if choice in item.keys()), None)
                        elif each_ent == 'furnace' and key == 'uses':
                            choice = random.choice(false_ignitablity)
                            res = next((item for item in value if choice in item.keys()), None)
                        else:
                            if key == 'where':
                                res = value
                            else:
                                res = random.choice(value)
                        constants.place[each_ent][key] = res
                        option_picked[str(res)] = True
                    if all(option_picked.values()) or option_picked_flag == False:
                        # print(f'All options are picked')
                        break
                    # else:
                    #     print(f'Some options are not picked')
            # for each_ent in ents:
            #     constants.place[each_ent] = save_yaml.Inline(constants.place[each_ent])



        # make_achievement
        # based on ignitability to revise the nearby requirements
        for ent, cond in constants.make.items():
            
            if 'sword' in ent:
                mat = ent.split('_')[0]
                constants.make[ent] = (constants.make[f"{mat}_pickaxe"])
                continue
            uses = list(cond['uses'].keys())
            result_list = [constants.ignitability.get(item, False) for item in uses]
            constants.make[ent]['nearby'] = ['table']
            if any(result_list):
                if random_bool():
                    constants.make[ent]['nearby'].append('furnace')
                

        save_yaml.set_value('collect', constants.collect)
        save_yaml.set_value('place', constants.place)
        save_yaml.set_value('make', constants.make)
    
        # print(constants.collect)

        # print(check_techTree.check(constants))
        # if check_techTree.check(constants, args.record):
        #     print("The techTree is invalid! Please regenerate!")
        #     continue
        # else:
            
        #     print("OK! The techTree is valid!")
        #     break
        
    # check_techTree.check(constants, args.record)



    save_yaml.save_yaml(args.record / 'world.yaml', save_yaml._global_dict)


def check_entry(args, random):
    while True:
        change_env_world(args, random)
        if check_techTree.check(constants, args.record):
            print("OK! The techTree is valid!")
            break
            
        else:
            print("The techTree is invalid! Please regenerate!")
            # break
    # save_yaml.save_yaml(args.record / 'world.yaml', constants)
