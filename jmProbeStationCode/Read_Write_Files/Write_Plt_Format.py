#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 10:02:15 2021

@author: jfm
"""

#This writes out data in a format known to my own plotting software
#The format is not that complicated
#It requires a header line such as "x,y"
#so it knows what the format is (i.e. scatter)
#Another example is "m,c" which means straight lines with those parameters
#Then it is just a list
#You can convert a lot of files to this format by simple adding the header. Even if there is other data in other cells
#(like excel). As long as the header and the data is on the far left and in the order expected, the reader will
#ignore any other data

def Write_StandardPltFormat(folderPath, filename, fmt, data):
        #folderPath and file name should be obvious
        #fmt is format i.e. a string such as "x,y". Defined by the user
        #data is all teh data, in a 2D array.
        #So [XDataArray, YDataArray, EYDataArray] etc
        
        fileLines = []
        
        fileLines.append(fmt)
        
        if fmt == "x":
            lenX = len(data)
            
            line = ""
            for j in range(lenX): #New data piece
                line = str(data[j])
                if j != lenX - 1:
                    line = line + ","
                
                fileLines.append(line)
                
        else:            
            lenX = len(data)
            lenY = len(data[0])
                    
            for i in range(lenY): #New line
                line = ""
                for j in range(lenX): #New data piece
                    line = line + str(data[j][i])
                    if j != lenX - 1:
                        line = line + ","
                    
                fileLines.append(line)
            
            
        path = folderPath + "/" + filename
            
        file = open(path, 'w+')
        file.truncate(0)
            
        for l in fileLines:
            file.write(l)
            file.write('\n')
                
        file.close()
        
        
def Read_StandardPltFormat(path):
    
    file1 = open(path, 'r')
    lines = file1.read().splitlines()
    
    xData = []
    yData = []
    
    flagFound = False
    
    for i in range(0, len(lines)):        
        line = lines[i]
        #print("Line = " + str(line))
        
        if line == "\n" or line == "END\n" or line == "\r" or line == "END\r" or line == "END" or line == "":
            flagFound = False
            
        if flagFound:
            split = line.split(',');
            xData.append(float(split[0]))
            if (len(split) > 1):
                try: 
                    yData.append(float(split[1]))
                except:
                    yData.append((split[1]))
        
        if line == "x,y" or line == "x,y\r" or line == "x,y,ey" or line == "x,y,ey\r":
            flagFound = True            
        if line == "Time_Dif_List" or line == "Time_Dif_List\r":
            flagFound = True            
          
    return [xData, yData];