from __future__ import print_function
from __future__ import division
from malmo_agent import *
from ai import *
import matplotlib.pyplot as plt

NUM_EPISODES = 5

rewards = []
scores = []
kills = []
prev_kills = 0
player_life = []
survival_time = []

agent = Agent()

brain = Dqn(2, 7, 0.9)
brain.load()
time.sleep(1)
for episode in range(NUM_EPISODES):
    agent.start_episode(episode)
    t = 0
    while agent.is_episode_running():
        if agent.observe_env():
            action = brain.update(agent.tick_reward, [agent.zombie_los_in_range, agent.zombie_los])
            scores.append(brain.score())
            agent.play_action(action)

            agent.update_per_tick()
            t += 1

    survival_time.append(agent.survival_time_score)
    player_life.append(agent.current_life)
    if agent.zombie_kill_score != prev_kills:
        kills.append(agent.zombie_kill_score - prev_kills)
        prev_kills = agent.zombie_kill_score
    else:
        kills.append(0)
    rewards.append(agent.episode_reward)
    plot_table(rewards, "rewards")



    agent.quit_episode()

    # Keep Agent scores



print('Complete')
plot_table(scores, "Q-values", show_result=True)
plot_table(kills, "kills", show_result=True)
plt.ioff()
plt.show()

brain.save()

time.sleep(1)
