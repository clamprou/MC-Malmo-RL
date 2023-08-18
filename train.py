from __future__ import print_function
from __future__ import division
from malmo_agent import *
from ai import *

NUM_MISSIONS = 200

agent = Agent()

brain = Dqn(1, 11, 0.9)
brain.load()
time.sleep(1)
for mission_no in range(1, NUM_MISSIONS+1):
    agent.start_mission(mission_no)
    while agent.is_mission_running():
        world_state = agent.malmo_agent.getWorldState()
        if world_state.number_of_observations_since_last_state > 0:  # Agent is alive
            agent.unresponsive_count = 10
            ob = json.loads(world_state.observations[-1].text)
            if all(d.get('name') != 'Zombie' for d in ob["entities"]):
                agent.all_zombies_died = True

            # Normalize observed data
            if "entities" in ob:
                pass
            if u'LineOfSight' in ob:
                los = ob[u'LineOfSight']
                if los[u'hitType'] == "entity" and los[u'inRange'] and los[u'type'] == "Zombie":
                    agent.zombie_los = 1
                    agent.last_reward += 0.5
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
            action = brain.update(agent.last_reward, [agent.zombie_los])
            agent.malmo_agent.sendCommand(agent.actions[action])
            agent.last_reward = 0
            agent.zombie_los = 0
        elif world_state.number_of_observations_since_last_state == 0:
            agent.unresponsive_count -= 1
        if world_state.number_of_rewards_since_last_state > 0:
            for rew in world_state.rewards:
                agent.last_reward = rew.getValue() + 1
                print("Reward:" + str(rew.getValue()))
        time.sleep(0.000001)

    agent.quit_mission()
    agent.print_finish_data()

brain.save()
time.sleep(1)
