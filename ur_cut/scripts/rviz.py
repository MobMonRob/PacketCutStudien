#!/usr/bin/env python

import sys
import copy
import rospy
import moveit_commander
import moveit_msgs.msg
import geometry_msgs.msg
from math import pi
from std_msgs.msg import String
import actionlib
from control_msgs.msg import *
from trajectory_msgs.msg import *
import numpy as numpy
import time
from pyquaternion import *
from geometry_msgs.msg import Vector3





class rvizCollision(object):
    def __init__(self, robot, scene, group):
        super(rvizCollision, self).__init__()

        ## Getting Basic Information
        ## ^^^^^^^^^^^^^^^^^^^^^^^^^
        # We can get the name of the reference frame for this robot:
        planning_frame = group.get_planning_frame()

        # We can also print the name of the end-effector link for this group:
        eef_link = group.get_end_effector_link()

        # We can get a list of all the groups in the robot:
        group_names = robot.get_group_names()

        # Misc variables
        self.box_name = ''
        self.robot = robot
        self.scene = scene
        self.group = group
        self.planning_frame = planning_frame
        self.eef_link = eef_link
        self.group_names = group_names

    ## Ensuring Collision Updates Are Receieved
    ## ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    def wait_for_state_update(self, box_is_known=False, box_is_attached=False, timeout=4):

        start = rospy.get_time()
        seconds = rospy.get_time()
        while (seconds - start < timeout) and not rospy.is_shutdown():
            # Test if the box is in attached objects
            attached_objects = self.scene.get_attached_objects([self.box_name])
            is_attached = len(attached_objects.keys()) > 0

            # Test if the box is in the scene.
            # Note that attaching the box will remove it from known_objects
            is_known = self.box_name in self.scene.get_known_object_names()

            # Test if we are in the expected state
            if (box_is_attached == is_attached) and (box_is_known == is_known):
                return True

            # Sleep so that we give other threads time on the processor
            rospy.sleep(0.1)
            seconds = rospy.get_time()

            # If we exited the while loop without returning then we timed out
        return False


    def addGround(self):
        return self.add_box("groundPlate", position=(0, 0, -0.01), box_size=(2, 2, 0.01), timeout=10)

    def addRoof(self):
        return self.add_box("roofPlate", position=(0, 0, 0.9), box_size=(2, 2, 0.01), timeout=10)

    def addBackWall(self):
        return self.add_box("backWall", position=(0, -0.5, 0.45), box_size=(2, 0.01, 0.9), timeout=10)

    def addCutStation(self):
        return self.add_box("cutStation", position=(0, 0.7, 0.4), box_size=(2, 1, 0.01), timeout=10)

    def addCutter(self):
        return self.add_box("cutter", position=(0, 0.8, 0.8), box_size=(2, 1, 0.01), timeout=10)
        

    def removeGround(self):
        return self.remove_box("groundPlate")

    def removeRoof(self):
        return self.remove_box("roofPlate")

    def removeBackWall(self):
        return self.remove_box("backWall")

    def removeCutStation(self):
        return self.remove_box("cutStation")

    def removeCutter(self):
        return self.remove_box("cutter")


    def addCollisionObjects(self):
        self.addGround()
        self.addBackWall()
        self.addRoof()
        self.addCutStation()
        self.addCutter()

    def removeCollisionObjects(self):
        self.removeGround()
        self.removeBackWall()
        self.removeRoof()
        self.removeCutStation()
        self.removeCutter()


    def add_box(self, name = "box", position = (0, 0, 0), box_size = (1, 1, 1), timeout=4):
        ## Adding Objects to the Planning Scene
        ## ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        box_pose = geometry_msgs.msg.PoseStamped()
        box_pose.header.frame_id = self.robot.get_planning_frame()
        box_pose.pose.orientation.w = 1.0
        box_pose.pose.position.x = position[0]
        box_pose.pose.position.y = position[1]
        box_pose.pose.position.z = position[2]
        self.box_name = name
        self.scene.add_box(self.box_name, box_pose, box_size)

        return self.wait_for_state_update(box_is_known=True, timeout=timeout)



    def attach_box(self, timeout=4):
        # Copy class variables to local variables to make the web tutorials more clear.
        # In practice, you should use the class variables directly unless you have a good
        # reason not to.
        box_name = self.box_name
        robot = self.robot
        scene = self.scene
        eef_link = self.eef_link
        group_names = self.group_names

        ## BEGIN_SUB_TUTORIAL attach_object
        ##
        ## Attaching Objects to the Robot
        ## ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ## Next, we will attach the box to the Panda wrist. Manipulating objects requires the
        ## robot be able to touch them without the planning scene reporting the contact as a
        ## collision. By adding link names to the ``touch_links`` array, we are telling the
        ## planning scene to ignore collisions between those links and the box. For the Panda
        ## robot, we set ``grasping_group = 'hand'``. If you are using a different robot,
        ## you should change this value to the name of your end effector group name.
        grasping_group = 'manipulator'
        touch_links = robot.get_link_names(group=grasping_group)
        scene.attach_box(eef_link, box_name, touch_links=touch_links)
        ## END_SUB_TUTORIAL

        # We wait for the planning scene to update.
        return self.wait_for_state_update(box_is_attached=True, box_is_known=False, timeout=timeout)

    def detach_box(self):
        # Copy class variables to local variables to make the web tutorials more clear.
        # In practice, you should use the class variables directly unless you have a good
        # reason not to.
        box_name = self.box_name
        scene = self.scene
        eef_link = self.eef_link

        ## BEGIN_SUB_TUTORIAL detach_object
        ##
        ## Detaching Objects from the Robot
        ## ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ## We can also detach and remove the object from the planning scene:
        scene.remove_attached_object(eef_link, name=box_name)
        ## END_SUB_TUTORIAL

        # We wait for the planning scene to update.
        return self.wait_for_state_update(box_is_known=True, box_is_attached=False)

    def remove_box(self, name):
        ## BEGIN_SUB_TUTORIAL remove_object
        ##
        ## Removing Objects from the Planning Scene
        ## ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ## We can remove the box from the world.
        ## Box must be detached before remove
        self.box_name = name
        self.scene.remove_world_object(self.box_name)

        # We wait for the planning scene to update.
        return self.wait_for_state_update(box_is_attached=False, box_is_known=False)
    pass