from __future__ import print_function
from __future__ import division
from malmo_agent import *
from ai import *
import matplotlib.pyplot as plt

NUM_EPISODES = 2000

rewards = []
scores = []
kills = []
prev_kills = 0
player_life = []
survival_time = []

agent = Agent()

brain = Dqn(5, 7, 0.9)
brain.load()
for episode in range(NUM_EPISODES):
    agent.start_episode(episode)
    t = 0
    while agent.is_episode_running():
        if agent.observe_env():
            action = brain.update(agent.tick_reward, [agent.zombie_los_in_range, agent.zombie_los, agent.current_pos[0]
                                  , agent.current_pos[1], agent.current_life])
            scores.append(brain.score())
            agent.play_action(action)
            print("reward:"+str(agent.tick_reward)+"[zombie_los:"+str(agent.zombie_los_in_range)+" zombie_los_range:" +
                  str(agent.zombie_los)+" agent_pos:("+str(agent.current_pos[0])+","+str(agent.current_pos[1])
                  + ") zombie_pos:("+str(agent.zombies_pos[0])+"," + str(agent.zombies_pos[1]) + ")" + " life:" +
                  str(agent.current_life) + " action:"+ agent.actions[action])
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
    plot_table(scores, "Score")



    agent.quit_episode()



print('Complete')
plot_table(scores, "Q-values", show_result=True)
plot_table(rewards, "rewards", show_result=True)
plot_table(kills, "kills", show_result=True)
plot_table(player_life, "life", show_result=True)
plot_table(survival_time, "survival", show_result=True)
plt.ioff()
plt.show()

brain.save()

time.sleep(1)
