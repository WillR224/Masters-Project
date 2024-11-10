#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  8 14:37:49 2021

@author: jfm
"""

import numpy as np
import time

def getCurrentValue(line, lineSplitter, lineSplitIndex):
    split = line.split(lineSplitter)
    #print(line)
    #for s in split:
    #    print(s + "\n")
    return float(split[lineSplitIndex])




#def Read_XYFormat(path):
    #DataOut = []    
    #The output will be a 2D array. So to acces your data use DataOut[1,:] (or the other way round)         
    
#   return Read_XYFormat(path, "", False)


#def Read_XYFormat(path, extention):
#    return Read_XYFormat(path, extention, False)


def Read_XYFormat(path, extention = "", averageOtherColumns = False, startIndex = 0):
    #DataOut = []    
    #The output will be a 2D array. So to acces your data use DataOut[1,:] (or the other way round)         
    
    #timeAtStart = round(time.time() * 1000)
    #timeStamps = []
    #timeStamps.append(round(time.time() * 1000) - timeAtStart)
    
    try:
    
        file1 = open(path + extention, 'r')
        lines = file1.read().splitlines()
        
        #lines = [];
        #while True:
    
        #    # Get next line from file
        #    line = file1.readline()
         
            # If line is empty end of file is reached
        #    if not line:
        #        break
        #    else:
        #        lines.append(line)
        
        lenX = len(lines)
        lenY = len(lines[startIndex].split(','))
        #print(lenX, lenY)
        #print(lenX - startIndex)
        
        DataOut = np.empty((lenX - startIndex, lenY))
        
        #timeStamps.append(round(time.time() * 1000) - timeAtStart)
        #print("Start")
        for i in range(0, lenX - startIndex): #len(lines)
            line = lines[i + startIndex]
            #if i < 30:
                #print(str(i) + ": " + line)
            lineOut = np.empty(lenY)
            split = line.split(',');
            averagingCount = 0                
            
            for j in range(0, lenY): #len(split)                
                if (split[j] == "" or split[j] == " "):
                    lineOut[j] = 0 #.append(0)
                else:
                    #print("split[j] = '" + str(split[j]) + "'")
                    if j == 0:
                        lineOut[j] = float(split[j]) #.append(float(split[j]))
                    else:
                        if averageOtherColumns:
                            lineOut[2] = lineOut[2] + float(split[j]) #.append(float(split[j])) 
                            averagingCount = averagingCount + 1
                        else:
                            lineOut[j] = float(split[j]) #.append(float(split[j])) 
                            averagingCount = 1
                  
            
            if averageOtherColumns:
                lineOut[2] = lineOut[2] / averagingCount
            DataOut[i] = lineOut;
            
            
            #if i == 0:
            #     print("")
            #     print("")
            # ind = 1
            # if i == ind:
            #     print("line = " + line)
            #     print("DataOut[" + str(i) + "] = " + str(DataOut[i]))            
            
        #timeStamps.append(round(time.time() * 1000) - timeAtStart)
        
        #line = "  :  "
        #for t in timeStamps:
        #    line = line + "   " + str(t)
        #print(line)
                
        #volt = DataOut[:,2]
        # print("max(volt) = " + str(max(volt)))
        

    
    except Exception as e:
        
        print("Issue reading file: " + str(path + extention))
        #print("Exception: " + str(e))
        print(e)
        
        return False, None
    
    return True, DataOut;
    
    