from __future__ import print_function
from __future__ import division
from malmo_agent import *

NUM_EPISODES = 20
agent = Agent()

for episode in range(NUM_EPISODES):
    agent.start_episode(episode)
    t = 0
    while agent.is_episode_running():
        if agent.observe_env():
            agent.play_action(0)
            print("reward:"+str(agent.episode_reward)+"[zombie_los:"+str(agent.zombie_los_in_range)+" zombie_los_range:" +
                  str(agent.zombie_los)+" agent_pos:("+str(agent.current_pos[0])+","+str(agent.current_pos[1])
                  + ") zombie_pos:("+str(agent.zombies_pos[0])+"," + str(agent.zombies_pos[1]) + ")" + " life:" +
                  str(agent.current_life))
            agent.update_per_tick()
            t += 1

    agent.update_per_episode()
    # plot_table(agent.rewards, "rewards")

print('Complete')
plot_table(agent.rewards, "rewards", show_result=True)
plot_table(agent.kills, "kills", show_result=True)
plot_table(agent.player_life, "life", show_result=True)
plot_table(agent.survival_time, "survival", show_result=True)
plt.ioff()
plt.show()

time.sleep(1)
