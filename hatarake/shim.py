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
    def run(self, **options):
        """Performs various setup tasks including creating the underlying Objective-C application, starting the timers,
        and registering callback functions for click events. Then starts the application run loop.
        .. versionchanged:: 0.2.1
            Accepts `debug` keyword argument.
        :param debug: determines if application should log information useful for debugging. Same effect as calling
                      :func:`rumps.debug_mode`.
        """
        dont_change = object()
        debug = options.get('debug', dont_change)
        if debug is not dont_change:
            debug_mode(debug)

        nsapplication = AppKit.NSApplication.sharedApplication()
        nsapplication.activateIgnoringOtherApps_(True)  # NSAlerts in front
        self._nsapp = rumps.NSApp.alloc().init()
        self._nsapp._app = self.__dict__  # allow for dynamic modification based on this App instance
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

        self._nsapp.initializeStatusBar()

        PyObjCTools.AppHelper.runEventLoop()
