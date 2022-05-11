'''
Created on 30 mars 2020
updated on May 17th 2021

Takes as input a json file corresponding to an Agilkia trace set, an abstract function, 
and a boolean to take subsumption into account.
The abstract function is given as the 2nd argument. By default, it is OpNames_Set. 
By default, subsumption is False.

It uses the abstract function to group traces in clusters, using the Agilkia primitives for clusters. 

It returns a json file storing a traceset tagged with cluster information.
(another script should be used to pick up one test case per cluster and generate a reduced traceset).

Example:

ClusterAgilkiaTestSuite.py ../traces/1026-steps.AgilkiaTraces.json OpNames_Seq_NoSt

it computes 11 clusters, and generates the file ../traces/1026-steps.AgilkiaTraces.Clustered/1026-steps.AgilkiaTraces_OpNames_Seq_NoSt.json

If subsumption is activated, the clusters which are subsummed by another (larger) one, are deleted. This reduces the number of clusters.

Example :

ClusterAgilkiaTestSuite.py ../traces/1026-steps.AgilkiaTraces.json OpNames_Seq_NoSt 2

it uses subsumption "MatchedBy" and computes 2 clusters (instead of 11 without subsumption).

The codes are 0-> No Sub, 1 -> (subset, subbag, prefix), 2 -> (subset, subbag, matchedBy), depending on the nature of the criterion (Set, Bag or Seq)  

@author: ledru
License: MIT
'''
import os
import sys
import csv
import time
# from shutil import copy
from pathlib import Path
import agilkia


def main():
    (File2Xplore,absFunc,subsume) = GetArgs()
    
    ComputeSigDictAndReduce(File2Xplore,absFunc,subsume,"")
    #ComputeSigDictAndReduce(File2Xplore,"OpNames_Set",0,"")
    #ComputeSigDictAndReduce(File2Xplore,"OpNamesAndRet_Set",0,"")
    #ComputeSigDictAndReduce(File2Xplore,"OpNamesAndAbsRet_Set",0,"")
    #ComputeSigDictAndReduce(File2Xplore,"OpNames_Bag",0,"")
    #ComputeSigDictAndReduce(File2Xplore,"OpNamesAndRet_Bag",0,"")
    #ComputeSigDictAndReduce(File2Xplore,"OpNamesAndAbsRet_Bag",0,"")
    #ComputeSigDictAndReduce(File2Xplore,"OpNames_Seq",0,"")
    #ComputeSigDictAndReduce(File2Xplore,"OpNamesAndRet_Seq",0,"")
    #ComputeSigDictAndReduce(File2Xplore,"OpNamesAndAbsRet_Seq",0,"")
    #ComputeSigDictAndReduce(File2Xplore,"OpNames_Seq_NoSt",0,"")
    #ComputeSigDictAndReduce(File2Xplore,"OpNamesAndRet_Seq_NoSt",0,"")
    #ComputeSigDictAndReduce(File2Xplore,"OpNamesAndAbsRet_Seq_NoSt",0,"")

def ComputeSigDictAndReduce(File2Xplore,absFunction,subsumption,my_outputDir):
    local_time = time.ctime(time.time())
    print(str(local_time)+" Computing signatures with abstract function "+absFunction+" ...")
    (trace_set,absDirPath,shortFileName)=GetTraceSetAndDirAndFileName(File2Xplore)
    sigDict = BuildSigDict(trace_set,absFunction)
    
    intermediate_time = time.ctime(time.time())
    print(str(intermediate_time)+" Building Clusters...")
    if subsumption>0 :
        subSumptionFunction = findSubsumption(absFunction,subsumption)
    else:
        subSumptionFunction = NoSub 
    cl=BuildClusters(sigDict,subSumptionFunction) 
    AddClustersToTraceset(trace_set,cl)   
    print(str(intermediate_time)+" Reducing testsuite.")
    # If the user does not define an output dir, the default is absDirPath/shortFileName_Clustered
    if subsumption==1:
        subsumptionString= "_sub"
    elif subsumption==2:
        subsumptionString= "_su2"
    else:
        subsumptionString= ""
    trace_set.set_meta("clustering_criterion",absFunction+subsumptionString)
    if my_outputDir=="":
        outputDir=os.path.join(absDirPath,shortFileName+"_Clustered")
    CreateOutputDir(outputDir)
    saveTraceSetAndClusters(trace_set,shortFileName,outputDir,absFunction+subsumptionString)
#    ReduceTestSuite(cl,absDirPath,outputDir)  
    final_time = time.ctime(time.time())
    print(final_time)

#Takes a trace_set and clustering information and adds clustering information to the trace_set
def AddClustersToTraceset(trace_set,cl) :
    labels = [ (-1) for tr in trace_set.traces] 
    for i in range(len(cl)) :
        for j in cl[i][1] :
            labels[j]=i
    trace_set.set_clusters(labels)
            

#Returns the first argument or '.' if the first argument is missing
#also it returns the abstract function (2nd argument) or "OpNames_Set" if missing
def GetArgs():
    result = "."
    absFunction = "OpNames_Set"
    subsume = 0
    if (len(sys.argv) > 1):
        result = sys.argv[1]
    if (len(sys.argv) > 2):
        absFunction = sys.argv[2]
    if (len(sys.argv) > 3):
        subsume = int(sys.argv[3])
    return (result,absFunction,subsume)

# Returns an agilkia traceset located at filePath
# and the absolute path of the directory storing the file.
# and the file name (without ".json")
# filePath must be a json file
def GetTraceSetAndDirAndFileName(filePath):
    if os.path.isfile(filePath)  and filePath.endswith(".json"):
        #The parameter corresponds to a single json file
        tr_set = agilkia.TraceSet.load_from_json(Path(filePath))
        absDirPath=os.path.abspath(os.path.dirname(filePath))
        (shortFileName, fileExtension) = os.path.splitext(os.path.basename(filePath))
    else :
        absDirPath = ""
        shortFileName = ""
        tr_set = agilkia.TraceSet([])
        print('No json file at location: '+filePath)
    return (tr_set,absDirPath,shortFileName)

# returns the set of operation names 
# for a given trace, i.e. a list of events
# The set is transformed into a sorted list.
def GetOpNames(tr_events):
    listOfNames = [(evt.action) for evt in tr_events]
    listOfNames = list(set(listOfNames))
    listOfNames.sort()
    return listOfNames  

# returns the set of operation names and return results
# for a given trace, i.e. a list of events
# The set is transformed into a sorted list.
def GetOpNamesAndReturn(tr_events):
    listOfNames = [(evt.action+(str(evt.outputs.get("Status")))) for evt in tr_events] 
    # we use outputs.get("Status") instead of outputs["Status"] to avoid keyerror exception 
    listOfNames = list(set(listOfNames))
    listOfNames.sort()
    return listOfNames  

# reports if its argument is >0, <0, =0
def abstractReturn (resultOfEvt):
    try:
        if float(resultOfEvt)>0:
            res = '>0'
        elif float(resultOfEvt)<0:
            res = '<0'
        else:
            res = '=0'
    except ValueError:
        res = '**'
    return res

# returns the set of operation names and an abstraction of the return results
# for a given trace, i.e. a list of events
# The set is transformed into a sorted list.
def GetOpNamesAndAbstractReturn(tr_events):
    listOfNames = [(evt.action+abstractReturn(str(evt.outputs.get("Status")))) for evt in tr_events]
    listOfNames = list(set(listOfNames))
    listOfNames.sort()
    return listOfNames  

# returns the bag of operation names
# for a given trace, i.e. a list of events
def GetOpNamesBag(tr_events):
    listOfNames = [(evt.action) for evt in tr_events]
    listOfNames.sort()
    return listOfNames 

# returns the bag of operation names and abstract return results
# for a given trace, i.e. a list of events
def GetOpNamesAndReturnBag(tr_events):
    listOfNames = [(evt.action+(str(evt.outputs.get("Status")))) for evt in tr_events] 
    listOfNames.sort()
    return listOfNames 

# returns the bag of operation names and return results
# for a given trace, i.e. a list of events
def GetOpNamesAndAbstractReturnBag(tr_events):
    listOfNames = [(evt.action+abstractReturn(str(evt.outputs.get("Status")))) for evt in tr_events]
    listOfNames.sort()
    return listOfNames 


# returns the sequence of operation names
# for a given trace, i.e. a list of events
def GetOpNamesSequence(tr_events):
    listOfNames = [(evt.action) for evt in tr_events]
    return listOfNames 

# returns the set of operation names and return results
# for a given trace, i.e. a list of events
def GetOpNamesAndReturnSequence(tr_events):
    listOfNames = [(evt.action+(str(evt.outputs.get("Status")))) for evt in tr_events] 
    return listOfNames 

# returns the set of operation names and return results
# for a given trace, i.e. a list of events
def GetOpNamesAndAbstractReturnSequence(tr_events):
    listOfNames = [(evt.action+abstractReturn(str(evt.outputs.get("Status")))) for evt in tr_events]
    return listOfNames 

# This function must be combined with one of the above functions which return a sequence
# Given a sequence, removes consecutive replicates
# [ 'a', 'b', 'b', 'b', 'a', 'a'] gives [ 'a', 'b', 'a']
def RemoveConsecutiveReplicates(myList):
    result = []
    previous = ""
    for i in myList:
        if i != previous:
            result.append(i)
            previous = i            
    return result

# returns True if pref is a prefix of seq
def prefix(my_pref,my_seq):
    if len(my_pref) > len(my_seq):
        return False
    result = True
    i = 0
    while i<len(my_pref) and result==True :
        result = result and (my_pref[i]==my_seq[i])
        i+=1
    return result

# returns True if my_shortseq can be found in my_seq after deleting some of its elements
# e.g. [B,C,E] is matched by [A,B,C,D,E,F] because the elements of the short sequence appear in the same order in the big sequence
def matchedBy(my_shortseq,my_seq):
    result = True
    i=0
    j=0
    while i<len(my_shortseq) and j<len(my_seq):
        if my_shortseq[i]==my_seq[j]:
            i+=1
            j+=1
        else : 
            j+=1
    if i==len(my_shortseq):
        result = True
    else :
        result = False
    return result


# returns True if my_sub is a subset of my_set
def subset(my_sub,my_set):
    result = True
    for i in my_sub:
        if i not in my_set:
            result = False
    return result

# returns True if my_sub is a subbag of my_bag, i.e. all elements of the first bag are included in the second one.
# bags are represented by sorted lists with repetition of elements
def subbag(my_sub,my_bag):
    result = True
    i=0
    j=0
    while i<len(my_sub) and j<len(my_bag) and result==True:
        if my_sub[i]==my_bag[j]:
            i+=1
            j+=1
        elif my_sub[i]>my_bag[j]:
            j+=1
        elif my_sub[i]<my_bag[j]:
            result=False
    if j==len(my_bag) and i<len(my_sub):
        result=False
    return result

# Function which always returns False; i.e. the subsumption relation is empty
def NoSub(my_sub,my_bag):
    return False

def ComputeSig(tr_events,absFunction):
    if absFunction == "OpNames_Set":
        sigResult = GetOpNames(tr_events)
    elif absFunction == "OpNamesAndRet_Set":
        sigResult = GetOpNamesAndReturn(tr_events)
    elif absFunction == "OpNamesAndAbsRet_Set":
        sigResult = GetOpNamesAndAbstractReturn(tr_events)
    elif absFunction == "OpNames_Bag":
        sigResult = GetOpNamesBag(tr_events)
    elif absFunction == "OpNamesAndRet_Bag":
        sigResult = GetOpNamesAndReturnBag(tr_events)
    elif absFunction == "OpNamesAndAbsRet_Bag":
        sigResult = GetOpNamesAndAbstractReturnBag(tr_events)
    elif absFunction == "OpNames_Seq":
        sigResult = GetOpNamesSequence(tr_events)
    elif absFunction == "OpNamesAndRet_Seq":
        sigResult = GetOpNamesAndReturnSequence(tr_events)
    elif absFunction == "OpNamesAndAbsRet_Seq":
        sigResult = GetOpNamesAndAbstractReturnSequence(tr_events)
    elif absFunction == "OpNames_Seq_NoSt":
        sigResult = GetOpNamesSequence(tr_events)
        sigResult = RemoveConsecutiveReplicates(sigResult)
    elif absFunction == "OpNamesAndRet_Seq_NoSt":
        sigResult = GetOpNamesAndReturnSequence(tr_events)
        sigResult = RemoveConsecutiveReplicates(sigResult)
    elif absFunction == "OpNamesAndAbsRet_Seq_NoSt":
        sigResult = GetOpNamesAndAbstractReturnSequence(tr_events)
        sigResult = RemoveConsecutiveReplicates(sigResult)
    else:
        print("Unknown abstraction function!")
        sigResult = []
    return (sigResult)

def findSubsumption(absFunction,subsume):
    if absFunction == "OpNames_Set":
        subFunction = subset
    elif absFunction == "OpNamesAndRet_Set":
        subFunction = subset
    elif absFunction == "OpNamesAndAbsRet_Set":
        subFunction = subset
    elif absFunction == "OpNames_Bag":
        subFunction = subbag
    elif absFunction == "OpNamesAndRet_Bag":
        subFunction = subbag
    elif absFunction == "OpNamesAndAbsRet_Bag":
        subFunction = subbag
    elif absFunction == "OpNames_Seq":
        if subsume==2:
            subFunction = matchedBy
        else:
            subFunction = prefix
    elif absFunction == "OpNamesAndRet_Seq":
        if subsume==2:
            subFunction = matchedBy
        else:
            subFunction = prefix
    elif absFunction == "OpNamesAndAbsRet_Seq":
        if subsume==2:
            subFunction = matchedBy
        else:
            subFunction = prefix
    elif absFunction == "OpNames_Seq_NoSt":
        if subsume==2:
            subFunction = matchedBy
        else:
            subFunction = prefix
    elif absFunction == "OpNamesAndRet_Seq_NoSt":
        if subsume==2:
            subFunction = matchedBy
        else:
            subFunction = prefix
    elif absFunction == "OpNamesAndAbsRet_Seq_NoSt":
        if subsume==2:
            subFunction = matchedBy
        else:
            subFunction = prefix
    else:
        print("Unknown abstraction function!")
        subFunction = NoSub
    return (subFunction)


# builds a mapping between test cases (agilkia traces) and signatures
def BuildSigDict(trace_set,absFunction):
    mySigDict={}
    for i in range(len(trace_set.traces)):
        tr_indx = i 
            # builds the list of operations  
        signature=ComputeSig(trace_set.traces[i],absFunction)
        mySigDict[tr_indx]=signature
    print()
    print()
    return (mySigDict)

# builds the range of mySigDict (the list of different signatures)
# each of these values corresponds to a new cluster.
#The range is sorted (which makes it easier to compare with the result of other clusterings)
def BuildValSetasList(mySigDict):
    valSetasList=[]
    for j in mySigDict.values():
        if j not in valSetasList:  
            valSetasList.append(j)
    print("Number of clusters : "+str(len(valSetasList)))
    valSetasList.sort()
    return(valSetasList)

# use the mapping to construct the clusters and choose one test case per cluster.
def BuildClusters(mySigDict,subsumedBy):
    # Extract the range of mySigDict, which corresponds to the set of clusters signatures 
    valSetasList = BuildValSetasList(mySigDict)
    # perform additional modifications of valSetasList
    i=0
    
    while i<len(valSetasList):
        j=i+1
        while j<len(valSetasList):
        
            if subsumedBy(valSetasList[j],valSetasList[i]):
                #j is a subset of i so j should be deleted from the list
                #j does not change its value but now points to the next element of the list
                valSetasList.pop(j)
            
            elif subsumedBy(valSetasList[i],valSetasList[j]):
                #i is a subset of j, so i should be deleted, and j reset to i+1
                # the value of i does not change but now points to the next element of the list
                valSetasList.pop(i)
                j=i+1
            else:
                #neither i nor j is a subset of the other; j should be incremented
                j=j+1
        #j has reached the end of the list, the next i should be explored
        i=i+1
    print("Number of clusters after subsumption: "+str(len(valSetasList)))
    
        
    #builds "clusters", the inverse mapping of valSetasList, as a list of tuples (cluster,list of test cases)
    #and prints his mapping
    clusters=[]
    for val in valSetasList:
        testCases = [k for k,v in mySigDict.items() if v == val]
        clusters.append((val,testCases))
        print(val)
        print(testCases)
    print()
    #print the abstractions, i.e. the signatures of the clusters
    print("Signatures of clusters")
    for val in valSetasList:
        print(val)
    # print the results
    print("Number of clusters : "+str(len(valSetasList)))
    return(clusters)

# Creates an output directory if it does not already exist
def CreateOutputDir(outputDir):
#    result = "OK"
    if not os.path.exists(outputDir):
        print('Creating directory',outputDir)
        os.makedirs(outputDir)
    else :
        print('Directory ',outputDir,'already exists. Proceeding with the existing directory.')
#        if len(os.listdir(outputDir))>0:
#            print ("Directory is not empty. Halting the program! No reduced test suite was saved.")
#            result = "Directory not empty!"
#    return result

def saveTraceSetAndClusters(trace_set,shortFileName,outputDir,criteria):
    outputFileName=os.path.join(outputDir,shortFileName+"_"+criteria+".json")
    trace_set.save_to_json(Path(outputFileName))
    print("Traceset saved to "+outputFileName)

#This function is no longer used
def ReduceTestSuite(clusters,absDirPath,outputDir):    
    # pick the first test case of each cluster (cl[1][0]) and print the result
    for i in range(len(clusters)):
        cl = clusters[i]
        print("Selected trace from cluster "+str(i)+" : tr"+str(cl[1][0]))
    print()
    # print the number of clusters a second time because the first one might be out of screen
    print("Number of test cases : "+str(len(clusters)))
    
    
#Main program
if __name__ == '__main__' :
    main()
