from __future__ import print_function
from __future__ import division
# ------------------------------------------------------------------------------------------------
# Copyright (c) 2016 Microsoft Corporation
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------

# Test of multi-agent missions - runs a number of agents in a shared environment.

from builtins import range
from past.utils import old_div
import malmo.MalmoPython as MalmoPython
import json
import numpy as np
import logging
import math
import os
import random
import sys
import time
import re
import uuid
from collections import namedtuple
from operator import add

EntityInfo = namedtuple('EntityInfo', 'x, y, z, name')

# Create one agent host for parsing:
agent_hosts = [MalmoPython.AgentHost()]

# Parse the command-line options:
agent_hosts[0].addOptionalFlag( "debug,d", "Display debug information.")
agent_hosts[0].addOptionalIntArgument("agents,n", "Number of agents to use, including observer.", 4)

try:
    agent_hosts[0].parse( sys.argv )
except RuntimeError as e:
    print('ERROR:',e)
    print(agent_hosts[0].getUsage())
    exit(1)
if agent_hosts[0].receivedArgument("help"):
    print(agent_hosts[0].getUsage())
    exit(0)

DEBUG = agent_hosts[0].receivedArgument("debug")
INTEGRATION_TEST_MODE = agent_hosts[0].receivedArgument("test")
agents_requested = agent_hosts[0].getIntArgument("agents")
NUM_AGENTS = max(1, agents_requested - 1) # Will be NUM_AGENTS robots running around, plus one static observer.
NUM_MOBS = NUM_AGENTS * 4

# Create the rest of the agent hosts - one for each robot, plus one to give a bird's-eye view:
agent_hosts += [MalmoPython.AgentHost() for x in range(1, NUM_AGENTS + 1) ]

# Set up debug output:
for ah in agent_hosts:
    ah.setDebugOutput(DEBUG)    # Turn client-pool connection messages on/off.

if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
else:
    import functools
    print = functools.partial(print, flush=True)

def agentName(i):
    return "Robot#" + str(i + 1)

def safeStartMission(agent_host, my_mission, my_client_pool, my_mission_record, role, expId):
    used_attempts = 0
    max_attempts = 5
    print("Calling startMission for role", role)
    while True:
        try:
            # Attempt start:
            agent_host.startMission(my_mission, my_client_pool, my_mission_record, role, expId)
            break
        except MalmoPython.MissionException as e:
            errorCode = e.details.errorCode
            if errorCode == MalmoPython.MissionErrorCode.MISSION_SERVER_WARMING_UP:
                print("Server not quite ready yet - waiting...")
                time.sleep(2)
            elif errorCode == MalmoPython.MissionErrorCode.MISSION_INSUFFICIENT_CLIENTS_AVAILABLE:
                print("Not enough available Minecraft instances running.")
                used_attempts += 1
                if used_attempts < max_attempts:
                    print("Will wait in case they are starting up.", max_attempts - used_attempts, "attempts left.")
                    time.sleep(2)
            elif errorCode == MalmoPython.MissionErrorCode.MISSION_SERVER_NOT_FOUND:
                print("Server not found - has the mission with role 0 been started yet?")
                used_attempts += 1
                if used_attempts < max_attempts:
                    print("Will wait and retry.", max_attempts - used_attempts, "attempts left.")
                    time.sleep(2)
            else:
                print("Other error:", e.message)
                print("Waiting will not help here - bailing immediately.")
                exit(1)
        if used_attempts == max_attempts:
            print("All chances used up - bailing now.")
            exit(1)
    print("startMission called okay.")

def safeWaitForStart(agent_hosts):
    print("Waiting for the mission to start", end=' ')
    start_flags = [False for a in agent_hosts]
    start_time = time.time()
    time_out = 120  # Allow a two minute timeout.
    while not all(start_flags) and time.time() - start_time < time_out:
        states = [a.peekWorldState() for a in agent_hosts]
        start_flags = [w.has_mission_begun for w in states]
        errors = [e for w in states for e in w.errors]
        if len(errors) > 0:
            print("Errors waiting for mission start:")
            for e in errors:
                print(e.text)
            print("Bailing now.")
            exit(1)
        time.sleep(0.1)
        print(".", end=' ')
    if time.time() - start_time >= time_out:
        print("Timed out while waiting for mission to start - bailing.")
        exit(1)
    print()
    print("Mission has started.")

def drawMobs():
    xml = ""
    for i in range(NUM_MOBS):
        x = str(random.randint(-17,17))
        z = str(random.randint(-17,17))
        xml += '<DrawEntity x="' + x + '" y="202" z="' + z + '" type="Zombie"/>'
    return xml

def getXML(reset):
    xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
    <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <About>
        <Summary/>
      </About>
      <ModSettings>
        <MsPerTick>50</MsPerTick>
      </ModSettings>
      <ServerSection>
        <ServerInitialConditions>
          <Time>
            <StartTime>13000</StartTime>
          </Time>
        </ServerInitialConditions>
        <ServerHandlers>
          <FlatWorldGenerator forceReset="'''+reset+'''" generatorString="" seed=""/>
          <DrawingDecorator>
            <DrawCuboid x1="-19" y1="200" z1="-19" x2="19" y2="235" z2="19" type="wool"/>
            <DrawCuboid x1="-18" y1="202" z1="-18" x2="18" y2="247" z2="18" type="air"/>
            <DrawBlock x="0" y="226" z="0" type="fence"/>
            <DrawCuboid x1="-19" y1="235" z1="-19" x2="19" y2="255" z2="19" type="wool"/>
          </DrawingDecorator>
          <ServerQuitFromTimeUp description="" timeLimitMs="40000"/>
        </ServerHandlers>
      </ServerSection>
    '''
    for i in range(NUM_AGENTS):
        xml += '''<AgentSection mode="Survival">
        <Name>''' + agentName(i) + '''</Name>
        <AgentStart>
          <Placement x="''' + str(random.randint(-17,17)) + '''" y="204" z="''' + str(random.randint(-17,17)) + '''"/>
          <Inventory>
            <InventoryObject type="diamond_sword" slot="0" quantity="1"/>
          </Inventory>
        </AgentStart>
        <AgentHandlers>
          <ContinuousMovementCommands turnSpeedDegs="360"/>
          <ChatCommands/>
          <MissionQuitCommands/>
            <RewardForDamagingEntity>
                <Mob reward="1" type="Zombie"/>
            </RewardForDamagingEntity>
          <ObservationFromNearbyEntities>
            <Range name="entities" xrange="40" yrange="2" zrange="40"/>
          </ObservationFromNearbyEntities>
          <ObservationFromRay/>
          <ObservationFromFullStats/>
        </AgentHandlers>
      </AgentSection>'''

    xml += '''<AgentSection mode="Creative">
        <Name>TheWatcher</Name>
        <AgentStart>
          <Placement x="0.5" y="228" z="0.5" pitch="90"/>
        </AgentStart>
        <AgentHandlers>
          <ContinuousMovementCommands turnSpeedDegs="360"/>
          <MissionQuitCommands/>
          <VideoProducer>
            <Width>640</Width>
            <Height>640</Height>
          </VideoProducer>
        </AgentHandlers>
      </AgentSection>'''

    xml += '</Mission>'
    return xml

client_pool = MalmoPython.ClientPool()
for x in range(10000, 10000 + NUM_AGENTS + 1):
    client_pool.add( MalmoPython.ClientInfo('127.0.0.1', x) )

# Keep score of how our robots are doing:
survival_scores = [0 for x in range(NUM_AGENTS)]    # Lasted to the end of the mission without dying.
zombie_kill_scores = [0 for x in range(NUM_AGENTS)] # Good! Help rescue humanity from zombie-kind.
player_kill_scores = [0 for x in range(NUM_AGENTS)] # Bad! Don't kill the other players!

num_missions = 5 if INTEGRATION_TEST_MODE else 30000
for mission_no in range(1, num_missions+1):
    print("Running mission #" + str(mission_no))
    my_mission = MalmoPython.MissionSpec(getXML("true" if mission_no == 1 else "false"), True)
    experimentID = str(uuid.uuid4())
    for i in range(len(agent_hosts)):
        safeStartMission(agent_hosts[i], my_mission, client_pool, MalmoPython.MissionRecordSpec(), i, experimentID)

    safeWaitForStart(agent_hosts)
    time.sleep(1)
    running = True
    current_life = [20 for x in range(NUM_AGENTS)]
    # When an agent is killed, it stops getting observations etc. Track this, so we know when to bail.
    unresponsive_count = [10 for x in range(NUM_AGENTS)]
    num_responsive_agents = lambda: sum([urc > 0 for urc in unresponsive_count])

    for _ in range(NUM_MOBS):
        agent_hosts[0].sendCommand(
            "chat /summon Zombie "
            + str(np.random.randint(-18, 18))
            + " 202 "
            + str(np.random.randint(-18, 18))
            + " {HealF:10.0f}"
        )

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
                if "Life" in ob:
                    life = ob[u'Life']
                    if life != current_life[i]:
                        current_life[i] = life
                if "PlayersKilled" in ob:
                    player_kill_scores[i] = -ob[u'PlayersKilled']
                if "MobsKilled" in ob:
                    all_zombies_killed = ob[u'MobsKilled']
                    curr_zombies_killed = abs(zombie_kill_scores[i] - all_zombies_killed)
                    zombie_kill_scores[i] = all_zombies_killed
                    if curr_zombies_killed != 0:
                        # Every time a zombie is killed we spawn it back and +1 to make it more difficult
                        for _ in range(curr_zombies_killed + 1):
                            ah.sendCommand(
                                "chat /summon Zombie "
                                + str(np.random.randint(-18, 18))
                                + " 202 "
                                + str(np.random.randint(-18, 18))
                                + " {HealF:10.0f}"
                            )
            elif world_state.number_of_observations_since_last_state == 0:
                unresponsive_count[i] -= 1
            if world_state.number_of_rewards_since_last_state > 0:
                for rew in world_state.rewards:
                    print("Reward:" + str(rew.getValue()))

        time.sleep(0.05)

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
    winner_survival = survival_scores.index(max(survival_scores))
    winner_zombies = zombie_kill_scores.index(max(zombie_kill_scores))
    winner_players = player_kill_scores.index(max(player_kill_scores))
    win_counts[winner_survival] += 1
    win_counts[winner_zombies] += 1
    win_counts[winner_players] += 1

    print()
    print("=========================================")
    print("Survival scores: ", survival_scores, "Winner: ", agentName(winner_survival))
    print("Zombie kill scores: ", zombie_kill_scores, "Winner: ", agentName(winner_zombies))
    print("Player kill scores: ", player_kill_scores, "Winner: ", agentName(winner_players))
    print("=========================================")
    print("CURRENT OVERALL WINNER: " + agentName(win_counts.index(max(win_counts))))
    print()

    time.sleep(2)
