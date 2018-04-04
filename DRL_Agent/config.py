from torch import optim
from torch.nn import MSELoss

AGENT_CONFIG = {
    'lr':0.01,
    'mom':0,
    'reward_decay':0.9,
    'e_greedy':0.9,
    'batch_size':32,
    'memory_size': 10000,
}

DQN_CONFIG = {
    'replace_target_iter':300,
    'e_greedy_increment':None,
    'optimizer': optim.RMSprop,
    'loss' : MSELoss
}

DDPG_CONFIG = {
    'tau' : 0.001,
    'noise_var' : 3,
    'noise_min' : 0,
    'noise_decrease' : 0.0005,
    'optimizer_a': optim.Adam,
    'optimizer_c': optim.Adam,
    'lr_a' : 1e-3,
    'critic_loss': MSELoss
}

NAF_CONFIG = {
    'tau' : 0.001,
    'noise_var' : 3,
    'noise_min' : 0,
    'noise_decrease' : 0.0005,
    'optimizer': optim.Adam,
    'loss': MSELoss
}

TRPO_CONFIG = {
    'cg_iters': 10,
    'cg_residual_tol' : 1e-10,
    'cg_damping': 1e-3,
    'policy_type': 'FC',
    'value_type': 'FC',
    'action_var':1,
    'max_kl_divergence':0.001,
    'loss_func_v':MSELoss,
    'v_optimizer':optim.LBFGS
}

POLICY_BASED_AGENT = {

}