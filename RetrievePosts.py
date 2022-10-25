from operator import indexOf
import struct
from typing import Tuple
from requests import request
from GenerateNetwork import generateNetwork
import urllib3
from html.parser import HTMLParser
import numpy as np
import pickle

class NetworkList:
    networks: list[np.array] = []
    userlists: list[list[str]] = []
    urls: list[str] = []

    def append(self, network: np.array, userlist: list[str], url: str) -> None:
        self.networks.append(network)
        self.userlists.append(userlist)
        self.urls.append(url)

    def get(self, i: int) -> Tuple[np.array, list[str], str]:
        #TODO: make sure ind is within bounds
        return(self.networks[i],self.userlists[i],self.urls[i])

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
        r = http.request("GET",urls[i])
        strings.append(r.data.decode('utf-8'))
        #for now, only look at first 10 pages
        for j in range(1,min(counts[i]+1,10)):
            r = http.request("GET",urls[i]+"&page="+str(j))
            strings[i] += r.data.decode("utf-8")
    return strings



if __name__ == "__main__":
    (urls,counts) = getThreads()
    strings = getStrings(urls,counts)
    nets = NetworkList()
    for i in range(len(urls)):
        (users,adjMat) = generateNetwork(strings[i])
        nets.append(adjMat,users,urls[i])
    outfile = open("networks.pkl","wb")
    print(nets.networks[3])
    pickle.dump(nets,outfile)


    