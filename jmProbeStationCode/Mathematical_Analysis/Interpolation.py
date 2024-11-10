#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 15:16:19 2022

@author: jfm
"""


#Function which performs a linear interpolation between TWO points and then finds the x position for a particular TARGET value
#2pT means???
#two times, two voltages
def linearInterpolation_2pT(t1, t2, v1, v2, targetV):
    #ngl, pretty sure this is just y=mx+c

    m  = (v2-v1) / (t2-t1)
    c = v2 - (t2 * m)
    
    x = (targetV - c) / m
    
    #print("t1 = " + str(t1))
    #print("t2 = " + str(t2))
    #print("v1 = " + str(v1))
    #print("v2 = " + str(v2))
    #print("targetV = " + str(targetV))
    
    #print("m = " + str(m))
    #print("c = " + str(c))
    #print("x = " + str(x))
    
    return x
    
    
    