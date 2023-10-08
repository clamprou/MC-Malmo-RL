from __future__ import print_function
from __future__ import division
from malmo_agent import *

NUM_EPISODES = 20
agent = Agent()

for episode in range(NUM_EPISODES):
    agent.start_episode(episode)
    t = 0
    while agent.is_episode_running():
        agent.observe_env()
        # print("State:", agent.state)
        # print("Tick Reward:", agent.tick_reward)
        # print("Sum Reward:", str(agent.episode_reward))
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
