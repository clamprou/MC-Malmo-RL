from __future__ import print_function
from __future__ import division
from malmo_agent import *
from ai import *
from gym_env import FightingZombiesDisc

NUM_EPISODES = 2500
env = FightingZombiesDisc()

for episode in range(NUM_EPISODES):
    print("Running mission #" + str(episode)) # problem
    state, done = env.reset()
    t = 0
    state = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
    while not done:
        action = select_action(state)
        observation, reward, done = env.step(action.item())
        reward = torch.tensor([reward], device=device)
        next_state = torch.tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
        memory.push(state, action, next_state, reward)
        state = next_state
        optimize_model()
        target_net_state_dict = target_net.state_dict()
        policy_net_state_dict = policy_net.state_dict()
        for key in policy_net_state_dict:
            target_net_state_dict[key] = policy_net_state_dict[key]*TAU + target_net_state_dict[key]*(1-TAU)
        target_net.load_state_dict(target_net_state_dict)
        t += 1

    # plot_table(agent.rewards, "rewards")

print('Complete')
plot_table(env.agent.rewards, "rewards", show_result=True)
plot_table(env.agent.kills, "kills", show_result=True)
plot_table(env.agent.player_life, "life", show_result=True)
plot_table(env.agent.survival_time, "survival", show_result=True)
plt.ioff()
plt.show()

time.sleep(1)
