from .env import Env
from .recorder import Recorder

try:
  import gym
  gym.register(
      id='MarsReward-v1',
      entry_point='mars:Env',
      max_episode_steps=10000,
      kwargs={'reward': True})
  gym.register(
      id='MarsNoReward-v1',
      entry_point='mars:Env',
      max_episode_steps=10000,
      kwargs={'reward': False})
except ImportError:
  pass
