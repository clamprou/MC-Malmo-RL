import os
import sys
import malmo.MalmoPython as MalmoPython
import time
import random
import numpy as np


def parseCommandOptions(agent):
    agent.addOptionalFlag( "debug,d", "Display debug information.")
    agent.addOptionalIntArgument("agents,n", "Number of agents to use, including observer.", 4)
    try:
        agent.parse( sys.argv )
    except RuntimeError as e:
        print('ERROR:',e)
        print(agent.getUsage())
        exit(1)
    if agent.receivedArgument("help"):
        print(agent.getUsage())
        exit(0)

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
                print("Other error:", e)
                print("Waiting will not help here - bailing immediately.")
                exit(1)
        if used_attempts == max_attempts:
            print("All chances used up - bailing now.")
            exit(1)
    print("startMission called okay.")

def safeWaitForStart(agent_host):
    print("Waiting for the mission to start", end=' ')
    start_flag = False
    start_time = time.time()
    time_out = 120  # Allow a two minute timeout.
    while not start_flag and time.time() - start_time < time_out:
        state = agent_host.peekWorldState()
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

def spawnZombies(mobs, agent):
    for _ in range(mobs):
        agent.sendCommand(
            "chat /summon Zombie "
            + str(0)
            + " 202 "
            + str(9)
            + " {HealF:10.0f}"
        )

def getXML(agents, reset, requested, ms_pertick):
    xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
    <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <About>
        <Summary/>
      </About>
      <ModSettings>
        <ms_pertick>'''+ms_pertick+'''</ms_pertick>
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
            <DrawCuboid x1="-19" y1="200" z1="-19" x2="19" y2="235" z2="19" type="wool" colour="ORANGE"/>
            <DrawCuboid x1="-18" y1="202" z1="-18" x2="18" y2="247" z2="18" type="air"/>
            <DrawBlock x="0" y="226" z="0" type="fence"/>
            <DrawCuboid x1="-19" y1="235" z1="-19" x2="19" y2="255" z2="19" type="wool" colour="ORANGE"/>
          </DrawingDecorator>
          <ServerQuitFromTimeUp description="" timeLimitMs="50000"/>
        </ServerHandlers>
      </ServerSection>
    '''
    for i in range(agents):
        xml += '''<AgentSection mode="Survival">
        <Name>''' + agentName(i) + '''</Name>
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
            <VideoProducer want_depth="false">
               <Width>800</Width>
               <Height>600</Height>
            </VideoProducer>
          <ObservationFromNearbyEntities>
            <Range name="entities" xrange="40" yrange="2" zrange="40"/>
          </ObservationFromNearbyEntities>
          <ObservationFromRay/>
          <ObservationFromFullStats/>
        </AgentHandlers>
      </AgentSection>'''

    if requested != 1:
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