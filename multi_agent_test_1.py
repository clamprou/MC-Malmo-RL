from __future__ import print_function
from __future__ import division
from builtins import range
import malmo.MalmoPython as MalmoPython
import json
import os
import sys
import time
from Agent import getXML, safeStartMission, safeWaitForStart, agentName, spawnZombies, parseCommandOptions
import uuid
from collections import namedtuple

EntityInfo = namedtuple('EntityInfo', 'x, y, z, name')

# TODO msPerTick change dynamically
msPerTick = 50

# Create one agent host for parsing:
agent_hosts = [MalmoPython.AgentHost()]
parseCommandOptions(agent_hosts[0])

DEBUG = agent_hosts[0].receivedArgument("debug")
INTEGRATION_TEST_MODE = agent_hosts[0].receivedArgument("test")
agents_requested = agent_hosts[0].getIntArgument("agents")
NUM_AGENTS = max(1, agents_requested - 1) # Will be NUM_AGENTS robots running around, plus one static observer.
NUM_MOBS = NUM_AGENTS * 5

# Create the rest of the agent hosts - one for each robot, plus one to give a bird's-eye view:
if agents_requested == 1:
    agent_hosts += [MalmoPython.AgentHost() for x in range(1, NUM_AGENTS)]
else:
    agent_hosts += [MalmoPython.AgentHost() for x in range(1, NUM_AGENTS + 1)]
# Set up debug output:
for ah in agent_hosts:
    ah.setDebugOutput(DEBUG)    # Turn client-pool connection messages on/off.

if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
else:
    import functools
    print = functools.partial(print, flush=True)

client_pool = MalmoPython.ClientPool()
if agents_requested == 1:
    for x in range(10000, 10000 + NUM_AGENTS):
        client_pool.add(MalmoPython.ClientInfo('127.0.0.1', x))
else:
    for x in range(10000, 10000 + NUM_AGENTS + 1):
        client_pool.add(MalmoPython.ClientInfo('127.0.0.1', x))

# Keep score of how our robots are doing:
survival_scores = [0 for x in range(NUM_AGENTS)]    # Lasted to the end of the mission without dying.
survival_time_scores = [0 for x in range(NUM_AGENTS)]    # Lasted to the end of the mission without dying.
zombie_kill_scores = [0 for x in range(NUM_AGENTS)] # Good! Help rescue humanity from zombie-kind.
player_kill_scores = [0 for x in range(NUM_AGENTS)] # Bad! Don't kill the other players!

num_missions = 5 if INTEGRATION_TEST_MODE else 30000
for mission_no in range(1, num_missions+1):
    print("Running mission #" + str(mission_no))
    my_mission = MalmoPython.MissionSpec(getXML(NUM_AGENTS, "false", agents_requested, str(msPerTick)), True)
    experimentID = str(uuid.uuid4())
    for i in range(len(agent_hosts)):
        safeStartMission(agent_hosts[i], my_mission, client_pool, MalmoPython.MissionRecordSpec(), i, experimentID)

    safeWaitForStart(agent_hosts)
    time.sleep(1)
    running = True
    current_life = [20 for x in range(NUM_AGENTS)]
    current_pos = [(0,0) for x in range(NUM_AGENTS)]
    # When an agent is killed, it stops getting observations etc. Track this, so we know when to bail.
    unresponsive_count = [10 for x in range(NUM_AGENTS)]
    num_responsive_agents = lambda: sum([urc > 0 for urc in unresponsive_count])

    spawnZombies(NUM_MOBS, agent_hosts[0])
    agent_hosts[0].sendCommand("chat /gamerule naturalRegeneration false")
    agent_hosts[0].sendCommand("chat /difficulty 1")

    timed_out = False
    while num_responsive_agents() > 0 and not timed_out:
        for i in range(NUM_AGENTS):
            ah = agent_hosts[i]
            world_state = ah.getWorldState()
            if world_state.is_mission_running == False:
                timed_out = True
            if world_state.is_mission_running and world_state.number_of_observations_since_last_state > 0:
                unresponsive_count[i] = 10
                ob = json.loads(world_state.observations[-1].text)
                if ob[u'TimeAlive'] != 0:
                    survival_time_scores[i] = ob[u'TimeAlive']
                if "Life" in ob:
                    life = ob[u'Life']
                    if life != current_life[i]:
                        current_life[i] = life
                if "PlayersKilled" in ob:
                    player_kill_scores[i] = -ob[u'PlayersKilled']
                if "MobsKilled" in ob:
                    zombie_kill_scores[i] = ob[u'MobsKilled']
                    # curr_zombies_killed = abs(zombie_kill_scores[i] - all_zombies_killed)
                    # zombie_kill_scores[i] = all_zombies_killed
                    # if curr_zombies_killed != 0:
                    #     # Every time a zombie is killed we spawn it back
                    #     spawnZombies(curr_zombies_killed, agent_hosts[0])
                if "XPos" in ob and "ZPos" in ob:
                    current_pos[i] = (ob[u'XPos'], ob[u'ZPos'])
            elif world_state.number_of_observations_since_last_state == 0:
                unresponsive_count[i] -= 1
            if world_state.number_of_rewards_since_last_state > 0:
                for rew in world_state.rewards:
                    print("Reward:" + str(rew.getValue()))

        time.sleep(0.05)
    print()
    if not timed_out:
        # All agents except the watcher have died.
        agent_hosts[-1].sendCommand("quit")
    else:
        # We timed out. Bonus score to any agents that survived!
        for i in range(NUM_AGENTS):
            if unresponsive_count[i] > 0:
                print("SURVIVOR: " + agentName(i))
                survival_scores[i] += 1

    print("Waiting for mission to end ", end=' ')
    # Mission should have ended already, but we want to wait until all the various agent hosts
    # have had a chance to respond to their mission ended message.
    hasEnded = False
    while not hasEnded:
        hasEnded = True  # assume all good
        print(".", end="")
        time.sleep(0.1)
        for ah in agent_hosts:
            world_state = ah.getWorldState()
            if world_state.is_mission_running:
                hasEnded = False  # all not good

    win_counts = [0 for robot in range(NUM_AGENTS)]
    winner_survival = survival_time_scores.index(max(survival_time_scores))
    winner_zombies = zombie_kill_scores.index(max(zombie_kill_scores))
    winner_players = player_kill_scores.index(max(player_kill_scores))
    win_counts[winner_survival] += 1
    win_counts[winner_zombies] += 1
    win_counts[winner_players] += 1

    print()
    print("=========================================")
    print("Survival time scores: ", survival_time_scores, "Winner: ", agentName(winner_survival))
    print("Zombie kill scores: ", zombie_kill_scores, "Winner: ", agentName(winner_zombies))
    print("Player kill scores: ", player_kill_scores, "Winner: ", agentName(winner_players))
    print("=========================================")
    print("CURRENT OVERALL WINNER: " + agentName(win_counts.index(max(win_counts))))
    print()

    time.sleep(2)
