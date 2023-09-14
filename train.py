from __future__ import print_function
from __future__ import division
from malmo_agent import *
import matplotlib.pyplot as plt
from ai_cart_pole1 import *

NUM_EPISODES = 300

scores = []
kills = []
player_life = []
survival_time = []
last_reward = 0

agent = Agent()

time.sleep(1)
for episode in range(NUM_EPISODES):
    kills.append(0)
    player_life.append(0)
    survival_time.append(0)
    agent.start_episode(episode)
    state = [agent.zombie_los, agent.zombie_los_in_range]
    state = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
    t = 0
    while agent.is_episode_running():
        if agent.observe_env():
            action = select_action(state)
            agent.play_action(action.item())
            time.sleep(MS_PER_TICK * 0.000001)
            agent.observe_env()
            observation = [agent.zombie_los, agent.zombie_los_in_range]
            reward = agent.tick_reward
            reward = torch.tensor([reward], device=device)
            done = not agent.is_episode_running()
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

    episode_durations.append(agent.episode_reward)
    plot_durations()



    agent.quit_episode()

    # Keep Agent scores
    kills[episode - 1] = agent.zombie_kill_score
    player_life[episode - 1] = agent.current_life
    survival_time[episode - 1] = agent.survival_time_score



print('Complete')
plot_durations(show_result=True)
plt.ioff()
plt.show()


# plt.figure(1)
# plt.plot(scores, label='Scores: Q-values', color='blue')
# plt.xlabel('Ticks')
# plt.ylabel('Q-values')
# plt.title('Q-value probabilities for every tick')
# plt.legend()
#
# plt.figure(2)
# plt.plot(kills, label='Player kills', color='green')
# plt.xlabel('Episodes')
# plt.ylabel('Kills')
# plt.title('Sum of player kills per episode')
# plt.legend()
#
# plt.figure(3)
# plt.plot(player_life, label='Player life', color='red')
# plt.xlabel('Episodes')
# plt.ylabel('Life')
# plt.title('Life of player per episode')
# plt.legend()
#
# plt.figure(4)
# plt.plot(survival_time, label='Time alive', color='purple')
# plt.xlabel('Episodes')
# plt.ylabel('Time alive')
# plt.title('Survival time score per episode')
# plt.legend()
#
# plt.show()

time.sleep(1)
