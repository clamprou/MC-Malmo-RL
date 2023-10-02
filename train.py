from __future__ import print_function
from __future__ import division
from malmo_agent import *
import matplotlib.pyplot as plt
from ai_cart_pole1 import *

NUM_EPISODES = 200

rewards = []
scores = []
kills = []
prev_kills = 0
player_life = []
survival_time = []

agent = Agent()

for episode in range(NUM_EPISODES):
    agent.start_episode(episode)
    state = [agent.zombie_los_in_range, agent.zombie_los, agent.current_pos[0], agent.current_pos[1], agent.current_life]
    state = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
    t = 0
    while agent.is_episode_running():
        if agent.observe_env():
            action = select_action(state)
            agent.play_action(action.item())
            agent.observe_env()
            observation = [agent.zombie_los_in_range, agent.zombie_los, agent.current_pos[0], agent.current_pos[1], agent.current_life]
            reward = torch.tensor([agent.tick_reward], device=device)
            done = not agent.is_episode_running()
            print("reward:"+str(agent.tick_reward)+"[zombie_los:"+str(agent.zombie_los_in_range)+" zombie_los_range:" +
                  str(agent.zombie_los)+" agent_pos:("+str(agent.current_pos[0])+","+str(agent.current_pos[1])
                  + ") zombie_pos:("+str(agent.zombies_pos[0])+"," + str(agent.zombies_pos[1]) + ")" + " life:" +
                  str(agent.current_life) + " action:"+ agent.actions[action])
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

            agent.update_per_tick()
            t += 1
            agent.play_action(0)

    survival_time.append(agent.survival_time_score)
    player_life.append(agent.current_life)
    if agent.zombie_kill_score != prev_kills:
        kills.append(agent.zombie_kill_score - prev_kills)
        prev_kills = agent.zombie_kill_score
    else:
        kills.append(0)

    rewards.append(agent.episode_reward)
    # plot_table(rewards, "Rewards")



    agent.quit_episode()



print('Complete')
# plot_table(scores, "Q-values", show_result=True)
plot_table(rewards, "rewards", show_result=True)
plot_table(kills, "kills", show_result=True)
plot_table(player_life, "life", show_result=True)
plot_table(survival_time, "survival", show_result=True)
plt.ioff()
plt.show()

time.sleep(1)