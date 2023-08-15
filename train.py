from __future__ import print_function
from __future__ import division
from malmo_agent import *

agent = Agent()

for mission_no in range(1, NUM_MISSIONS+1):
    agent.start_mission(mission_no)
    unresponsive_count = 10
    time.sleep(0.05)
    all_zombies_died = False
    # if unresponsive_count <= 0 agent has died
    while unresponsive_count > 0 and not all_zombies_died:
        world_state = agent.malmo_agent.getWorldState()
        if world_state.is_mission_running and world_state.number_of_observations_since_last_state > 0:
            unresponsive_count = 10
            ob = json.loads(world_state.observations[-1].text)
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
            if all(d.get('name') != 'Zombie' for d in ob["entities"]):
                all_zombies_died = True
        elif world_state.number_of_observations_since_last_state == 0:
            unresponsive_count -= 1
        if world_state.number_of_rewards_since_last_state > 0:
            for rew in world_state.rewards:
                print("Reward:" + str(rew.getValue()))
        time.sleep(0.05)
    print()

    agent.malmo_agent.sendCommand("quit")
    print("All Zombies Died") if all_zombies_died else print("Agent Died")
    print("Waiting for mission to end ", end=' ')
    hasEnded = False
    while not hasEnded:
        hasEnded = True  # assume all good
        print(".", end="")
        time.sleep(0.1)
        world_state = agent.malmo_agent.getWorldState()
        if world_state.is_mission_running:
            hasEnded = False  # all not good
    print()
    print("=========================================")
    print("Player life: ", agent.current_life)
    print("Survival time score: ", agent.survival_time_score)
    print("Zombie kill score: ", agent.zombie_kill_score)
    print("=========================================")
    print()
    time.sleep(0.05)
