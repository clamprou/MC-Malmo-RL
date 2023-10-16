from __future__ import print_function
from __future__ import division
from malmo_agent import *
from ai1 import *

NUM_EPISODES = 500
agent = Agent()

for episode in range(NUM_EPISODES):
    agent.start_episode(episode)
    t = 0
    state = torch.tensor(agent.state, dtype=torch.float32, device=device).unsqueeze(0)
    while agent.is_episode_running():
        action = select_action(state)
        agent.play_action(action.item())
        agent.observe_env()
        reward = torch.tensor([agent.tick_reward], device=device)
        next_state = torch.tensor(agent.state, dtype=torch.float32, device=device).unsqueeze(0)
        memory.push(state, action, next_state, reward)
        state = next_state
        optimize_model()
        target_net_state_dict = target_net.state_dict()
        policy_net_state_dict = policy_net.state_dict()
        for key in policy_net_state_dict:
            target_net_state_dict[key] = policy_net_state_dict[key]*TAU + target_net_state_dict[key]*(1-TAU)
        target_net.load_state_dict(target_net_state_dict)
        agent.update_per_tick()
        t += 1

    agent.update_per_episode()
    plot_table(agent.rewards, "rewards")

print('Complete')
plot_table(agent.rewards, "rewards", show_result=True)
plot_table(agent.kills, "kills", show_result=True)
plot_table(agent.player_life, "life", show_result=True)
plot_table(agent.survival_time, "survival", show_result=True)
plt.ioff()
plt.show()

time.sleep(1)
