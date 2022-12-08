import pickle
import struct
import time
from html.parser import HTMLParser
from operator import indexOf
from typing import Tuple

import numpy as np
import urllib3
from requests import request
from scipy import io, sparse

from GenerateNetwork import generateNetwork


class NetworkList:
    networks: list[sparse.csc_matrix] = []
    userlists: list[list[str]] = []
    urls: list[str] = []
    isRunningRelated: list[bool] = []
    categories: list[str] = []
    labelLists: list[list[int]] = []

    def append(self, network: np.array, userlist: list[str], url: str, running: bool, category: str, labelList: list[int]) -> None:
        self.networks.append(network)
        self.userlists.append(userlist)
        self.urls.append(url)
        self.isRunningRelated.append(running)
        self.categories.append(category)
        self.labelLists.append(labelList)

    def get(self, i: int) -> Tuple[np.array, list[str], str]:
        #TODO: make sure ind is within bounds
        return(self.networks[i],self.userlists[i],self.urls[i],self.isRunningRelated[i],self.categories[i],self.labelLists[i])

    def printCats(self) -> None:
        for i in range(len(self.categories)):
            print(str(i)+": "+self.categories[i])


class HomepageParser(HTMLParser):
    threads = []
    pageCounts = []
    reading = False
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str]]) -> None:
        #only start reading threads when we get to the list
        if tag == "ul":
            for attr in attrs:
                if attr[0] == "class" and attr[1] == "forum-index-thread-list":
                    self.reading = True
        #stop reading when we get to the end of the list
        if self.reading and tag == "span":
            for attr in attrs:
                if attr[0] == "title" and "You are viewing" in attr[1]:
                    self.reading = False
        if self.reading and tag == "a":
            for attr in attrs:
                if attr[0] == "href" and "thread=" in attr[1]:
                    if "page" not in attr[1]:
                        #main link
                        if attr[1] not in self.threads:
                            self.threads.append(attr[1])
                            self.pageCounts.append(0)
                    else:
                        #page link
                        temp = attr[1].split("&")
                        page = temp[1].split("=")
                        self.pageCounts[indexOf(self.threads,temp[0])] = int(page[1])
        return super().handle_starttag(tag, attrs)


def getThreads() -> tuple[list[str],list[int]]:
    http = urllib3.PoolManager()
    r = http.request("GET", "https://letsrun.com/forum")
    hpp = HomepageParser()
    hpp.feed(r.data.decode('utf-8'))
    return(hpp.threads,hpp.pageCounts)
    #print(hpp.threads)
    #print(hpp.pageCounts)

def getStrings(urls: list[str], counts: list[int]) -> list[str]:
    http = urllib3.PoolManager()
    (urls,counts) = getThreads()
    strings = []
    for i in range(len(urls)):
        try:
            r = http.request("GET",urls[i])
        except:
            time.sleep(2)
            try:
                r = http.request("GET",urls[i])
            except:
                print("failed to get post")
                continue
        strings.append(r.data.decode('utf-8'))
        #for now, only look at first 10 pages not anymore
        for j in range(1,counts[i]+1):
            try:
                r = http.request("GET",urls[i]+"&page="+str(j),)
            except:
                break
            if(r.status != 200):
                break
            strings[i] += r.data.decode("utf-8")
    return strings



if __name__ == "__main__":
    (urls,counts) = getThreads()
    print("got " + str(len(urls)) + " threads")
    strings = getStrings(urls,counts)
    print("got all strings")
    nets = NetworkList()
    netDict = dict()
    for i in range(len(strings)):
        (users,adjMat,running,category,labels) = generateNetwork(strings[i])
        nets.append(adjMat,users,urls[i],running,category,labels)
        netDict[str(i)] = adjMat
        print("made matrix")
    outfile = open("networks.pkl","wb")
    pickle.dump(nets,outfile)
    io.savemat("nets.mat", netDict)
    nets.printCats()


    