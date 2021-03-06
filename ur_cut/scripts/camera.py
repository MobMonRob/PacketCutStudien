#!/usr/bin/env python

import roslib
import rospy
import time

from sensor_msgs.msg import PointCloud2
import sensor_msgs.point_cloud2 as pc2

class Camera(object):
    def __init__(self):
        super(Camera, self).__init__()

        self.newData = False
        return

    def callback(self, msg):  
        self.pointCloud = msg
        self.newData = True
        return

# Call this Method to get the distance to an object infront of the Camera
    def getDistance(self):
        camera_node = rospy.Subscriber("/royale_camera_driver/point_cloud", PointCloud2, self.callback)
        
        # Wait till callback delivered new data
        while self.newData == False:
            # Do nothing
            pass

        self.newData = False

        x, y, z = self.searchForDistanceInPointCloud()
        camera_node.unregister()
        return z
    
    def searchForDistanceInPointCloud(self):
        
        # Distance is not searched for all points, only in the middle of the image
        # Create 2D Array with points to search distance for
        midpoint_x = (95,96,97,98,99,100,101,102,103,104)
        midpoint_y = (80,81,82,83,84,85,86,87,88,89)
        
        for mx in midpoint_x:
            for my in midpoint_y:
                midpoint = (mx, my)
                points_2d = ([midpoint])

                # skip_nans is needed to protect for traceback NaN Error
                for point_3d in list(pc2.read_points(self.pointCloud, uvs=points_2d, skip_nans=True)):
                    x, y, z = point_3d
                    return x, y, z

        return None

    pass       