#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug  4 11:32:51 2021

@author: jfm
"""

def d2SortX(x, y):
    newX = [x[0]]
    newY = [y[0]]

    for i in range(1, len(x)):
        insertionMade = False
        for j in range(0, len(newX)):
            if x[i] < newX[j]:
                newX.insert(j, x[i])
                newY.insert(j, y[i])                            
                insertionMade = True
                break
        if not insertionMade:
            newX.append(x[i])
            newY.append(y[i])       
                
    return [newX, newY]

def d3SortX(x, y, z):
    newX = [x[0]]
    newY = [y[0]]
    newZ = [z[0]]

    for i in range(1, len(x)):
        insertionMade = False
        for j in range(0, len(newX)):
            if x[i] < newX[j]:
                newX.insert(j, x[i])
                newY.insert(j, y[i])                            
                newZ.insert(j, z[i])
                insertionMade = True
                break
        if not insertionMade:
            newX.append(x[i])
            newY.append(y[i])       
            newZ.append(z[i])       
                
    return [newX, newY, newZ]


def d4SortX(x, y, z, w):
    newX = [x[0]]
    newY = [y[0]]
    newZ = [z[0]]
    newW = [w[0]]

    for i in range(1, len(x)):
        insertionMade = False
        for j in range(0, len(newX)):
            if x[i] < newX[j]:
                newX.insert(j, x[i])
                newY.insert(j, y[i])                            
                newZ.insert(j, z[i])
                newW.insert(j, w[i])
                insertionMade = True
                break
        if not insertionMade:
            newX.append(x[i])
            newY.append(y[i])       
            newZ.append(z[i])       
            newW.append(w[i])  
                
    return [newX, newY, newZ, newW]


#def mdSort(data, listToSort):
    