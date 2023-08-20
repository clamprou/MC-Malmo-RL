from __future__ import print_function
from __future__ import division
from malmo_agent import *
from ai import *
import matplotlib.pyplot as plt

NUM_MISSIONS = 10
zombies_alive = NUM_MOBS
zombie_los = 0
zombie_los_in_range = 0

scores = []
kills = []
player_life = []
survival_time = []
last_reward = 0

agent = Agent()

brain = Dqn(2, 9, 0.9)
brain.load()
time.sleep(1)
for mission_no in range(1, NUM_MISSIONS+1):
    kills.append(0)
    player_life.append(0)
    survival_time.append(0)
    agent.start_mission(mission_no)
    while agent.is_mission_running():
        world_state = agent.malmo_agent.getWorldState()
        if world_state.number_of_rewards_since_last_state > 0:
            for rew in world_state.rewards:
                if rew.getValue() > 1:
                    last_reward += 0.1
                else:
                    last_reward += rew.getValue() * 0.1
                print("Last Reward:", last_reward)
        if world_state.number_of_observations_since_last_state > 0:  # Agent is alive
            agent.unresponsive_count = 10
            ob = json.loads(world_state.observations[-1].text)
            if all(d.get('name') != 'Zombie' for d in ob["entities"]):
                agent.all_zombies_died = True
            # Normalize observed data
            cur_zombies_alive = list(d.get('name') == 'Zombie' for d in ob["entities"]).count(True)
            if cur_zombies_alive - zombies_alive != 0:
                last_reward += abs(cur_zombies_alive - zombies_alive) * 0.7
                print("Agent killed a Zombie and got reward:", abs(cur_zombies_alive - zombies_alive) * 0.7)
                print("last Reward:", last_reward)
            zombies_alive = cur_zombies_alive
            if u'LineOfSight' in ob:
                los = ob[u'LineOfSight']
                if los[u'hitType'] == "entity" and los[u'inRange'] and los[u'type'] == "Zombie":
                    zombie_los_in_range = 1
                elif los[u'hitType'] == "entity" and los[u'type'] == "Zombie":
                    zombie_los = 1
            if ob[u'TimeAlive'] != 0:
                agent.survival_time_score = ob[u'TimeAlive']
            if "Life" in ob:
                life = ob[u'Life']
                if life != agent.current_life:
                    agent.current_life = life
            if "MobsKilled" in ob:
                agent.zombie_kill_score = ob[u'MobsKilled']
            if "XPos" in ob and "ZPos" in ob:
                agent.current_pos = (ob[u'XPos'], ob[u'ZPos'])
            action = brain.update(last_reward, [zombie_los_in_range, zombie_los])
            scores.append(brain.score())
            agent.play_action(action)
        elif world_state.number_of_observations_since_last_state == 0:
            agent.unresponsive_count -= 1

        agent.total_reward += last_reward
        agent.episode_reward += last_reward
        last_reward = 0
        zombie_los = 0
        zombie_los_in_range = 0
        time.sleep(MS_PER_TICK * 0.000001)

    agent.quit_mission()
    agent.print_finish_data()
    agent.episode_reward = 0
    zombies_alive = NUM_MOBS
    player_life[mission_no - 1] = agent.current_life
    survival_time[mission_no - 1] = agent.survival_time_score
    kills[mission_no - 1] = agent.zombie_kill_score

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

brain.save()
time.sleep(1)
