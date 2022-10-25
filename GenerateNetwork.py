from html.parser import HTMLParser
from operator import indexOf
import numpy as np

class LetsRunParser(HTMLParser):
    curind = -1
    parentList = [-1]
    userList = []
    getPostName = False

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
                if tup[0] == "class" and tup[1] == "mention-link":
                    #only looking at main reply reference
                    break
                if tup[0] == "href" and "post" in tup[1]:
                    temp = tup[1].split("-")
                    if(len(temp) == 2):
                        #print(tup[1])
                        self.parentList.append(int(temp[1])-1)
        if (tag == "button"):
            for tup in attrs:
                if tup[0] == "title" and tup[1] == "User Dropdown":
                    self.getPostName = True


        return super().handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if (tag == "button"):
            self.getPostName = False
        return super().handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if(self.getPostName) and data not in ['','\n',' ']:
            #print(data)
            self.userList.append(data)
        return super().handle_data(data)

def generateNetwork(data: str) -> tuple[list[str], np.array]:
    lrp = LetsRunParser()
    lrp.feed(data)
    users = []
    for name in lrp.userList:
        if name not in users:
            users.append(name)
    numUsers = len(users)
    adjMat = np.zeros((numUsers,numUsers), dtype=np.int8)
    for i in range(len(lrp.parentList)):
        child = lrp.userList[i]
        childInd = indexOf(users,child)
        parent = lrp.userList[lrp.parentList[i]]
        parentInd = indexOf(users,parent)
        #currently just making this an undirected graph
        #weighted by number of connections
        adjMat[childInd,parentInd] += 1
        adjMat[parentInd,childInd] += 1
    return (users,adjMat)
    


if __name__ == "__main__":
    lrp = LetsRunParser()
    testFile = open("letsruntest1.htm", "r")
    testText = testFile.read()
    testFile.close()
    (users,adjMat) = generateNetwork(testText)
    print(users)
    print(adjMat)