from __future__ import print_function
from __future__ import division
from malmo_agent import *
from ai import *

agent = Agent()

# brain = Dqn(5, 13, 0.9)

for mission_no in range(1, NUM_MISSIONS+1):
    agent.start_mission(mission_no)
    while agent.is_mission_running():
        agent.observe_state()
        # TODO things

    agent.quit_mission()
    agent.print_finish_data()
