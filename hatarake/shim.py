import sys
import logging

import rumps.rumps as rumps
import AppKit
import Foundation
import PyObjCTools


logger = logging.getLogger(__name__)


class Shim(rumps.App):
    '''
    Custom run method to get around notification center errors in a virtual env
    '''
    def run(self):
        """
        Perform various setup tasks then start application run loop.
        """
        nsapplication = AppKit.NSApplication.sharedApplication()
        nsapplication.activateIgnoringOtherApps_(True)  # NSAlerts in front
        self._nsapp = rumps.NSApp.alloc().init()
        self._nsapp._app = self.__dict__  # allow for dynamic modification based on this App instance
        self._nsapp.initializeStatusBar()
        nsapplication.setDelegate_(self._nsapp)
        try:
            Foundation.NSUserNotificationCenter.defaultUserNotificationCenter().setDelegate_(self._nsapp)
        except AttributeError:
            logger.debug("Error setting up notification center")

        setattr(rumps.App, '*app_instance', self)  # class level ref to running instance (for passing self to App subclasses)
        t = b = None
        for t in getattr(rumps.timer, '*timers', []):
            t.start()
        for b in getattr(rumps.clicked, '*buttons', []):
            b(self)  # we waited on registering clicks so we could pass self to access _menu attribute
        del t, b

        PyObjCTools.AppHelper.runEventLoop()
        sys.exit(0)
