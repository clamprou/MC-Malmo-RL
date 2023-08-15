from __future__ import print_function
from __future__ import division
from builtins import range
import malmo.MalmoPython as MalmoPython
import json
import time
from malmo_agent import getXML, safeStartMission, safeWaitForStart, spawnZombies
import uuid

MS_PERTICK = 50
NUM_MISSIONS = 5
NUM_AGENTS = 1
NUM_MOBS = 3

agent = MalmoPython.AgentHost()
client_pool = MalmoPython.ClientPool()
client_pool.add(MalmoPython.ClientInfo('127.0.0.1', 10000))

# Keep score of how our robot is doing:
survival_time_score = 0    # Lasted to the end of the mission without dying.
zombie_kill_score = 0  # Good! Help rescue humanity from zombie-kind.

for mission_no in range(1, NUM_MISSIONS+1):
    print("Running mission #" + str(mission_no))
    my_mission = MalmoPython.MissionSpec(getXML(NUM_AGENTS, "true" if mission_no == 1 else "false", NUM_AGENTS, str(MS_PERTICK)), True)
    experimentID = str(uuid.uuid4())
    safeStartMission(agent, my_mission, client_pool, MalmoPython.MissionRecordSpec(), 0, experimentID)
    safeWaitForStart(agent)
    time.sleep(1)
    running = True
    current_life = 20
    current_pos = (0, 0)
    # When an agent is killed, it stops getting observations etc. Track this, so we know when to bail.
    unresponsive_count = 10
    spawnZombies(NUM_MOBS, agent)
    agent.sendCommand("chat /gamerule naturalRegeneration false")
    agent.sendCommand("chat /gamerule doMobLoot false")
    agent.sendCommand("chat /difficulty 1")

    timed_out = False
    while unresponsive_count > 0 and not timed_out:
        world_state = agent.getWorldState()
        if world_state.is_mission_running == False:
            timed_out = True
        if world_state.is_mission_running and world_state.number_of_observations_since_last_state > 0:
            unresponsive_count = 10
            ob = json.loads(world_state.observations[-1].text)
            if ob[u'TimeAlive'] != 0:
                survival_time_score = ob[u'TimeAlive']
            if "Life" in ob:
                life = ob[u'Life']
                if life != current_life:
                    current_life = life
            if "MobsKilled" in ob:
                zombie_kill_score = ob[u'MobsKilled']
            if "XPos" in ob and "ZPos" in ob:
                current_pos = (ob[u'XPos'], ob[u'ZPos'])
            if ob["WorldTime"] > 13100 and (not"entities" in ob or all(d.get('name') != 'Zombie' for d in ob["entities"])):
                timed_out = True
                # TODO end mission
        elif world_state.number_of_observations_since_last_state == 0:
            unresponsive_count -= 1
        if world_state.number_of_rewards_since_last_state > 0:
            for rew in world_state.rewards:
                print("Reward:" + str(rew.getValue()))
        time.sleep(0.05)
    print()
    if not timed_out:
        # All agents except the watcher have died.
        agent.sendCommand("quit")
    else:
        # TODO not sure if its ok to quit here
        agent.sendCommand("quit")

    print("Waiting for mission to end ", end=' ')
    hasEnded = False
    while not hasEnded:
        hasEnded = True  # assume all good
        print(".", end="")
        time.sleep(0.1)
        world_state = agent.getWorldState()
        if world_state.is_mission_running:
            hasEnded = False  # all not good
    print()
    print("=========================================")
    print("Player life: ", current_life)
    print("Survival time score: ", survival_time_score)
    print("Zombie kill score: ", zombie_kill_score)
    print("=========================================")
    print()
    time.sleep(2)
