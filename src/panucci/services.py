#!/usr/bin/env python
#
#  from services.py -- Core Services for gPodder
#  Thomas Perl <thp@perli.net>   2007-08-24
#
#  2009-02-13 - nikosapi: made ObservableService more Panucci-esque
#

from logging import getLogger

class ObservableService(object):
    def __init__(self, signal_names=[], log=None):
        self.__log = getLogger('ObservableService') if log is None else log

        self.observers = {}
        for signal in signal_names:
            self.observers[signal] = []

        if not signal_names:
            self.__log.warning('No signal names defined...')

    def register(self, signal_name, observer):
        if signal_name in self.observers:
            if not observer in self.observers[signal_name]:
                self.observers[signal_name].append(observer)
                self.__log.debug( 'Registered "%s" as an observer for "%s"',
                    observer.__name__, signal_name )
            else:
                self.__log.warning(
                    'Observer "%s" is already added to signal "%s"',
                    observer.__name__, signal_name )
        else:
            self.__log.warning(
                'Signal "%s" is not available for registration', signal_name )

    def unregister(self, signal_name, observer):
        if signal_name in self.observers:
            if observer in self.observers[signal_name]:
                self.observers[signal_name].remove(observer)
                self.__log.debug( 'Unregistered "%s" as an observer for "%s"',
                    observer.__name__, signal_name )
            else:
                self.__log.warning(
                    'Observer "%s" could not be removed from signal "%s"', 
                    observer.__name__, signal_name )
        else:
            self.__log.warning(
                'Signal "%s" is not available for un-registration.',
                signal_name )

    def notify(self, signal_name, *args, **kwargs):
        caller = kwargs.get('caller')
        caller = 'UnknownCaller' if caller is None else caller.__name__

        if signal_name in self.observers:
            self.__log.debug(
                'Sending signal "%s" for caller "%s"', signal_name, caller )

            for observer in self.observers[signal_name]:
                observer( *args )
        else:
            self.__log.warning(
                'Signal "%s" (from caller "%s") is not available '
                'for notification', signal_name, caller )

