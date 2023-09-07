from __future__ import print_function
from __future__ import division
from malmo_agent import *
import matplotlib.pyplot as plt

NUM_EPISODES = 5

scores = []
kills = []
player_life = []
survival_time = []
last_reward = 0

agent = Agent()

time.sleep(1)
for episode in range(1, NUM_EPISODES + 1):
    kills.append(0)
    player_life.append(0)
    survival_time.append(0)
    agent.start_episode(episode)
    while agent.is_episode_running():
        # Do AI things
        if agent.observe_env():


        agent.update_per_tick()


    agent.quit_episode()

    # Keep Agent scores
    kills[episode - 1] = agent.zombie_kill_score
    player_life[episode - 1] = agent.current_life
    survival_time[episode - 1] = agent.survival_time_score






plt.figure(1)
plt.plot(scores, label='Scores: Q-values', color='blue')
plt.xlabel('Ticks')
plt.ylabel('Q-values')
plt.title('Q-value probabilities for every tick')
plt.legend()

plt.figure(2)
plt.plot(kills, label='Player kills', color='green')
plt.xlabel('Episodes')
plt.ylabel('Kills')
plt.title('Sum of player kills per episode')
plt.legend()

plt.figure(3)
plt.plot(player_life, label='Player life', color='red')
plt.xlabel('Episodes')
plt.ylabel('Life')
plt.title('Life of player per episode')
plt.legend()

plt.figure(4)
plt.plot(survival_time, label='Time alive', color='purple')
plt.xlabel('Episodes')
plt.ylabel('Time alive')
plt.title('Survival time score per episode')
plt.legend()

plt.show()

time.sleep(1)
