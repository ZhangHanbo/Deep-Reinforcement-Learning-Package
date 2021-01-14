import argparse
import os
import torch
import numpy as np
from gym import spaces
from tensorboardX import SummaryWriter
from collections import deque

import sys
sys.path.append("./softgymenvs/")

from utils.envbuilder import build_env, set_global_seeds
from utils.vec_envs import space_dim
from agents import *
from agents.config import *
from configs import CONFIGS

torch.set_default_tensor_type(torch.FloatTensor)

def arg_parser():
    parser = argparse.ArgumentParser(description='PyTorch REINFORCE example')
    parser.add_argument('--alg', default='NAF',
                        help='algorithm to use: DQN | DDQN | DuelingDQN | DDPG | NAF | PG | NPG | TRPO | PPO')
    parser.add_argument('--env', default="Reacher-v1",
                        help='name of the environment to run')
    parser.add_argument('--reward', default='sparse',
                        help='reward type during training: dense | sparse, default: sparse. NOTE: this argument will be '
                             'used only when the environment supports sparse rewards. ')
    parser.add_argument('--ou_noise', type=bool, default=True)
    # TODO: SUPPORT PARAM NOISE
    parser.add_argument('--param_noise', type=bool, default=False)
    # TODO: SUPPORT NOISE END
    parser.add_argument('--exploration_end', type=int, default=100, metavar='N',
                        help='number of episodes with noise (default: 100)')
    parser.add_argument('--seed', type=int, default=4, metavar='N',
                        help='random seed (default: 4)')
    # TODO: add '--num_steps' '--num_episodes' '--updates_per_step' '--snapshot_episode' '--render' into config file.
    parser.add_argument('--num_envs', type=int, default=1, metavar='N',
                        help='env numbers (default: 1)')
    parser.add_argument('--num_steps', type=int, default=1e6, metavar='N',
                        help='max episode length (default: 1e6)')
    parser.add_argument('--network', default=None,
                        help='network type')
    parser.add_argument('--updates_per_step', type=int, default=1, metavar='N',
                        help='model updates per simulator step (default: 1)')
    parser.add_argument('--display', type=int, default=500, metavar='N',
                        help='episode interval for display (default: 5)')
    parser.add_argument('--eval_interval', type=int, default=0, metavar='N',
                        help='episode interval for evaluation (default: 0). 0 means no evaluation option is applied.')
    parser.add_argument('--num_evals', type=int, default=10, metavar='N',
                        help='evaluation episode number each time (default: 10)')
    parser.add_argument('--snapshot_steps', type=int, default=1e4, metavar='N',
                        help='snapshot interval (default: 1e4)')
    parser.add_argument('--resume', action='store_true', default=False,
                        help='whether to resume training from a specific checkpoint')
    parser.add_argument('--unnormobs', action='store_true', default=False,
                        help='whether to normalize inputs')
    parser.add_argument('--unnormret', action='store_true', default=False,
                        help='whether to normalize outputs')
    parser.add_argument('--unnormact', action='store_true', default=False,
                        help='whether to normalize outputs')
    parser.add_argument('--checkpoint', type=int, default=0,
                        help='resume from this checkpoint')
    parser.add_argument('--render', action='store_true', default=False,
                        help='whether to render GUI (default: False) during evaluation.')
    parser.add_argument('--test', help='test the specific policy.', action='store_true', default = False)
    parser.add_argument('--cpu', help='whether use cpu to train', action='store_true', default = False)
    parser.add_argument('--usedemo', action='store_true', default=False,
                        help='whether to use imitation learning to improve performance')
    parser.add_argument('--demopath', default='demos',
                        help='path where you stores the demonstration file demo.hdf5. Now only HTRPO supported.')

    args = parser.parse_args()
    return args

def imitation_pretrain():

    # if args.usedemo:
    #     assert args.alg in {"HTRPO", "HPG"}, "Imitation learning warm-up only supports HTRPO and HPG."
    #     demofile = os.path.join(args.demopath, "demo.pkl")
    #     if not os.path.exists(demofile):
    #         raise RuntimeError("Demo file " + demofile + " does not exist.")
    #     train_configs = {
    #         "batch_size": 100,
    #         "iter_num": 0,
    #         "num_ep_selected": 225, # from the setting of IRIS
    #         "using_act_norm":True
    #     }
    #     info = RL_brain.pretrain_policy_use_demos(demofile, train_configs)
    #     if info["action_mean"] is not None and info["action_std"] is not None:
    #         env.a_mean = info["action_mean"]
    #         env.a_std = info["action_std"]

    pass

if __name__ == "__main__":
    args = arg_parser()

    configs = {
        "norm_ob": not args.unnormobs,
        "norm_rw": not args.unnormret,
    }
    # TODO: REMOVE THE DISABLING OF NORMALIZATION FOR TD3, NAF and DDPG.
    #  IMPROVEMENTS SHOULD BE MADE FOR THESE ALGORITHMS.

    # build game environment
    env, env_type, env_id = build_env(args)
    env.env_id = env_id
    env.env_type = env_type
    env_obs_space = env.observation_space
    env_act_space = env.action_space
    n_states = space_dim(env_obs_space)

    if isinstance(env_act_space, spaces.Discrete):
        n_actions = env_act_space.n  # decrete action space, value based rl brain
        n_action_dims = 1
        DICRETE_ACTION_SPACE = True
    elif isinstance(env_act_space, spaces.Box):
        n_actions = None
        n_action_dims = env_act_space.shape[0]
        DICRETE_ACTION_SPACE = False
    elif isinstance(env_act_space, np.ndarray):
        n_actions = len(env_act_space)
        n_action_dims = 1
        DICRETE_ACTION_SPACE = True
    else:
        assert 0, "Invalid Environment"

    # if env_type not in {"mujoco", "robotics", "robotsuite"}:
    #     print("The chosen env dose not support input normalization. No normalization is applied.")
    #     configs['norm_ob'] = False

    logger = SummaryWriter(comment = args.alg + "-" + args.env)
    output_dir = os.path.join("output", "models", args.alg)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # initialize configurations
    env_id_for_cfg = "".join(args.env.split("-"))
    configs.update(eval("CONFIGS[{}][{}].{}config".format('"' + args.alg + '"', '"' + env_id_for_cfg + '"', args.alg)))
    configs['n_states'] = n_states
    configs['n_action_dims'] = n_action_dims
    configs['dicrete_action'] = DICRETE_ACTION_SPACE
    if n_actions:
        configs['n_actions'] = n_actions
    configs['reward_type'] = args.reward

    # for hindsight algorithms, init goal space of the environment.
    if args.alg in {"HTRPO", "HPG"}:
        configs['other_data'] = env.reset()
        assert isinstance(configs['other_data'], dict), \
            "Please check the environment settings, hindsight algorithms only support goal conditioned tasks."
        configs['reward_fn'] = env.compute_reward
        configs['max_episode_steps'] = env.max_episode_steps

    # init agent
    if args.alg in ("PG", "NPG", "TRPO", "PPO", "AdaptiveKLPPO", "HTRPO", "HPG"):
        if DICRETE_ACTION_SPACE:
            RL_brain = eval(args.alg + "_Softmax(configs)")
        else:
            RL_brain = eval(args.alg + "_Gaussian(configs)")
    else:
        RL_brain = eval(args.alg + "(configs)")

    if not args.cpu:
        RL_brain.cuda()

    # resume networks
    if args.resume:
        RL_brain.load_model(load_path=output_dir, load_point=args.checkpoint)

    if args.usedemo:
        # TODO: imitation learning now is not supported yet.
        imitation_pretrain()

    # training
    if args.alg == "PPO" or args.alg == "AdaptiveKLPPO":
        trained_brain = run_ppo_train(env, RL_brain, args.num_steps, logger)
    elif args.alg == "PG":
        trained_brain = run_pg_train(env, RL_brain, args.num_steps, logger)
    elif args.alg == "NPG":
        trained_brain = run_npg_train(env, RL_brain, args.num_steps, logger)
    elif args.alg == "TRPO":
        trained_brain = run_trpo_train(env, RL_brain, args.num_steps, logger)
    elif args.alg == "NAF":
        trained_brain = run_naf_train(env, RL_brain, args.num_steps, logger, args.display)
    elif args.alg == "DDPG":
        trained_brain = run_ddpg_train(env, RL_brain, args.num_steps, logger, args.display)
    elif args.alg == "TD3":
        trained_brain = run_td3_train(env, RL_brain, args.num_steps, logger, args.display)
    elif args.alg == 'HTRPO':
        trained_brain = run_htrpo_train(env, RL_brain, args.num_steps, logger,
                                        eval_interval = args.eval_interval if args.eval_interval > 0 else None,
                                        num_evals = args.num_evals, render=args.render)
    elif args.alg == 'HPG':
        trained_brain = run_hpg_train(env, RL_brain, args.num_steps, logger,
                                        eval_interval = args.eval_interval if args.eval_interval > 0 else None,
                                        num_evals = args.num_evals, render=args.render)
    else:
        raise RuntimeError("Not an invalid algorithm.")

    logger.close()
