from __future__ import print_function
from __future__ import division
import gymnasium as gym
import math
import random
import matplotlib
import matplotlib.pyplot as plt
from collections import namedtuple, deque
from itertools import count

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from malmo_agent import *


# set up matplotlib
is_ipython = 'inline' in matplotlib.get_backend()
if is_ipython:
    from IPython import display

plt.ion()

# if GPU is to be used
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

Transition = namedtuple('Transition',
                        ('state', 'action', 'next_state', 'reward'))


class ReplayMemory(object):

    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        """Save a transition"""
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)

class DQN(nn.Module):

    def __init__(self, n_observations, n_actions):
        super(DQN, self).__init__()
        self.layer1 = nn.Linear(n_observations, 128)
        self.layer2 = nn.Linear(128, 128)
        self.layer3 = nn.Linear(128, n_actions)

    # Called with either one element to determine next action, or a batch
    # during optimization. Returns tensor([[left0exp,right0exp]...]).
    def forward(self, x):
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))
        return self.layer3(x)

#BATCH_SIZE is the number of transitions sampled from the replay buffer
# GAMMA is the discount factor as mentioned in the previous section
# EPS_START is the starting value of epsilon
# EPS_END is the final value of epsilon
# EPS_DECAY controls the rate of exponential decay of epsilon, higher means a slower decay
# TAU is the update rate of the target network
# LR is the learning rate of the ``AdamW`` optimizer
BATCH_SIZE = 128
GAMMA = 0.99
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 1000
TAU = 0.005
LR = 1e-4

agent = Agent()

# Get number of actions from gym action space
n_actions = 7
# Get the number of state observations
n_observations = 2

policy_net = DQN(n_observations, n_actions).to(device)
target_net = DQN(n_observations, n_actions).to(device)
target_net.load_state_dict(policy_net.state_dict())

optimizer = optim.AdamW(policy_net.parameters(), lr=LR, amsgrad=True)
memory = ReplayMemory(10000)


steps_done = 0


def select_action(state):
    global steps_done
    sample = random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * \
                    math.exp(-1. * steps_done / EPS_DECAY)
    steps_done += 1
    if sample > eps_threshold:
        with torch.no_grad():
            # t.max(1) will return the largest column value of each row.
            # second column on max result is index of where max element was
            # found, so we pick action with the larger expected reward.
            return policy_net(state).max(1)[1].view(1, 1)
    else:
        return torch.tensor([[random.randint(0, 6)]], device=device, dtype=torch.long)


episode_durations = []


def plot_durations(show_result=False):
    plt.figure(1)
    durations_t = torch.tensor(episode_durations, dtype=torch.float)
    if show_result:
        plt.title('Result')
    else:
        plt.clf()
        plt.title('Training...')
    plt.xlabel('Episode')
    plt.ylabel('Duration')
    plt.plot(durations_t.numpy())
    # Take 100 episode averages and plot them too
    if len(durations_t) >= 100:
        means = durations_t.unfold(0, 100, 1).mean(1).view(-1)
        means = torch.cat((torch.zeros(99), means))
        plt.plot(means.numpy())

    plt.pause(0.001)  # pause a bit so that plots are updated
    if is_ipython:
        if not show_result:
            display.display(plt.gcf())
            display.clear_output(wait=True)
        else:
            display.display(plt.gcf())

def optimize_model():
    if len(memory) < BATCH_SIZE:
        return
    transitions = memory.sample(BATCH_SIZE)
    # Transpose the batch (see https://stackoverflow.com/a/19343/3343043 for
    # detailed explanation). This converts batch-array of Transitions
    # to Transition of batch-arrays.
    batch = Transition(*zip(*transitions))

    # Compute a mask of non-final states and concatenate the batch elements
    # (a final state would've been the one after which simulation ended)
    non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                            batch.next_state)), device=device, dtype=torch.bool)
    non_final_next_states = torch.cat([s for s in batch.next_state
                                       if s is not None])
    state_batch = torch.cat(batch.state)
    action_batch = torch.cat(batch.action)
    reward_batch = torch.cat(batch.reward)

    # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
    # columns of actions taken. These are the actions which would've been taken
    # for each batch state according to policy_net
    state_action_values = policy_net(state_batch).gather(1, action_batch)

    # Compute V(s_{t+1}) for all next states.
    # Expected values of actions for non_final_next_states are computed based
    # on the "older" target_net; selecting their best reward with max(1)[0].
    # This is merged based on the mask, such that we'll have either the expected
    # state value or 0 in case the state was final.
    next_state_values = torch.zeros(BATCH_SIZE, device=device)
    with torch.no_grad():
        next_state_values[non_final_mask] = target_net(non_final_next_states).max(1)[0]
    # Compute the expected Q values
    expected_state_action_values = (next_state_values * GAMMA) + reward_batch

    # Compute Huber loss
    criterion = nn.SmoothL1Loss()
    loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

    # Optimize the model
    optimizer.zero_grad()
    loss.backward()
    # In-place gradient clipping
    torch.nn.utils.clip_grad_value_(policy_net.parameters(), 100)
    optimizer.step()

# if torch.cuda.is_available():
#     NUM_MISSIONS = 600
# else:
#     NUM_MISSIONS = 50

NUM_MISSIONS = 10

zombies_alive = NUM_MOBS
zombie_los = 0
zombie_los_in_range = 0
ticks = 0

scores = []
kills = []
player_life = []
survival_time = []
last_reward = 0

time.sleep(1)
for mission_no in range(1, NUM_MISSIONS+1):
    kills.append(0)
    player_life.append(0)
    survival_time.append(0)
    agent.start_episode(mission_no)
    state = [zombie_los_in_range, zombie_los]
    state = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
    while agent.is_episode_running():
        action = select_action(state)
        agent.play_action(action.item())
        time.sleep(MS_PER_TICK * 0.000001)
        world_state = agent.malmo_agent.getWorldState()
        if world_state.number_of_rewards_since_last_state > 0:
            for rew in world_state.rewards:
                if rew.getValue() > 1:
                    last_reward += 0.1
                else:
                    last_reward += rew.getValue() * 0.1
                print("Last Reward:", last_reward)
        if world_state.number_of_observations_since_last_state > 0:  # Agent is alive
            agent.unresponsive_count = 10
            ob = json.loads(world_state.observations[-1].text)
            if all(d.get('name') != 'Zombie' for d in ob["entities"]):
                agent.all_zombies_died = True
            # Normalize observed data
            cur_zombies_alive = list(d.get('name') == 'Zombie' for d in ob["entities"]).count(True)
            if cur_zombies_alive - zombies_alive != 0:
                last_reward += abs(cur_zombies_alive - zombies_alive) * 0.7
                print("Agent killed a Zombie and got reward:", abs(cur_zombies_alive - zombies_alive) * 0.7)
                print("last Reward:", last_reward)
            zombies_alive = cur_zombies_alive
            if u'LineOfSight' in ob:
                los = ob[u'LineOfSight']
                if los[u'hitType'] == "entity" and los[u'inRange'] and los[u'type'] == "Zombie":
                    zombie_los_in_range = 1
                elif los[u'hitType'] == "entity" and los[u'type'] == "Zombie":
                    zombie_los = 1
            if ob[u'TimeAlive'] != 0:
                agent.survival_time_score = ob[u'TimeAlive']
            if "Life" in ob:
                life = ob[u'Life']
                if life != agent.current_life:
                    agent.current_life = life
            if "MobsKilled" in ob:
                agent.zombie_kill_score = ob[u'MobsKilled']
            if "XPos" in ob and "ZPos" in ob:
                agent.current_pos = (ob[u'XPos'], ob[u'ZPos'])
        elif world_state.number_of_observations_since_last_state == 0:
            agent.unresponsive_count -= 1

        observation = [zombie_los_in_range, zombie_los]
        reward = torch.tensor([last_reward], device=device)
        done = not(agent.is_episode_running())

        if done:
            next_state = None
        else:
            next_state = torch.tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)

        memory.push(state, action, next_state, reward)
        state = next_state

        optimize_model()
        target_net_state_dict = target_net.state_dict()
        policy_net_state_dict = policy_net.state_dict()
        for key in policy_net_state_dict:
            target_net_state_dict[key] = policy_net_state_dict[key]*TAU + target_net_state_dict[key]*(1-TAU)
        target_net.load_state_dict(target_net_state_dict)
        if done:
            episode_durations.append(ticks + 1)
            plot_durations()

        agent.total_reward += last_reward
        agent.episode_reward += last_reward
        last_reward = 0
        zombie_los = 0
        zombie_los_in_range = 0
        # time.sleep(MS_PER_TICK * 0.000001)
        ticks += 1

    agent.quit_episode()
    agent.print_finish_data()
    agent.episode_reward = 0
    zombies_alive = NUM_MOBS
    player_life[mission_no - 1] = agent.current_life
    survival_time[mission_no - 1] = agent.survival_time_score
    kills[mission_no - 1] = agent.zombie_kill_score

print('Complete')
plot_durations(show_result=True)
plt.ioff()
plt.show()

# plt.figure(ticks + 1)
# plt.plot(scores, label='Scores: Q-values', color='blue')
# plt.xlabel('Ticks')
# plt.ylabel('Q-values')
# plt.title('Q-value probabilities for every tick')
# plt.legend()

plt.figure(ticks + 2)
plt.plot(kills, label='Player kills', color='green')
plt.xlabel('Episodes')
plt.ylabel('Kills')
plt.title('Sum of player kills per episode')
plt.legend()

plt.figure(ticks + 3)
plt.plot(player_life, label='Player life', color='red')
plt.xlabel('Episodes')
plt.ylabel('Life')
plt.title('Life of player per episode')
plt.legend()

plt.figure(ticks + 4)
plt.plot(survival_time, label='Time alive', color='purple')
plt.xlabel('Episodes')
plt.ylabel('Time alive')
plt.title('Survival time score per episode')
plt.legend()

plt.show()