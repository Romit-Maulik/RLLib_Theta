from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
HERE = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0,HERE)

import argparse
import numpy as np
import gym
from gym import spaces
from ray.rllib.models import ModelCatalog
from ray.rllib.models.tf.tf_modelv2 import TFModelV2
from ray.rllib.models.tf.fcnet_v2 import FullyConnectedNetwork
import ray.rllib.agents.ppo as ppo

import ray
from ray import tune
from ray.rllib.utils import try_import_tf
from ray.tune import grid_search
from ray.tune.registry import register_env
from ray.tune.logger import pretty_print
from time import time

parser = argparse.ArgumentParser()
parser.add_argument("--ray-address")
args = parser.parse_args()

tf = try_import_tf()


#debugging by following example code 
class CustomModel(TFModelV2):
    """Example of a custom model that just delegates to a fc-net."""

    def __init__(self, obs_space, action_space, num_outputs, model_config,
         name):
        super(CustomModel, self).__init__(obs_space, action_space, num_outputs,
                          model_config, name)
        self.model = FullyConnectedNetwork(obs_space, action_space,
                           num_outputs, model_config, name)
        self.register_variables(self.model.variables())

    def forward(self, input_dict, state, seq_lens):
        return self.model.forward(input_dict, state, seq_lens)

    def value_function(self):
        return self.model.value_function()


if __name__ == "__main__":
    # Can also register the env creator function explicitly with:
    zero_time = time()
    ray.init(redis_address=args.ray_address)
    print('***********************************************************')
    print('Nodes used:',len(ray.nodes()))
    print('Available resources:',ray.available_resources())
    print('***********************************************************')

    connect_time = time()
    ModelCatalog.register_custom_model("my_model", CustomModel)
    register_time = time()

    config = ppo.DEFAULT_CONFIG.copy()
    config["log_level"] = "WARN"
    config["num_gpus"] = 0
    #config["num_workers"] = len(ray.nodes())
    config["num_workers"] = int(ray.available_resources()['CPU'])
    config["lr"] = 1e-4
    config["simple_optimizer"] = False
    config["num_envs_per_worker"] = 1

    # Add custom model for policy
    model={}
    model["custom_model"] = "my_model"
    config["model"] = model

    # Trainer
    trainer = ppo.PPOTrainer(config=config, env="CartPole-v0")
    trainer_time = time()

    # Can optionally call trainer.restore(path) to load a checkpoint.
    for i in range(10):
        # Perform one iteration of training the policy with PPO
        print('Performing iteration:',i)
        init_time = time()
        result = trainer.train()
        print('Iteration time:',time()-init_time)

    iterations_time = time()
    
    print(pretty_print(result))

    # Final save
    init_time = time()
    checkpoint = trainer.save()
    print("Final checkpoint saved at", checkpoint)

    f = open("rl_checkpoint",'w')
    f.write(checkpoint)
    f.close()
    final_time = time()

    print('Breakdown of times in this experiment')
    print('Time to connect:',connect_time-zero_time)
    print('Time to register environment:',register_time - connect_time)
    print('Time to setup PPO trainer:',trainer_time - register_time)
    print('Time for total iterations:',iterations_time - trainer_time)
    print('Time to save checkpoint:',final_time - init_time)
    print('Total time to solution:',final_time - zero_time)
