import logging
from datamodel.search.datamodel import ProducedLink, OneUnProcessedGroup, robot_manager
from spacetime_local.IApplication import IApplication
from spacetime_local.declarations import Producer, GetterSetter, Getter
from lxml import html,etree
import re, os
from time import time
from urllib2 import urlopen
from bs4 import BeautifulSoup
import hashlib


try:
    # For python 2
    from urlparse import urlparse, parse_qs
except ImportError:
    # For python 3
    from urllib.parse import urlparse, parse_qs


logger = logging.getLogger(__name__)
LOG_HEADER = "[CRAWLER]"
url_count = (set()
    if not os.path.exists("successful_urls.txt") else
    set([line.strip() for line in open("successful_urls.txt").readlines() if line.strip() != ""]))
MAX_LINKS_TO_DOWNLOAD = 2000
md5 =[]
url_record = []
numBadLink=0
MaxLink=-1
average_time=0
sub_links=0
@Producer(ProducedLink)
@GetterSetter(OneUnProcessedGroup)
class CrawlerFrame(IApplication):

    def __init__(self, frame):
        self.starttime = time()
        # Set app_id <student_id1>_<student_id2>...
        self.app_id = "73784800_29529834_34564916"
        #34564916
        # Set user agent string to IR W17 UnderGrad <student_id1>, <student_id2> ...
        # If Graduate studetn, change the UnderGrad part to Grad.
        self.UserAgentString = "IR W17 Grad 73784800, 29529834, 34564916"
        # Set user agent string to IR W17 UnderGrad <student_id1>, <student_id2> ...

        self.frame = frame
        assert(self.UserAgentString != None)
        assert(self.app_id != "")
        if len(url_count) >= MAX_LINKS_TO_DOWNLOAD:
            self.done = True

    def initialize(self):
        self.count = 0
        l = ProducedLink("http://www.ics.uci.edu", self.UserAgentString)
        print l.full_url
        self.frame.add(l)

    def update(self):
        for g in self.frame.get(OneUnProcessedGroup):
            print "Got a Group"
            outputLinks, urlResps = process_url_group(g, self.UserAgentString)
            for urlResp in urlResps:
                if urlResp.bad_url and self.UserAgentString not in set(urlResp.dataframe_obj.bad_url):
                    urlResp.dataframe_obj.bad_url += [self.UserAgentString]
            for l in outputLinks:
                if is_valid(l) and robot_manager.Allowed(l, self.UserAgentString):
                    lObj = ProducedLink(l, self.UserAgentString)
                    self.frame.add(lObj)
        if len(url_count) >= MAX_LINKS_TO_DOWNLOAD:
            # global  average_time
            # average_time = (time()-self.starttime)/len(url_count)
            # with open("information.txt", "a") as info:
            #     info.write("number of bad link is "+str(numBadLink))
            #     info.write("Max sub link is "+str(MaxLink))
            #     info.write("Average download time is "+str(average_time))
            #     info.write("Total number of sub urls is "+str(sub_links))
            self.done = True

    def shutdown(self):
        print "downloaded ", len(url_count), " in ", time() - self.starttime, " seconds."
        pass

def save_count(urls):
    global url_count
    urls = set(urls).difference(url_count)
    url_count.update(urls)
    if len(urls):
        with open("successful_urls.txt", "a") as surls:
            surls.write(("\n".join(urls) + "\n").encode("utf-8",'ignore'))

def process_url_group(group, useragentstr):
    rawDatas, successfull_urls = group.download(useragentstr, is_valid)
    save_count(successfull_urls)
    return extract_next_links(rawDatas), rawDatas

#######################################################################################
'''
STUB FUNCTIONS TO BE FILLED OUT BY THE STUDENT.
'''
def extract_next_links(rawDatas):
    outputLinks = list()
    global numBadLink,MaxLink,average_time,sub_links
    '''
    rawDatas is a list of objs -> [raw_content_obj1, raw_content_obj2, ....]
    Each obj is of type UrlResponse  declared at L28-42 datamodel/search/datamodel.py
    the return of this function should be a list of urls in their absolute form
    Validation of link via is_valid function is done later (see line 42).
    It is not required to remove duplicates that have already been downloaded.
    The frontier takes care of that.

    Suggested library: lxml
    '''
    #print(rawDatas)
    #print("__________________________")
    #print(not rawDatas)
    #os.sleep(100)
    start_time = time()
    if rawDatas == []:
        print "empty"
        return rawDatas
    numberLinkInItem = 0
    for item in rawDatas:
        print "all info is_Redi,final,httpcode,headers,error"
        print item.is_redirected
        print item.final_url
        print item.http_code
        print item.headers
        print item.error_message
        if item == []:
            print "rawDatas is empty"
            # if raw data is empty, return it.
            return item
        if is_valid(item.url)==False:
            item.bad_url = True
            print "bad url"
            print item.url
            continue
        # if item.is_redirected == True:
        #     if not is_valid(item.final_url):
        #         continue
        #     else:
        #         item.url = item.final_url
        if not item.content or len(item.error_message) != 0:
            # content is empty and error_message exists.
            # bad url
            # check if is valid. maybe item.url is .txt, instead of a accessible page.
            print str(item.url) + "is a badddddddddd!!!!"
            item.bad_url = True
            numBadLink = numBadLink+1
            continue
        else:
            dom  = html.fromstring(item.content)
            Lists = dom.xpath('//a/@href')
            if len(Lists) == 0:
                # there is no url inside given page.
                # continue to process next link.
                continue
            for link in Lists: # select the url in href for all a tags(links)
                # for output information:
                split_error=False
                try:
                    link.encode('ascii')
                    link.decode('utf-8')
                except UnicodeEncodeError as e:
                    print "cannot decode link, bad url"
                    continue
                if len(Lists)>MaxLink:
                    MaxLink = len(Lists)
                check_vaild = False
                print "test url" + str(link)
                if not link:
                    # if link is empty
                    # continue to process next link
                    continue
                try:
                    splitByColon = link.split(":")
                except e:
                    # error means it is relative path and no mailto: no javascript:
                    split_error = True
                    # set this boolean vari for a clear way.
                if split_error == True:
                    # there is no colon inside url
                    # must be relative path
                    # this kind of path is accessible in full path form.
                    if link == "":
                        continue
                    if link == "#":
                        continue
                    if link[0:2] == './':
                        link = link[2:]
                    if link[0] == '/':
                        link = link[1:]
                        while(link[0]=='/'):
                            link = link[1:]
                        link = item.url[0]+'/'+link
                        check_vaild = is_valid(unicode(link))
                    elif link[0:3]=='../':
                        # link start with ..
                        dotnumber = 1
                        link = link[3:]
                        while(link[0:3]=='../'):
                            dotnumber = dotnumber+1
                            link = link[3:]
                        urlsplit = item.url[0].split("/")
                        if len(urlsplit)<=3+dotnumber:
                            continue
                        else:
                            UrlWithoutLastHier = urlsplit[0]+"//"+urlsplit[2]
                            for index in range(3,len(urlsplit)-dotnumber):
                                UrlWithoutLastHier = UrlWithoutLastHier +'/'+ urlsplit[index]
                            link = UrlWithoutLastHier + '/'+link[2:]
                        check_vaild = is_valid(unicode(link))
                    elif link[0]=='?':
                        HasQuestionMark = True
                        try:
                            SplitByQuestionMark = item.url[0].split("?")
                        except e:
                            HasQuestionMark = False
                        if HasQuestionMark == True:
                            link = SplitByQuestionMark[0:-1] + link
                        else:
                            link = item.url[0] + link
                        check_vaild = is_valid(unicode(link))
                else:
                    # there is colon inside url
                    # it could be http:
                    if link[0:7]=='http://' or link[0:8] == 'https://':
                        # if url start with 'https://' or 'http://'
                        # check if it is valid.
                        check_vaild = is_valid(unicode(link))
                    else:
                    # cannot figure out any possible, logical url with more than one colons
                        continue
                    # outputLinks append this link
                if check_vaild:
                    numberLinkInItem = numberLinkInItem+1
                    outputLinks.append(link)
    # type cast again to make sure every link is unique.
    if numberLinkInItem != 0:
        average_time = average_time + (time()- start_time)
    sub_links = sub_links+numberLinkInItem
    average_time_tmp =0
    if sub_links!=0:
        average_time_tmp = average_time/sub_links
    with open("information.txt", "w") as info:
        info.write("number of bad link|Max sub link|Average download time|Total number of sub urls"+'\n')
        info.write(str(numBadLink)+'\t'+str(MaxLink)+'\t'+str(float(average_time_tmp))+'\t'+str(sub_links)+'\n')
        info.close()
    outputLinks = list(set(outputLinks))
    return outputLinks

def is_valid(url):
    '''
    Function returns True or False based on whether the url has to be downloaded or not.
    Robot rules and duplication rules are checked separately.

    This is a great place to filter out crawler traps.
    '''
    #print(url)
    try:
        url.encode("ascii")
    except UnicodeEncodeError as e:
        print "cannot convert to ascii"
        return False
    parsed = urlparse(url)
    #print parsed.schemes
    if parsed.scheme not in set(["http", "https", "www"]):
        return False
    try:
        return ".ics.uci.edu" in parsed.hostname \
            and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4"\
            + "|wav|txt|odp|py|avi|mov|xgmml|bed|ss|lif|psp|bst|c|java|sge|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
            + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
            + "|thmx|mso|arff|rtf|jar|csv"\
            + "|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()) \
            and PageDuplicate(str(url)) \
            and UrlDuplicate(str(url)) \
            and UrlConfuseHier(str(url))

    except TypeError:
        print ("TypeError for ", parsed)
"""
    UrlConfuseHier
        Function:
            CHECK THERE IS NO ".." IN GIVEN URL
        Args:
            paraml: Url
        Returns:
            If given URl contains of "..", return false.
            else return true
"""
def UrlConfuseHier(url):
    if ".." in url or "./" in url or "../" in url:
        print "this is url with confusion of hierarchy"
        print(url)
        return False
    else:
        return True
"""
    UrlDuplicate
        Function:
            Make sure the URL is new
        Args:
            param1: Url
        Returns:
            If we had visited this URL return False, otherwise it return True
"""
def UrlDuplicate(url):
    if url in url_record:
        return False
    else:
        url_record.append(url)
        return True
"""
    PageDuplicate
        Function:
            Make sure the page we extracted, it should be unique, even there are same
            URL. We try our best to analysis the content fo html page
        Args:
            param1: Url
        Returns:
            If we doesn't have the content of this page, it will return True.
            If we can't analysis the content or the content we already have it,
            it will return False
"""

def PageDuplicate(url):
    md5_checker = True
    MAX_FILE_SIZE = 1024 * 1024 * 1024
    print (url) 
    try:
        page = urlopen(urlopen(url).geturl())
        r = page.read(MAX_FILE_SIZE)
        soup = BeautifulSoup(r,'html.parser')
    except:
        return False
    try:
        md5_h = hashlib.md5(soup.find('head').text.encode('utf-8','ignore')).hexdigest()
        md5_b = hashlib.md5(soup.find('body').text.encode('utf-8','ignore')).hexdigest()
    except:
        md5_checker = False

    if md5_checker:
        content = (md5_h, md5_b)
        if content in md5:
            return False
        else:
            md5.append(content)
            return True
    else:
        return True

