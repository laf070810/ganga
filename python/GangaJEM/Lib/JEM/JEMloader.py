"""
This is a stub object representing the core JEM library in the GangaJEM plugin for Ganga.
If the JEM library can be found in Ganga's external-directory *or* in the directory poin-
ted at by the shell variable $JEM_PACKAGEPATH (this path being priorized), it gets loaded
by the stub and inserted into the python-path.

@author: Tim Muenchen
@date: 20.04.09
@organization: University of Wuppertal,
               Faculty of mathematics and natural sciences,
               Department of physics.
@copyright: 2007-2009, University of Wuppertal, Department of physics.
@license: ::

        Copyright (c) 2007-2009 University of Wuppertal, Department of physics

    Permission is hereby granted, free of charge, to any person obtaining a copy of this 
    software and associated documentation files (the "Software"), to deal in the Software 
    without restriction, including without limitation the rights to use, copy, modify, merge, 
    publish, distribute, sublicense, and/or sell copies of the Software, and to permit 
    persons to whom the Software is furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all copies 
    or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
    PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE 
    LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE 
    OR OTHER DEALINGS IN THE SOFTWARE. 
"""
import os
import sys
import traceback

import GangaJEM

#-----------------------------------------------------------------------------------------------------------------------
from Ganga.Utility.logging import logging, getLogger
logger = getLogger()

# uncomment this to make the JEM proxy report the reason for initialization failure verbosely. 
#logger.setLevel(logging.DEBUG)
#-----------------------------------------------------------------------------------------------------------------------

# vars to access from other GangaJEM modules (FIXME)
INITIALIZED = False
JEM_PACKAGEPATH = None
rgmaPubEnabled = False
httpsPubEnabled = False
tcpPubEnabled = False
httpsExternal = False
fpEnabled = False


## try to load the Job Execution Monitor (JEM) for runtime job monitoring data.
try:
    # check if the user provided an own JEM packagepath via the shell variable...
    if not os.environ.has_key('JEM_PACKAGEPATH'):
        # if not, find the JEM package in the external packages...
        JEM_PACKAGEPATH = GangaJEM.PACKAGE.setup.getPackagePath('JEM')[0]

        # set the env var to enable JEM to find itself...
        os.environ['JEM_PACKAGEPATH'] = JEM_PACKAGEPATH
    else:
        JEM_PACKAGEPATH = os.environ['JEM_PACKAGEPATH']

    # ...and prepend it to the python-path (priorizing it)
    if not JEM_PACKAGEPATH in sys.path:
        sys.path = [JEM_PACKAGEPATH] + sys.path

    # import JEM-Ganga-Integration module (that manages the rest of JEMs initialisation)
    initError = None
    userpath = os.path.expanduser("~/.JEMrc")

    try:
        # try to import JEM configs and submit methods
        from JEMlib.conf import JEMSysConfig as SysConfig
        from JEMui.conf import JEMuiSysConfig as JEMConfig
        from JEMlib.conf import JEMConfig as WNConfig
        from JEMui.conf import JEMuiConfig as UIConfig

        # import needed JEM modules
        from JEMlib.utils.ReverseFileReader import ropen
        from JEMlib.utils.DictPacker import multiple_replace
        from JEMlib.utils import Utils
        from JEMlib import VERSION as JEM_VERSION
    except Exception, e:
        initError = "Wrong JEM_PACKAGEPATH specified. Could not find JEM library."
    
    if os.path.exists(userpath):
        if initError == None:
            if not SysConfig.GANGA_ENABLED:
                initError = "Please set the GANGA_ENABLED variable in JEMSysConfig to 'True' to enable JEM support."
    
        if initError == None:
            rgmaPubEnabled = WNConfig.PUBLISHER_USE_TYPE & WNConfig.PUBLISHER_USE_RGMA
            tcpPubEnabled = WNConfig.PUBLISHER_USE_TYPE & WNConfig.PUBLISHER_USE_TCP
            httpsPubEnabled = (WNConfig.PUBLISHER_USE_TYPE & WNConfig.PUBLISHER_USE_HTTPS) \
                              or (WNConfig.PUBLISHER_USE_TYPE & WNConfig.PUBLISHER_USE_FSHYBRID)
            httpsExternal = WNConfig.HTTPS_SERVER_EXTERNAL
    
            enabledPublisherCount = 0
            if rgmaPubEnabled:  enabledPublisherCount += 1
            if tcpPubEnabled:   enabledPublisherCount += 1
            if httpsPubEnabled: enabledPublisherCount += 1
            if enabledPublisherCount != 1:
                initError = 'Exactly one of [RGMA publisher, TCP publisher, HTTPS publisher, FS-Hybrid-publisher] must be activated. Please check PUBLISHER_USE_TYPE in JEMConfig.'

    if initError == None:
        lines = [
                  Utils.colored("JEM", 32) + " (the " + Utils.colored("J", 32) + "ob " \
                      + Utils.colored("E", 32) + "xecution " + Utils.colored("M", 32) + "onitor) v" + str(JEM_VERSION) + " loaded ",
                  "type 'help(JobExecutionMonitor)' for usage instructions",
                  "this is still an " + Utils.colored("alpha", 31) + " version of JEM - please give feedback!",
                  "visit https://svn.grid.uni-wuppertal.de/trac/JEM for more information"
                ]
        print Utils.getLogo(lines)
        print

        logger.debug("Using JEM from: " + JEM_PACKAGEPATH)

        if os.path.exists(userpath):
            # check if file publisher is enabled
            fpEnabled = (WNConfig.PUBLISHER_USE_TYPE & WNConfig.PUBLISHER_USE_FS) \
                        or (WNConfig.PUBLISHER_USE_TYPE & WNConfig.PUBLISHER_USE_FSHYBRID)
            if not fpEnabled:
                logger.warning("JEM is not correctly configured to include detailled monitoring data in the job's output sandbox.")
                logger.debug("Configuration hint: Please ensure that PUBLISHER_USE_TYPE contains PUBLISHER_USE_FS in JEMConfig.")
    
            # check if the JEMui side of the story uses the XML publisher
            if not UIConfig.PUBLISHER_OUTPUT_TYPE & JEMConfig.PUBLISHER_OUTPUT_JMD:
                logger.warning('JEM is not correctly configured to pass data to Ganga.')
                logger.debug("Configuration hint: Please ensure that PUBLISHER_OUTPUT_TYPE contains PUBLISHER_OUTPUT_JMD in JEMuiConfig.")
                if fpEnabled:
                    logger.warning('JEM realtime monitoring got disabled. However, monitoring data still will be available in the output sandbox.')
                else:
                    initError = 'Also, monitoring data isn\'t available in the output sandbox.'

    # if some error occured during initialization, disable JEM monitoring.
    if initError != None:
        raise Exception(initError)
    

    INITIALIZED = True
except Exception, err:
    if len(err.args) > 0 and err.args[0] == "disabled":
        logger.info("The Job Execution Monitor is disabled by config.")
    else:
        logger.warn("unable to initialize the Job Execution Monitor module - realtime job monitoring will be disabled.")
        logger.warn("reason: " + ": " + str(sys.exc_info()[1]))
        logger.debug("trace: " + str(traceback.extract_tb(sys.exc_info()[2])))
