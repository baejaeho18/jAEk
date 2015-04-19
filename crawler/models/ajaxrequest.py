'''
Created on 23.02.2015

@author: constantin
'''
import hashlib
from models.asyncrequests import AsyncRequests


class AjaxRequest(AsyncRequests):
    '''
    Models an Ajax-Request issued by an event
    '''
    def __init__(self, method, url, trigger, parameters=None):
        super(AjaxRequest, self).__init__(method, url, parameters)
        self.trigger = trigger

    def toString(self):
        msg =  "[Ajax - Methode: " + self.method + " - Url: "+ self.url.toString() + " - Trigger: " + self.trigger.toString() + " \n"
        for param_pair in self.parameters if self.parameters is not None else []:
            msg += " - Parameter pair: " + str(param_pair)
        return msg

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        try:
            url = self.url.complete_url
        except AttributeError:
            url = self.url
        try:
            o_url = other.url.complete_url
        except AttributeError:
            o_url = other.url

        return self.method == other.method and url == o_url and self.trigger == other.trigger

    def __neg__(self):
        return not  self.__eq__()

