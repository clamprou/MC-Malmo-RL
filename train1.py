from __future__ import print_function
from __future__ import division
from malmo_agent import *
from ai1 import *

NUM_EPISODES = 10
agent = Agent()

for episode in range(NUM_EPISODES):
    agent.start_episode(episode)
    t = 0
    state = torch.tensor([agent.zombie_los_in_range, agent.zombie_los, agent.current_pos[0]
                             , agent.current_pos[1], agent.current_life], dtype=torch.float32, device=device).unsqueeze(0)
    while agent.is_episode_running():
        if agent.observe_env():
            action = select_action(state)
            agent.play_action(action.item())
            agent.observe_env()
            reward = torch.tensor([agent.tick_reward], device=device)
            next_state = torch.tensor([agent.zombie_los_in_range, agent.zombie_los, agent.current_pos[0]
                                          , agent.current_pos[1], agent.current_life], dtype=torch.float32, device=device).unsqueeze(0)
            memory.push(state, action, next_state, reward)
            state = next_state
            optimize_model()
            target_net_state_dict = target_net.state_dict()
            policy_net_state_dict = policy_net.state_dict()
            for key in policy_net_state_dict:
                target_net_state_dict[key] = policy_net_state_dict[key]*TAU + target_net_state_dict[key]*(1-TAU)
            target_net.load_state_dict(target_net_state_dict)
            print("reward:"+str(agent.tick_reward)+"[zombie_los:"+str(agent.zombie_los_in_range)+" zombie_los_range:" +
                  str(agent.zombie_los)+" agent_pos:("+str(agent.current_pos[0])+","+str(agent.current_pos[1])
                  + ") zombie_pos:("+str(agent.zombies_pos[0])+"," + str(agent.zombies_pos[1]) + ")" + " life:" +
                  str(agent.current_life) + " action:" + agent.actions[action])
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
