#!/usr/bin/env python3
import re
import datetime
import logging
from decimal import *
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("parser")

from app.exceptions import *
import app.hand as hh
import app.handhistoryconverter as hhc


class PokerStars():

    sitename = "PokerStars"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 2 # Needs to match id entry in Sites database
    sym = {'USD': "\$", 'CAD': "\$", 'T$': "", "EUR": "\xe2\x82\xac", "GBP": "\£", "play": ""}         # ADD Euro, Sterling, etc HERE
    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",      # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|\£|", # legal currency symbols - Euro(cp1252, utf-8)
                           'PLYR': r'(?P<PNAME>.+?)',
                            'CUR': u"(\$|\xe2\x82\xac|\u20ac||\£|)",
                          'BRKTS': r'(\(button\) |\(small blind\) |\(big blind\) |\(button\) \(small blind\) |\(button\) \(big blind\) )?',
                    }

    # translations from captured groups to fpdb info strings
    Lim_Blinds = {      '0.04': ('0.01', '0.02'),         '0.08': ('0.02', '0.04'),
                        '0.10': ('0.02', '0.05'),         '0.20': ('0.05', '0.10'),
                        '0.40': ('0.10', '0.20'),         '0.50': ('0.10', '0.25'),
                        '1.00': ('0.25', '0.50'),         '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),         '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),         '4': ('1.00', '2.00'),
                        '6.00': ('1.00', '3.00'),         '6': ('1.00', '3.00'),
                        '8.00': ('2.00', '4.00'),         '8': ('2.00', '4.00'),
                       '10.00': ('2.00', '5.00'),        '10': ('2.00', '5.00'),
                       '20.00': ('5.00', '10.00'),       '20': ('5.00', '10.00'),
                       '30.00': ('10.00', '15.00'),      '30': ('10.00', '15.00'),
                       '40.00': ('10.00', '20.00'),      '40': ('10.00', '20.00'),
                       '60.00': ('15.00', '30.00'),      '60': ('15.00', '30.00'),
                       '80.00': ('20.00', '40.00'),      '80': ('20.00', '40.00'),
                      '100.00': ('25.00', '50.00'),     '100': ('25.00', '50.00'),
                      '150.00': ('50.00', '75.00'),     '150': ('50.00', '75.00'),
                      '200.00': ('50.00', '100.00'),    '200': ('50.00', '100.00'),
                      '400.00': ('100.00', '200.00'),   '400': ('100.00', '200.00'),
                      '800.00': ('200.00', '400.00'),   '800': ('200.00', '400.00'),
                     '1000.00': ('250.00', '500.00'),  '1000': ('250.00', '500.00'),
                     '2000.00': ('500.00', '1000.00'), '2000': ('500.00', '1000.00'),
                  }

    limits = { 'No Limit':'nl', 'NO LIMIT':'nl', 'Pot Limit':'pl', 'POT LIMIT':'pl', 'Limit':'fl', 'LIMIT':'fl' , 'Pot Limit Pre-Flop, No Limit Post-Flop': 'pn'}
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'),
                              "HOLD'EM" : ('hold','holdem'),
                                'Omaha' : ('hold','omahahi'),
                                'OMAHA' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo'),
                          'OMAHA HI/LO' : ('hold','omahahilo'),
                                 'Razz' : ('stud','razz'),
                                 'RAZZ' : ('stud','razz'),
                          '7 Card Stud' : ('stud','studhi'),
                          '7 CARD STUD' : ('stud','studhi'),
                    '7 Card Stud Hi/Lo' : ('stud','studhilo'),
                    '7 CARD STUD HI/LO' : ('stud','studhilo'),
                               'Badugi' : ('draw','badugi'),
              'Triple Draw 2-7 Lowball' : ('draw','27_3draw'),
              'Single Draw 2-7 Lowball' : ('draw','27_1draw'),
                          '5 Card Draw' : ('draw','fivedraw')
               }
    mixes = {
                                 'HORSE': 'horse',
                                '8-Game': '8game',
                                '8-GAME': '8game',
                                  'HOSE': 'hose',
                         'Mixed PLH/PLO': 'plh_plo',
                         'Mixed NLH/PLO': 'nlh_plo',
                       'Mixed Omaha H/L': 'plo_lo',
                        'Mixed Hold\'em': 'mholdem',
                           'Triple Stud': '3stud'
               } # Legal mixed games
    currencies = { u'€':'EUR', '$':'USD', '':'T$', u'£':'GBP' }

    # Static regexes
    re_GameInfo     = re.compile(u"""
          (PokerStars|POKERSTARS)(?P<TITLE>\sGame|\sHand|\sHome\sGame|\sHome\sGame\sHand|Game|\sZoom\sHand|\sGAME)\s\#(?P<HID>[0-9]+):\s+
          (\{.*\}\s+)?(Tournament\s\#                # open paren of tournament info
          (?P<TOURNO>\d+),\s
          # here's how I plan to use LS
          (?P<BUYIN>(?P<BIAMT>[%(LS)s\d\.]+)?\+?(?P<BIRAKE>[%(LS)s\d\.]+)?\+?(?P<BOUNTY>[%(LS)s\d\.]+)?\s?(?P<TOUR_ISO>%(LEGAL_ISO)s)?|Freeroll)\s+)?
          # close paren of tournament info
          (?P<MIXED>HORSE|8\-Game|8\-GAME|HOSE|Mixed\sOmaha\sH/L|Mixed\sHold\'em|Mixed\sPLH/PLO|Mixed\sNLH/PLO|Triple\sStud)?\s?\(?
          (?P<GAME>Hold\'em|HOLD\'EM|Razz|RAZZ|7\sCard\sStud|7\sCARD\sSTUD|7\sCard\sStud\sHi/Lo|7\sCARD\sSTUD\sHI/LO|Omaha|OMAHA|Omaha\sHi/Lo|OMAHA\sHI/LO|Badugi|Triple\sDraw\s2\-7\sLowball|Single\sDraw\s2\-7\sLowball|5\sCard\sDraw)\s
          (?P<LIMIT>No\sLimit|NO\sLIMIT|Limit|LIMIT|Pot\sLimit|POT\sLIMIT|Pot\sLimit\sPre\-Flop,\sNo\sLimit\sPost\-Flop)\)?,?\s
          (-\s)?
          (Match.*)?                  #TODO: waiting for reply from user as to what this means
          (Level\s(?P<LEVEL>[IVXLC]+)\s)?
          \(?                            # open paren of the stakes
          (?P<CURRENCY>%(LS)s|)?
          (?P<SB>[.0-9]+)/(%(LS)s)?
          (?P<BB>[.0-9]+)
          (?P<CAP>\s-\s[%(LS)s\d\.]+\sCap\s-\s)?        # Optional Cap part
          \s?(?P<ISO>%(LEGAL_ISO)s)?
          \)                        # close paren of the stakes
          (?P<BLAH2>\s\[AAMS\sID:\s[A-Z0-9]+\])?         # AAMS ID: in .it HH's
          \s-\s
          (?P<DATETIME>.*$)
        """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile(u"""
          ^Seat\s(?P<SEAT>[0-9]+):\s
          (?P<PNAME>.*)\s
          \((%(LS)s)?(?P<CASH>[.0-9]+)\sin\schips\)""" % substitutions,
          re.MULTILINE|re.VERBOSE)

    re_HandInfo     = re.compile("""
          ^Table\s\'(?P<TABLE>.+?)\'\s
          ((?P<MAX>\d+)-max\s)?
          (?P<PLAY>\(Play\sMoney\)\s)?
          (Seat\s\#(?P<BUTTON>\d+)\sis\sthe\sbutton)?""",
          re.MULTILINE|re.VERBOSE)

    re_SplitHands   = re.compile('(?:\s?\n){2,}')
    re_TailSplitHands   = re.compile('(\n\n\n+)')
    re_Button       = re.compile('Seat #(?P<BUTTON>\d+) is the button', re.MULTILINE)
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")
    re_DateTime     = re.compile("""(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)
    # revised re including timezone (not currently used):
    #re_DateTime     = re.compile("""(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+) \(?(?P<TZ>[A-Z0-9]+)""", re.MULTILINE)

    # These used to be compiled per player, but regression tests say
    # we don't have to, and it makes life faster.
    re_PostSB           = re.compile(r"^%(PLYR)s: posts small blind %(CUR)s(?P<SB>[.0-9]+)" %  substitutions, re.MULTILINE)
    re_PostBB           = re.compile(r"^%(PLYR)s: posts big blind %(CUR)s(?P<BB>[.0-9]+)" %  substitutions, re.MULTILINE)
    re_Antes            = re.compile(r"^%(PLYR)s: posts the ante %(CUR)s(?P<ANTE>[.0-9]+)" % substitutions, re.MULTILINE)
    re_BringIn          = re.compile(r"^%(PLYR)s: brings[- ]in( low|) for %(CUR)s(?P<BRINGIN>[.0-9]+)" % substitutions, re.MULTILINE)
    re_PostBoth         = re.compile(r"^%(PLYR)s: posts small \& big blinds %(CUR)s(?P<SBBB>[.0-9]+)" %  substitutions, re.MULTILINE)
    re_HeroCards        = re.compile(r"^Dealt to %(PLYR)s(?: \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\])" % substitutions, re.MULTILINE)
    re_Action           = re.compile(r"""
                        ^%(PLYR)s:(?P<ATYPE>\sbets|\schecks|\sraises|\scalls|\sfolds|\sdiscards|\sstands\spat)
                        (\s%(CUR)s(?P<BET>[.\d]+))?(\sto\s%(CUR)s(?P<BETTO>[.\d]+))?  # the number discarded goes in <BET>
                        \s*(and\sis\sall.in)?
                        (and\shas\sreached\sthe\s[%(CUR)s\d\.]+\scap)?
                        (\son|\scards?)?
                        (\s\[(?P<CARDS>.+?)\])?\s*$"""
                         %  substitutions, re.MULTILINE|re.VERBOSE)
    re_ShowdownAction   = re.compile(r"^%s: shows \[(?P<CARDS>.*)\]" % substitutions['PLYR'], re.MULTILINE)
    re_ShownCards       = re.compile("^Seat (?P<SEAT>[0-9]+): %(PLYR)s %(BRKTS)s(?P<SHOWED>showed|mucked) \[(?P<CARDS>.*)\]( and (lost|won \(%(CUR)s(?P<POT>[.\d]+)\)) with (?P<STRING>.*))?" % substitutions, re.MULTILINE)
    re_CollectPot       = re.compile(r"Seat (?P<SEAT>[0-9]+): %(PLYR)s %(BRKTS)s(collected|showed \[.*\] and won) \(%(CUR)s(?P<POT>[.\d]+)\)(, mucked| with.*|)" %  substitutions, re.MULTILINE)
    re_CollectPot2      = re.compile(r"^%(PLYR)s collected %(CUR)s(?P<POT>[.\d]+)" %  substitutions, re.MULTILINE)
    re_WinningRankOne   = re.compile(u"^%(PLYR)s wins the tournament and receives %(CUR)s(?P<AMT>[\.0-9]+) - congratulations!$" %  substitutions, re.MULTILINE)
    re_WinningRankOther = re.compile(u"^%(PLYR)s finished the tournament in (?P<RANK>[0-9]+)(st|nd|rd|th) place and received %(CUR)s(?P<AMT>[.0-9]+)\.$" %  substitutions, re.MULTILINE)
    re_RankOther        = re.compile(u"^%(PLYR)s finished the tournament in (?P<RANK>[0-9]+)(st|nd|rd|th) place$" %  substitutions, re.MULTILINE)
    re_Cancelled        = re.compile('Hand\scancelled', re.MULTILINE)

    def readSupportedGames(self):
            return [["ring", "hold", "nl"],
                    ["ring", "hold", "pl"],
                    ["ring", "hold", "fl"],
                    ["ring", "hold", "pn"],

                    ["ring", "stud", "fl"],

                    ["ring", "draw", "fl"],
                    ["ring", "draw", "pl"],
                    ["ring", "draw", "nl"],

                    ["tour", "hold", "nl"],
                    ["tour", "hold", "pl"],
                    ["tour", "hold", "fl"],
                    ["tour", "hold", "pn"],

                    ["tour", "stud", "fl"],

                    ["tour", "draw", "fl"],
                    ["tour", "draw", "pl"],
                    ["tour", "draw", "nl"],
                    ]

    def determineGameType(self, handText):
        info = {}
        m = PokerStars.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error("PokerStarsToFpdb.determineGameType: '%s'" % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        if 'LIMIT' in mg:
            info['limitType'] = PokerStars.limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = PokerStars.games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = mg['SB']
        if 'BB' in mg:
            info['bb'] = mg['BB']
        if 'CURRENCY' in mg:
            info['currency'] = PokerStars.currencies[mg['CURRENCY']]
        if 'MIXED' in mg:
            if mg['MIXED'] is not None: info['mix'] = PokerStars.mixes[mg['MIXED']]

        if 'TOURNO' in mg and mg['TOURNO'] is None:
            info['type'] = 'ring'
        else:
            info['type'] = 'tour'

        if not mg['CURRENCY'] and info['type']=='ring':
            info['currency'] = 'play'

        if info['limitType'] == 'fl' and info['bb'] is not None:
            if info['type'] == 'ring':
                try:
                    info['sb'] = PokerStars.Lim_Blinds[mg['BB']][0]
                    info['bb'] = PokerStars.Lim_Blinds[mg['BB']][1]
                except KeyError:
                    tmp = handText[0:200]
                    log.error("PokerStarsToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'" % (mg['BB'], tmp))
                    raise FpdbParseError
            else:
                info['sb'] = str((Decimal(mg['SB'])/2).quantize(Decimal("0.01")))
                info['bb'] = str(Decimal(mg['SB']).quantize(Decimal("0.01")))

        return info

    def readHandInfo(self, handText):
        info = {}
        m = PokerStars.re_HandInfo.search(handText,re.DOTALL)
        m2 = PokerStars.re_GameInfo.search(handText)
        if m is None or m2 is None:
            tmp = handText[0:200]
            log.error("PokerStarsToFpdb.readHandInfo: '%s'" % tmp)
            raise FpdbParseError

        info.update(m.groupdict())
        info.update(m2.groupdict())

        for key in info:
            if key == 'DATETIME':
                m1 = PokerStars.re_DateTime.finditer(info[key])
                datetimestr = "2000/01/01 00:00:00"  # default used if time not found
                for a in m1:
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
                self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
                self.startTime = hhc.HandHistoryConverter.changeTimezone(self.startTime, "ET", "UTC")
            if key == 'HID':
                self.handid = info[key]
            if key == 'TOURNO':
                self.tourNo = info[key]
            if key == 'BUYIN':
                if self.tourNo!=None:
                    #print "DEBUG: info['BUYIN']: %s" % info['BUYIN']
                    #print "DEBUG: info['BIAMT']: %s" % info['BIAMT']
                    #print "DEBUG: info['BIRAKE']: %s" % info['BIRAKE']
                    #print "DEBUG: info['BOUNTY']: %s" % info['BOUNTY']
                    if info[key] == 'Freeroll':
                        self.buyin = 0
                        self.fee = 0
                        self.buyinCurrency = "FREE"
                    else:
                        if info[key].find("$")!=-1:
                            self.buyinCurrency="USD"
                        elif info[key].find(u"£")!=-1:
                            self.buyinCurrency="GBP"
                        elif info[key].find(u"€")!=-1:
                            self.buyinCurrency="EUR"
                        elif info[key].find("FPP")!=-1:
                            self.buyinCurrency="PSFP"
                        elif re.match("^[0-9+]*$", info[key]):
                            self.buyinCurrency="play"
                        else:
                            #FIXME: handle other currencies, play money
                            log.error("PokerStarsToFpdb.readHandInfo: Failed to detect currency." + " Hand ID: %s: '%s'" % (selfid, info[key]))
                            raise FpdbParseError

                        info['BIAMT'] = info['BIAMT'].strip(u'$€£FPP')

                        if self.buyinCurrency!="PSFP":
                            if info['BOUNTY'] != None:
                                # There is a bounty, Which means we need to switch BOUNTY and BIRAKE values
                                tmp = info['BOUNTY']
                                info['BOUNTY'] = info['BIRAKE']
                                info['BIRAKE'] = tmp
                                info['BOUNTY'] = info['BOUNTY'].strip(u'$€£') # Strip here where it isn't 'None'
                                self.koBounty = int(100*Decimal(info['BOUNTY']))
                                self.isKO = True
                            else:
                                self.isKO = False

                            info['BIRAKE'] = info['BIRAKE'].strip(u'$€£')

                            self.buyin = int(100*Decimal(info['BIAMT']))
                            self.fee = int(100*Decimal(info['BIRAKE']))
                        else:
                            self.buyin = int(Decimal(info['BIAMT']))
                            self.fee = 0
            if key == 'LEVEL':
                self.level = info[key]

            if key == 'TABLE':
                if self.tourNo != None:
                    self.tablename = re.split(" ", info[key])[1]
                else:
                    self.tablename = info[key]
            if key == 'BUTTON':
                self.buttonpos = info[key]
            if key == 'MAX' and info[key] != None:
                self.maxseats = int(info[key])

        if PokerStars.re_Cancelled.search(self.handText):
            raise FpdbHandPartial("Hand '%s' was cancelled." % self.handid)

    def readPlayerStacks(self, hand):
        log.debug("readPlayerStacks")
        m = PokerStars.re_PlayerInfo.finditer(self.handText)
        for a in m:
            self.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):

        # There is no marker between deal and draw in Stars single draw games
        #  this upsets the accounting, incorrectly sets handsPlayers.cardxx and
        #  in consequence the mucked-display is incorrect.
        # Attempt to fix by inserting a DRAW marker into the hand text attribute

        if self.gametype['category'] in ('27_1draw', 'fivedraw'):
            # isolate the first discard/stand pat line (thanks Carl for the regex)
            discard_split = re.split(r"(?:(.+(?: stands pat|: discards).+))", self.handText,re.DOTALL)
            if len(self.handText) == len(discard_split[0]):
                # handText was not split, no DRAW street occurred
                pass
            else:
                # DRAW street found, reassemble, with DRAW marker added
                discard_split[0] += "*** DRAW ***\r\n"
                self.handText = ""
                for i in discard_split:
                    self.handText += i

        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        if self.gametype['base'] in ("hold"):
            m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                       r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S \S\S \S\S\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                       r"(\*\*\* TURN \*\*\* \[\S\S \S\S \S\S] (?P<TURN>\[\S\S\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
                       r"(\*\*\* RIVER \*\*\* \[\S\S \S\S \S\S \S\S] (?P<RIVER>\[\S\S\].+))?", self.handText,re.DOTALL)
        elif self.gametype['base'] in ("stud"):
            m =  re.search(r"(?P<ANTES>.+(?=\*\*\* 3rd STREET \*\*\*)|.+)"
                           r"(\*\*\* 3rd STREET \*\*\*(?P<THIRD>.+(?=\*\*\* 4th STREET \*\*\*)|.+))?"
                           r"(\*\*\* 4th STREET \*\*\*(?P<FOURTH>.+(?=\*\*\* 5th STREET \*\*\*)|.+))?"
                           r"(\*\*\* 5th STREET \*\*\*(?P<FIFTH>.+(?=\*\*\* 6th STREET \*\*\*)|.+))?"
                           r"(\*\*\* 6th STREET \*\*\*(?P<SIXTH>.+(?=\*\*\* RIVER \*\*\*)|.+))?"
                           r"(\*\*\* RIVER \*\*\*(?P<SEVENTH>.+))?", self.handText,re.DOTALL)
        elif self.gametype['base'] in ("draw"):
            if self.gametype['category'] in ('27_1draw', 'fivedraw'):
                m =  re.search(r"(?P<PREDEAL>.+(?=\*\*\* DEALING HANDS \*\*\*)|.+)"
                           r"(\*\*\* DEALING HANDS \*\*\*(?P<DEAL>.+(?=\*\*\* DRAW \*\*\*)|.+))?"
                           r"(\*\*\* DRAW \*\*\*(?P<DRAWONE>.+))?", self.handText,re.DOTALL)
            else:
                m =  re.search(r"(?P<PREDEAL>.+(?=\*\*\* DEALING HANDS \*\*\*)|.+)"
                           r"(\*\*\* DEALING HANDS \*\*\*(?P<DEAL>.+(?=\*\*\* FIRST DRAW \*\*\*)|.+))?"
                           r"(\*\*\* FIRST DRAW \*\*\*(?P<DRAWONE>.+(?=\*\*\* SECOND DRAW \*\*\*)|.+))?"
                           r"(\*\*\* SECOND DRAW \*\*\*(?P<DRAWTWO>.+(?=\*\*\* THIRD DRAW \*\*\*)|.+))?"
                           r"(\*\*\* THIRD DRAW \*\*\*(?P<DRAWTHREE>.+))?", self.handText,re.DOTALL)
        self.addStreets(m)

    def readBlinds(self, hand):
        liveBlind = True
        for a in PokerStars.re_PostSB.finditer(self.handText):
            if liveBlind:
                self.addBlind(a.group('PNAME'), 'small blind', a.group('SB'))
                liveBlind = False
            else:
                # Post dead blinds as ante
                self.addBlind(a.group('PNAME'), 'secondsb', a.group('SB'))
        for a in PokerStars.re_PostBB.finditer(self.handText):
            self.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
        for a in PokerStars.re_PostBoth.finditer(self.handText):
            self.addBlind(a.group('PNAME'), 'both', a.group('SBBB'))

    def readAntes(self, hand):
        log.debug("reading antes")
        m = PokerStars.re_Antes.finditer(self.handText)
        for player in m:
            #~ logging.debug("self.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            self.addAnte(player.group('PNAME'), player.group('ANTE'))

    def readButton(self, hand):
        m = PokerStars.re_Button.search(self.handText)
        if m:
            self.buttonpos = int(m.group('BUTTON'))
        else:
            log.info('readButton: ' + _('not found'))

    def readHeroCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        for street in ('PREFLOP', 'DEAL'):
            if street in self.streets.keys():
                m = PokerStars.re_HeroCards.finditer(self.streets[street])
                for found in m:
#                    if m == None:
#                        self.involved = False
#                    else:
                    self.hero = found.group('PNAME')
                    newcards = found.group('NEWCARDS').split(' ')
                    self.addHoleCards(street, self.hero, closed=newcards, shown=False, mucked=False, dealt=True)

        for street, text in self.streets.items():
            if not text or street in ('PREFLOP', 'DEAL'): continue  # already done these
            m = PokerStars.re_HeroCards.finditer(self.streets[street])
            for found in m:
                player = found.group('PNAME')
                if found.group('NEWCARDS') is None:
                    newcards = []
                else:
                    newcards = found.group('NEWCARDS').split(' ')
                if found.group('OLDCARDS') is None:
                    oldcards = []
                else:
                    oldcards = found.group('OLDCARDS').split(' ')

                if street == 'THIRD' and len(newcards) == 3: # hero in stud game
                    self.hero = player
                    self.dealt.add(player) # need this for stud??
                    self.addHoleCards(street, player, closed=newcards[0:2], open=[newcards[2]], shown=False, mucked=False, dealt=False)
                else:
                    self.addHoleCards(street, player, open=newcards, closed=oldcards, shown=False, mucked=False, dealt=False)

    def readShowdownActions(self, hand):
# TODO: pick up mucks also??
        for shows in PokerStars.re_ShowdownAction.finditer(self.handText):
            cards = shows.group('CARDS').split(' ')
            self.addShownCards(cards, shows.group('PNAME'))

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, self.streets.group(street)
            m = PokerStars.re_Board.search(self.streets[street])
            self.setCommunityCards(street, m.group('CARDS').split(' '))

    def readAction(self, hand, street):
        m = PokerStars.re_Action.finditer(self.streets[street])
        for action in m:
            acts = action.groupdict()
            #print "DEBUG: acts: %s" %acts
            if action.group('ATYPE') == ' folds':
                self.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                self.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' calls':
                self.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' raises':
                self.addRaiseBy( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' bets':
                self.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' discards':
                self.addDiscard(street, action.group('PNAME'), action.group('BET'), action.group('CARDS'))
            elif action.group('ATYPE') == ' stands pat':
                self.addStandsPat( street, action.group('PNAME'), action.group('CARDS'))
            else:
                print ("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'" % ("readAction", action.group('PNAME'), action.group('ATYPE')))

    def readCollectPot(self,hand):
        i=0
        for m in PokerStars.re_CollectPot.finditer(self.handText):
            self.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))
            i+=1
        if i==0:
            for m in PokerStars.re_CollectPot2.finditer(self.handText):
                self.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        for m in PokerStars.re_ShownCards.finditer(self.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(' ') # needs to be a list, not a set--stud needs the order
                string = m.group('STRING')

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "showed": shown = True
                elif m.group('SHOWED') == "mucked": mucked = True

                #print "DEBUG: self.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                self.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked, string=string)
