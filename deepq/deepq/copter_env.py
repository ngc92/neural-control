"""
Classic cart-pole system implemented by Rich Sutton et al.
Copied from https://webdocs.cs.ualberta.ca/~sutton/book/code/pole.c
"""

import logging
import math
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import math
from collections import deque

logger = logging.getLogger(__name__)

class CopterParams(object):
    def __init__(self):
        self.l = 0.31    # Arm length
        self.b = 5.324e-5    # Thrust coefficient
        self.d = 8.721e-7    # Drag coefficient
        self.m = 0.723    # Mass
        self.I = np.array([[8.678e-3,0,0],[0,8.678e-3,0],[0,0,3.217e-2]]) # Inertia
        self.J = 7.321e-5   # Rotor inertia


class CopterStatus(object):
    def __init__(self):
        self.position = np.array([0.0, 0, 0])
        self.velocity = np.array([0.0, 0, 0])
        self.attitude = np.array([0.0, 0, 0])
        self.angular_velocity = np.array([0.0, 0, 0])


class CopterEnv(gym.Env):
    metadata = {
        'render.modes': [],
        'video.frames_per_second' : 50
    }

    def __init__(self):
        high = np.array([np.inf]*12)
        
        self.copterparams = CopterParams()
        self.observation_space = spaces.Box(-high, high)
        self.action_space = spaces.Box(-1, 1, (4,))

        self.threshold    = 5 * math.pi / 180
        self.fail_threshold = 20 * math.pi / 180

        self._seed()
        self.viewer = None
        self.state  = None

        self.steps_beyond_done = None

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def _step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
        
        control = np.array(action) * 0.05
        dt      = 0.1

        ap, aa = self._calc_acceleration(control)
        quad = self.copterstatus
        quad.position += quad.velocity * dt + 0.5 * ap * dt * dt
        quad.velocity += ap * dt

        quad.attitude += quad.angular_velocity * dt + 0.5 * aa * dt * dt
        quad.angular_velocity += aa * dt

        # TODO currently, target attitude is 0
        err = np.max(np.abs(quad.attitude))

        done = bool(self._steps > 300)

        reward = 0.2
        if err < self.threshold:
            rerr = err / self.threshold
            reward += 1.0 - rerr

        if err > self.fail_threshold:
            reward = -10
            done = True

        return self._get_state(), reward, done, {}

    def _calc_acceleration(self, control):
        b = self.copterparams.b
        I = self.copterparams.I
        l = self.copterparams.l
        m = self.copterparams.m
        J = self.copterparams.J
        d = self.copterparams.d
        g = 9.81

        attitude = self.copterstatus.attitude
        avel     = self.copterstatus.angular_velocity
        roll     = attitude[0]
        pitch    = attitude[1]
        yaw      = attitude[2]

        droll    = avel[0]
        dpitch   = avel[1]
        dyaw     = avel[2]

        # damn, have to calculate this
        U1s = control[0] / b
        U2s = control[1] / b
        U3s = control[2] / b
        U4s = control[3] / d
        U13 = (U1s + U4s) / 2
        U24 = (U1s - U4s) / 2
        O1 = math.sqrt(abs(U13 + U3s)/2)
        O3 = math.sqrt(abs(U13 - U3s)/2)
        O2 = math.sqrt(abs(U24 - U2s)/2)
        O4 = math.sqrt(abs(U24 + U2s)/2)
        Or = -O1 + O2 - O3 + O4

        a0  = control[0] * ( math.cos(roll)*math.sin(pitch)*math.cos(yaw) + math.sin(roll)*math.sin(yaw) ) / m
        a1  = control[0] * ( math.cos(roll)*math.sin(pitch)*math.sin(yaw) + math.sin(roll)*math.cos(yaw) ) / m
        a2  = control[0] * ( math.cos(roll)*math.cos(pitch) ) / m - g

        
        aroll  = (dpitch * dyaw * (I[1, 1] - I[2, 2]) + dpitch * Or * J + control[1] * l) / I[0, 0]
        apitch = (droll  * dyaw * (I[2, 2] - I[0, 0]) + droll * Or * J + control[2] * l) / I[1, 1]
        ayaw   = (droll  * dyaw * (I[0, 0] - I[1, 1]) + control[3] * l) / I[2, 2]
        return np.array([a0, a1, a2]), np.array([aroll, apitch, ayaw])

    def _reset(self):
        self.copterstatus = CopterStatus()
        # start in resting position, but with low angular velocity
        self.copterstatus.angular_velocity = self.np_random.uniform(low=-0.1, high=0.1, size=(3,))
        self._steps = 0

        self.steps_beyond_done = None
        return self._get_state()

    def _get_state(self):
        s = self.copterstatus
        # currently, we ignore position and velocity!
        return np.concatenate([s.attitude, s.angular_velocity])

    def _render(self, mode='human', close=False):
        # currently not implemented
        return
