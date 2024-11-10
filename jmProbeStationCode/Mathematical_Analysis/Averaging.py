#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 01:02:31 2022

@author: jfm
"""
import numpy as np


def Get_StdAvg(lst):
    
    #First get the mean
    length = len(lst)
    
    avg = 0
    for i in range(length):
        avg = avg + lst[i]
    avg = avg / length
    
    stdD = 0
    for i in range(length):
        stdD = stdD + ((lst[i] - avg) * (lst[i] - avg))
    stdD = stdD / length
    stdD = np.sqrt(stdD)
    
    return avg, stdD, length