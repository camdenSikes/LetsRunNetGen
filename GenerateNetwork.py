from html.parser import HTMLParser
from operator import indexOf
import numpy as np
from scipy import sparse
import re

class LetsRunParser(HTMLParser):
    curind = -1
    parentList = [-1]
    #0 = normal, 1 = registered, 2 = official
    labelList = []
    userList = []
    getPostName = False
    getCategory = False
    category = ""
    running = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str]]) -> None:
        if (tag == "div"):
            for tup in attrs:
                if tup[0] == "id" and "post" in tup[1]:
                    #make sure we're in a new post
                    temp = tup[1].split("-")
                    if(len(temp) == 2 and str.isdigit(temp[1])):
                        #print("post: ",temp[1])
                        self.curind += 1
        if (tag == "a"):
            for tup in attrs:
                if tup[0] == "class" and (tup[1] == "mention-link" or tup[1] == "author-link"):
                    #only looking at main reply reference
                    break
                if tup[0] == "href" and "post" in tup[1]:
                    temp = tup[1].split("-")
                    if(len(temp) == 2):
                        #print(tup[1])
                        try:
                            self.parentList.append(int(temp[1])-1)
                        except:
                            #TODO: Make sure we don't want to do something else here
                            continue
        if (tag == "button"):
            for tup in attrs:
                if tup[0] == "title" and tup[1] == "User Dropdown":
                    self.getPostName = True
                if tup[0] == "id" and "call-to-action-follow" in tup[1] and self.labelList[self.curind] == 0:
                    self.labelList[self.curind] = 1
        if (tag == "svg"):
            for tup in attrs:
                #there should be a better way to do this
                if tup[0] == "class" and tup[1] == "default-icon mr-2 text-gray-500 w-3 h-3 sm:w-3.5 sm:h-3.5 relative top-px":
                    self.getCategory = True
                if tup[0] == "class" and tup[1] == "default-icon mr-1 relative text-letsrun-blue w-3 h-3":
                    self.labelList.append(2)


        return super().handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if (tag == "button"):
            self.getPostName = False
        return super().handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if(data == "Non-Running"):
            self.running = False
        if(self.getCategory) and data not in ['','\n',' ']:
            self.category = data
            self.getCategory = False
        if(self.getPostName) and data not in ['','\n',' ']:
            #print(data)
            self.userList.append(data)
            if(len(self.labelList) < len(self.userList)):
                self.labelList.append(0)
        return super().handle_data(data)

def generateNetwork(data: str) -> tuple[list[str], np.array]:
    lrp = LetsRunParser()
    lrp.feed(data)
    users = []
    for name in lrp.userList:
        if name not in users:
            users.append(name)
    numUsers = len(users)
    labels = [0]*numUsers
    adjMat = sparse.lil_matrix((numUsers,numUsers), dtype=np.int8)
    for i in range(len(lrp.parentList)):
        child = lrp.userList[i]
        childInd = indexOf(users,child)
        labels[childInd] = lrp.labelList[i]
        try:
            parent = lrp.userList[lrp.parentList[i]]
        except:
            print("parent out of range")
            continue
        parentInd = indexOf(users,parent)
        #currently just making this an undirected graph
        #weighted by number of connections
        adjMat[childInd,parentInd] += 1
        adjMat[parentInd,childInd] += 1
    return (users,adjMat,labels,lrp.running,lrp.category)
    


if __name__ == "__main__":
    lrp = LetsRunParser()
    testFile = open("letsrunlabeltest.htm", "r")
    testText = testFile.read()
    testFile.close()
    (users,adjMat,labels,isRunning,category) = generateNetwork(testText)
    print(users)
    print(adjMat)
    print(isRunning)
    print(category)
    print(labels)