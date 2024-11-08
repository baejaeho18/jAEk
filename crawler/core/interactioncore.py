'''
Copyright (C) 2015 Constantin Tschuertz

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


# from PyQt5.Qt import QWebPage, QWebSettings
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineSettings
from PyQt5.QtNetwork import QNetworkProxy, QNetworkRequest
from PyQt5.QtCore import QSize, QUrl, QByteArray

from time import time, sleep
from core.jsbridge import JsBridge
from models.clickable import Clickable
from models.utils import CrawlSpeed
import logging

class InteractionCore(QWebEnginePage):
    '''
    This is the main class for interacting with a webpage, here are all necessary js-files loaded, and signal connections build
    '''    
    def __init__(self, parent, proxy = "", port = 0, crawl_speed = CrawlSpeed.Medium, network_access_manager = None):
        QWebEnginePage.__init__(self, parent)
        self.app = parent.app
        self._js_bridge = JsBridge(self)
        self.loadFinished.connect(self.loadFinishedHandler)
        self.mainFrame().javaScriptWindowObjectCleared.connect(self.jsWinObjClearedHandler)
        self.frameCreated.connect(self.frameCreatedHandler)
        self.setViewportSize(QSize(1024, 800))

        if crawl_speed == CrawlSpeed.Slow:
            self.wait_for_processing = 1
            self.wait_for_event = 2
        if crawl_speed == CrawlSpeed.Medium:
            self.wait_for_processing = 0.3
            self.wait_for_event = 1
        if crawl_speed == CrawlSpeed.Fast:
            self.wait_for_processing = 0.1
            self.wait_for_event = 0.5
        if crawl_speed == CrawlSpeed.Speed_of_Lightning:
            self.wait_for_processing = 0.01
            self.wait_for_event = 0.1
        
        f = open("js/lib.js", "r")
        self._lib_js = f.read()
        f.close()
        
        f = open("js/ajax_observer.js")
        self._xhr_observe_js = f.read()
        f.close()
        
        f = open("js/timing_wrapper.js")
        self._timeming_wrapper_js = f.read()
        f.close()
        
        
        f = open("js/ajax_interceptor.js")
        self._xhr_interception_js = f.read()
        f.close()
        
        f = open("js/addeventlistener_wrapper.js")
        self._addEventListener = f.read()
        f.close()
        
        f = open("js/md5.js")
        self._md5 = f.read()
        f.close()

        f = open("js/property_obs.js")
        self._property_obs_js = f.read()
        f.close()

        enablePlugins = True
        loadImages = False
        self.settings().setAttribute(QWebEngineSettings.PluginsEnabled, enablePlugins)
        self.settings().setAttribute(QWebEngineSettings.JavaEnabled, enablePlugins)
        #self.settings().setAttribute(QWebEngineSettings.AutoLoadImages, loadImages)
        self.settings().setAttribute(QWebEngineSettings.DeveloperExtrasEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        
        if network_access_manager:
            self.setNetworkAccessManager(network_access_manager)
        
        if proxy != "" and port != 0: 
            manager = self.networkAccessManager()
            p = QNetworkProxy(QNetworkProxy.HttpProxy, proxy, port, None, None)
            manager.setProxy(p)
            self.setNetworkAccessManager(manager)

        #Have to connect it here, otherwise I could connect it to the old one and then replaces it
        self.networkAccessManager().finished.connect(self.loadComplete)

    def analyze(self, html, requested_url, timeout = 20):
        raise NotImplemented()
    
    def userAgentForUrl(self, url):
        return "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
    
    def loadFinishedHandler(self, result):
        pass
    
    def frameCreatedHandler(self, frame):
        pass
    
    def jsWinObjClearedHandler(self):
        pass

    def javaScriptAlert(self, frame, msg):
        pass

    def javaScriptConfirm(self, frame, msg):
        return True
    
    def javaScriptPrompt(self, *args, **kwargs):
        return True
            
    def _wait(self, waiting_time=1):
        """Wait for delay time
        """
        deadline = time() + waiting_time
        while time() < deadline:
            sleep(0)
            self.app.processEvents()
            
    def javaScriptConsoleMessage(self, message, lineNumber, sourceID):
        #logging.debug("Console: " + message + " at: " + str(lineNumber))
        pass

    def loadComplete(self, reply):
        pass

    def add_eventlistener_to_element(self, msg):
        #logging.debug(msg)
        if "id" in msg and msg['id'] != "":
            id = msg['id']
        else:
            id = None
        dom_address = msg['addr']
        event = msg['event']
        if event == "":
            event = None
        tag = msg['tag']
        if "class" in msg and msg['class'] != "":
            html_class = msg['class']
        else:
            html_class = None
        function_id = msg['function_id']
        if tag is not None and dom_address != "":
            tmp = Clickable(event, tag, dom_address, id, html_class, function_id=function_id)
            if tmp not in self._new_clickables:
                self._new_clickables.append(tmp)


    def search_element_with_id(self, element_id):
        elem = self.mainFrame().findAllElements("#" + str(element_id))
        if len(elem) > 0:
            return elem[0] # maybe check if there is more than one element
        else:
            return None

    def search_element_with_class(self, cls, dom_adress):
        css_cls_definition = ""
        classes = cls.split(" ")
        for cls in classes: #converting class names in css-compatible classnames
            cls = "." + cls
            css_cls_definition = css_cls_definition + cls + " "
        elems = self.mainFrame().findAllElements(css_cls_definition)
        for elem in elems:
            if dom_adress == elem.evaluateJavaScript("getXPath(this)"):
                return elem

    def search_element_without_id_and_class(self, dom_adress):
        check_dom_adress = dom_adress
        dom_address = dom_adress.split("/")
        current_element_in_dom = self.mainFrame().documentElement() #Is HTML-Element
        while len(dom_address) > 0 and current_element_in_dom is not None:
            target_tag_name = dom_address.pop(0) # Get and remove the first element
            target_tag_name = target_tag_name.upper()
            if len(target_tag_name) == 0:
                continue
            elif target_tag_name == "HTML": #or target_tag_name == "body":
                continue
            else:
                tmp = target_tag_name.find("[")
                if tmp > 0: # target_tag_name looks like tagname[index]
                    target_tag_name = target_tag_name.split("[")
                    index = int(target_tag_name[1].split("]")[0]) # get index out of target_tag_name
                    target_tag_name = target_tag_name[0] # target_tag_name name
                    last_child = current_element_in_dom.lastChild()
                    tmp_element = current_element_in_dom.findFirst(target_tag_name) # takes first child
                    if tmp_element.tagName() == target_tag_name: # if firstchild is from type of target_tag_name, subtrakt 1 from index
                        index -= 1;
                    counter = 100 #Sometimes comparing with last child went wrong, therefore we have an backup fragment_counter
                    while index > 0 and tmp_element != last_child: # take next sibbling until index is 0, if target_tag_name is equal subtrakt one
                        tmp_element = tmp_element.nextSibling() #
                        if tmp_element.tagName() == target_tag_name:
                            index -= 1
                        counter -= 1
                        if counter == 0: #If fragment_counter 0 then break, we wont find it anymore
                            current_element_in_dom = None
                            break
                    if index == 0 and tmp_element.tagName() == target_tag_name:
                        current_element_in_dom = tmp_element
                    else: #We miss the element
                        current_element_in_dom = None
                else: #target_tag_name is the only of his type, or the first...is die hell
                    tmp_element = current_element_in_dom.firstChild()
                    last_child = current_element_in_dom.lastChild()
                    counter = 100
                    while tmp_element.tagName() != target_tag_name and tmp_element != last_child and counter > 0:
                        #logging.debug(tmp_element.tagName())
                        counter -= 1
                        if tmp_element.tagName() == target_tag_name:
                            current_element_in_dom = tmp_element
                            break
                        else:
                            tmp_element = tmp_element.nextSibling()
                    if tmp_element.tagName() != target_tag_name or counter == 0:
                        current_element_in_dom = None
                    else:
                        current_element_in_dom = tmp_element

        tmp_element = None
        last_child = None
        dom_address = None

        if current_element_in_dom == None:
            return None
        if current_element_in_dom.evaluateJavaScript("getXPath(this)") != check_dom_adress:
            logging.debug("Element not found: " + str(current_element_in_dom.evaluateJavaScript("getXPath(this)")) + " : " + str(check_dom_adress))
            return None
        else:
            return current_element_in_dom


    def make_request(self, url):
        request = QNetworkRequest()
        request.setUrl(QUrl(url))
        return request

    def post_data_to_array(self, post_data):
        post_params = QByteArray()
        for (key, value) in post_data.items():
            if isinstance(value, list):
                for val in value:
                    post_params.append(key + "=" + val + "&")
            else:
                post_params.append(key + "=" + value + "&")
        post_params.remove(post_params.length() - 1, 1)
        return post_params