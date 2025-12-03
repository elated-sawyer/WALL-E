# Mars
Mars is an interactive environment built on the Crafter framework, designed to evaluate situated inductive reasoning in agents. It introduces counter-commonsense elements by modifying terrain, survival settings, and task dependencies. This environment provides a platform to assess how agents adapt and learn in new, unfamiliar contexts, highlighting their ability to perform situated inductive reasoning beyond pre-existing knowledge.

## Code Structure
```
├── mars
│     ├── assets     # Assets for the game
│     ├── change_techTree.py     # Change the tech tree
│     ├── check_techTree.py     # the principle that the tech tree should follow
│     ├── data.yaml     # the origin world setting (crafter)
│     ├── meta_constraints.yaml     # the constraints for the world setting
│     └── run_gui.py     # play the game
├── final_world     # seven modified worlds
│     ├── default     # the default world
│            ├── world.yaml     # the world setting
│            ├── Tech_tree.png    # the dependency graph of the world
│            ├── terrain.png     # the terrain of the world
├── baselines     # baselines for the game 
├── video     # the demo video for each world
├── LICENCE
├── README.md
└── setup.py
```

## Installation

```sh
conda create -n mars python=3.10    # create a new conda environment
conda activate mars    # activate the environment
cd Mars   # go to the Mars directory
python setup.py install  # Install Mars
```

## Modify the World or generate a new world
1) You can copy the default world and modify it or generate a new world by changing the world setting in the `world.yaml` file. Note that the world setting should follow the principle in the `check_techTree.py` file.
```python
world_path = pathlib.Path('myworld/modified_world')
mars.constants.read_world(world_path)
check(constants, world_path)
```
2) You can also randomly generate a new world by running the following command:
```sh
python3 -m mars.run_gui --record myworld/test1 --gen_world True --change_npc True # Generate a new world that only modifies the NPC (cow, zombie, ect) and adhere to the principle.
```
## Play the Game
```sh

python3 -m mars.run_gui --record myworld/test1 --gen_world False # Play the game
```
When you finish the game, you can find the recorded video in the `myworld/test1` directory.

## Baselines
We provide a few baselines for the game. You can find the LLM-based method in the `baselines` directory. The specific usage of the various baselines is described in the corresponding model directories. For RL-based methods, we use the `stable-baselines3` library for PPO and the `dreamerv3-torch` (https://github.com/NM512/dreamerv3-torch) code for DreamerV3. The parameters are set to the default values.

## Questions
If you have any questions, please feel free to contact us at xjtang0920@gmail.com.
You might encounter the error: `ImportError: numpy.core.multiarray failed to import`. In this case, you need to run the following commands:
```sh
pip uninstall numpy
pip install numpy
```
