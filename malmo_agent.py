from __future__ import print_function
from __future__ import division
from builtins import range
import json
import uuid
import malmo.MalmoPython as MalmoPython
import time
from datetime import datetime
import random
from IPython import display

import matplotlib
import torch
from matplotlib import pyplot as plt

MS_PER_TICK = 5

NUM_AGENTS = 1
NUM_MOBS = 1


class Agent:
    def __init__(self):
        self.episode_reward = 0
        self.total_reward = 0
        self.survival_time_score = 0  # Lasted to the end of the mission without dying.
        self.zombie_kill_score = 0  # Good! Help rescue humanity from zombie-kind.
        self.malmo_agent = MalmoPython.AgentHost()
        self.client_pool = MalmoPython.ClientPool()
        self.client_pool.add(MalmoPython.ClientInfo('127.0.0.1', 10000))
        self.running = True
        self.current_life = 20
        self.current_pos = (0, 0)
        self.unresponsive_count = 10
        self.all_zombies_died = False
        self.actions = ["attack 1", "move 1", "move -1", "strafe 1", "strafe -1", "turn 0.3", "turn -0.3"]

    def start_mission(self, mission_no):
        print("Running mission #" + str(mission_no))
        mission = MalmoPython.MissionSpec(self.__get_xml("true" if mission_no == 1 else "false"), True)
        experimentID = str(uuid.uuid4())
        self.__safe_start_mission(mission, MalmoPython.MissionRecordSpec(), 0, experimentID)
        self.__safe_wait_for_start()
        time.sleep(0.05)
        # Make sure no Zombies are spawn
        self.malmo_agent.sendCommand("chat /kill @e[type=!player]")
        # Spawn the Zombies
        self.__spawn_zombies()
        self.malmo_agent.sendCommand("chat /gamerule naturalRegeneration false")
        self.malmo_agent.sendCommand("chat /gamerule doMobLoot false")
        self.malmo_agent.sendCommand("chat /difficulty 1")
        self.unresponsive_count = 10
        self.all_zombies_died = False
        time.sleep(1)

    def is_mission_running(self):
        return self.unresponsive_count > 0 and not self.all_zombies_died

    def play_action(self, action_number):
        action_number = int(action_number)
        action = self.actions[action_number]
        if action == "attack 1":
            self.malmo_agent.sendCommand(action)
            time.sleep(MS_PER_TICK * 0.02)
            self.malmo_agent.sendCommand("attack 0")
        elif action == "turn 0.3" or action == "turn -0.3":
            self.malmo_agent.sendCommand(action)
            time.sleep(MS_PER_TICK * 0.01)
            self.malmo_agent.sendCommand("turn 0")
        elif action == "move 1" or action == "move -1":
            self.malmo_agent.sendCommand(action)
            time.sleep(MS_PER_TICK * 0.01)
            self.malmo_agent.sendCommand("move 0")
        elif action == "strafe 1" or action == "strafe -1":
            self.malmo_agent.sendCommand(action)
            time.sleep(MS_PER_TICK * 0.01)
            self.malmo_agent.sendCommand("strafe 0")

    def quit_mission(self):
        print()
        self.malmo_agent.sendCommand("quit")
        print("All Zombies Died") if self.all_zombies_died else print("Agent Died")
        print("Waiting for mission to end ", end=' ')
        hasEnded = False
        while not hasEnded:
            hasEnded = True  # assume all good
            print(".", end="")
            time.sleep(0.1)
            world_state = self.malmo_agent.getWorldState()
            if world_state.is_mission_running:
                hasEnded = False  # all not good

    def print_finish_data(self):
        print()
        print("=========================================")
        print("Episode Reward:", self.episode_reward)
        print("Total Reward:", self.total_reward)
        print("Player life: ", self.current_life)
        print("Survival time score: ", self.survival_time_score)
        print("Zombie kill score: ", self.zombie_kill_score)
        print("=========================================")
        print()
        time.sleep(0.05)

    def __safe_wait_for_zombies(self):
        while True:
            world_state = self.malmo_agent.getWorldState()

    def __safe_start_mission(self, mission, mission_record, role, expId):
        used_attempts = 0
        max_attempts = 5
        print("Calling startMission for role", role)
        while True:
            try:
                # Attempt start:
                self.malmo_agent.startMission(mission, self.client_pool, mission_record, role, expId)
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
                    print("Other error:", e)
                    print("Waiting will not help here - bailing immediately.")
                    exit(1)
            if used_attempts == max_attempts:
                print("All chances used up - bailing now.")
                exit(1)
        print("startMission called okay.")

    def __safe_wait_for_start(self):
        print("Waiting for the mission to start", end=' ')
        start_flag = False
        start_time = time.time()
        time_out = 120  # Allow a two minute timeout.
        while not start_flag and time.time() - start_time < time_out:
            state = self.malmo_agent.peekWorldState()
            start_flag = state.has_mission_begun
            errors = [e for e in state.errors]
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

    def __spawn_zombies(self):
        for _ in range(NUM_MOBS):
            self.malmo_agent.sendCommand(
                "chat /summon Zombie "
                + str(0)
                + " 202 "
                + str(9)
                + " {HealF:10.0f}"
            )

    def __get_xml(self, reset):
        xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
        <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <About>
            <Summary/>
          </About>
          <ModSettings>
            <MsPerTick>''' + str(MS_PER_TICK) + '''</MsPerTick>
          </ModSettings>
          <ServerSection>
            <ServerInitialConditions>
              <Time>
                <StartTime>13000</StartTime>
              </Time>
            </ServerInitialConditions>
            <ServerHandlers>
              <FlatWorldGenerator forceReset="''' + reset + '''" generatorString="" seed=""/>
              <DrawingDecorator>
                <DrawCuboid x1="-19" y1="200" z1="-19" x2="19" y2="235" z2="19" type="wool" colour="ORANGE"/>
                <DrawCuboid x1="-18" y1="202" z1="-18" x2="18" y2="247" z2="18" type="air"/>
                <DrawBlock x="0" y="226" z="0" type="fence"/>
                <DrawCuboid x1="-19" y1="235" z1="-19" x2="19" y2="255" z2="19" type="wool" colour="ORANGE"/>
              </DrawingDecorator>
            </ServerHandlers>
          </ServerSection>
        '''
        for i in range(NUM_AGENTS):
            xml += '''<AgentSection mode="Adventure">
            <Name>Robot</Name>
            <AgentStart>
              <Placement x="''' + str(0) + '''" y="202" z="''' + str(0) + '''"/>
              <Inventory>
                <InventoryBlock quantity="1" slot="0" type="diamond_sword" />
                <InventoryBlock quantity="1" slot="39" type="iron_helmet" />
                <InventoryBlock quantity="1" slot="38" type="iron_chestplate" />
                <InventoryBlock quantity="1" slot="37" type="iron_leggings" />
                <InventoryBlock quantity="1" slot="36" type="iron_boots" />
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

        if NUM_AGENTS != 1:
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

is_ipython = 'inline' in matplotlib.get_backend()
if is_ipython:
    from IPython import display

plt.ion()

def plot_table(table ,show_result=False):
    is_ipython = 'inline' in matplotlib.get_backend()
    plt.figure(1)
    durations_t = torch.tensor(table, dtype=torch.float)
    if show_result:
        plt.title('Result')
    else:
        plt.clf()
        plt.title('Training...')
    plt.xlabel('Episode')
    plt.ylabel('Duration')
    plt.plot(durations_t.numpy())
    # Take 100 episode averages and plot them too
    if len(durations_t) >= 100:
        means = durations_t.unfold(0, 100, 1).mean(1).view(-1)
        means = torch.cat((torch.zeros(99), means))
        plt.plot(means.numpy())

    plt.pause(0.001)  # pause a bit so that plots are updated
    if is_ipython:
        if not show_result:
            display.display(plt.gcf())
            display.clear_output(wait=True)
        else:
            display.display(plt.gcf())