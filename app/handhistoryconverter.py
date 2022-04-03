#!/usr/bin/env python3

# TODO: Prévoir l'extraction d'un fichier de HH complet pour récupérer les informations de la main
import time
from datetime import datetime
from pytz import timezone
import pytz
import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("parser")
import re
import codecs

from app import db, app
from app.models import PokerHH
import app.pokerstars as pokerstars
from app.exceptions import *
from app.hand import *
from app.email import send_following_hh


class HandHistoryConverter:

    re_SplitHands = re.compile('(?:\s?\n){2,}')
    re_tzOffset = re.compile('^\w+[+-]\d{4}$')
    re_room = re.compile(r'PokerStars|Winamax', re.IGNORECASE)

    def __init__(self, userid, files):
        self.files = files  # liste de fichiers
        self.userid = userid
        self.room = ''
        self.processedHands = []
        self.numHands = 0
        self.numErrors = 0
        self.numPartial = 0
        self.numDuplicate = 0
        self.toterrors = 0
        self.whole_file = ''
        self.hhctime = time.time()
        self.message = []
        self.start()

    def start(self):
        self.hhctime = time.time()
        handsList = self.allHandsAsList()
        following_hh = []

        for handText in handsList:
            try:
                self.processedHands.append(self.processHand(handText))
            except FpdbHandPartial as e:
                self.numPartial += 1
                app.logger.info("%s" % e)
            except FpdbParseError as e:
                self.numErrors += 1
                app.logger.info("Erreur rencontrée pour le fichier {} : {}".format(self.file, e))
            except HandDuplicate as e:
                self.numDuplicate += 1
                app.logger.info("Cette main est déjà dans la base de données", e)
        self.toterrors = self.numErrors + self.numPartial + self.numDuplicate
        self.numHands = len(handsList) - self.toterrors
        self.hhctime = time.time() - self.hhctime
        self.message.append("%d mains importée(s) (%d erreur(s)) en %.3f secondes" %
                            (self.numHands, self.toterrors, self.hhctime))
        if (self.numPartial + self.numErrors) > 0:
            self.message.append("%d mains non exploitable(s) (voir log)" % (self.numPartial + self.numErrors))
        if self.numDuplicate > 0:
            self.message.append("%d mains déjà présente(s) dans la base de données" % self.numDuplicate)

    def allHandsAsList(self):
        handlist = []
        for self.file in self.files:
            self.readFile()
            self.whole_file = self.whole_file.strip()
            self.whole_file = self.whole_file.replace('\r\n', '\n')

            if self.whole_file is None or self.whole_file == "":
                app.logger.info("Aucune main dans ce fichier : '%s'" % self.file)
            handlist_file = re.split(self.re_SplitHands,  self.whole_file)
            # Some HH formats leave dangling text after the split
            # ie. </game> (split) </session>EOL
            # Remove this dangler if less than 50 characters and warn in the log
            handlist.extend(handlist_file)
        if len(handlist[-1]) <= 50:
            handlist.pop()
            log.info("Removing text < 50 characters")
        return handlist

    def __listof(self, x):
        if isinstance(x, list) or isinstance(x, tuple):
            return x
        else:
            return [x]

    def readFile(self):
        """Open in_path according to self.codepage. Exceptions caught further up"""

        if self.file.split('.')[-1] == "txt":
            for kodec in self.__listof('utf8'):
                #print "trying", kodec
                try:
                    in_fh = codecs.open(self.file, 'r', kodec, 'ignore')
                    self.whole_file = in_fh.read()
                    in_fh.close()
                    return True
                except:
                    pass
            else:
                app.logger.info(" '%s' : unable to read file with any codec in list!" % self.file)
                self.whole_file = ""
                return False
        else:
            app.logger.info(" '%s' : Le format de fichier n'est pas pris en charge!" % self.file.split('.')[-1])

    def processHand(self, handText):

        if self.re_room.search(handText) is None:
            raise FpdbParseError("Seules les HH de PokerStars et Winamax sont prises en charge")
        else:
            self.room = self.re_room.findall(handText)[0]
            roomclass = eval(self.room.lower() + '.' + self.room + '()')
            gametype = roomclass.determineGameType(handText)
            hand = None
            if gametype is None:
                gametype = "unmatched"
                # TODO: not ideal, just trying to not error. Throw ParseException?
                raise FpdbParseError()
            if gametype['category'] != 'holdem':
                erreur = "le format {} n'est pas pris en charge".format(gametype['category'])
                raise FpdbParseError(erreur)
            if gametype['limitType'] != 'nl':
                erreur = "le format {} n'est pas pris en charge".format(gametype['limitType'])
                raise FpdbParseError(erreur)
            if gametype['type'] != 'ring':
                erreur = "le format {} n'est pas pris en charge".format(gametype['type'])
                raise FpdbParseError(erreur)
            else:
                # See if gametype is supported.
                hand = Hand(gametype, handText, self.userid, self.room)
                if hand:
                    return hand
                else:
                    print("LOG: %s Unsupported game type: %s" % (self.sitename, gametype))
                    # TODO: pity we don't know the HID at this stage. Log the entire hand?

    def getRake(self, hand):
        self.rake = self.totalpot - self.totalcollected #  * Decimal('0.05') # probably not quite right
        if self.rake < 0 and (not self.roundPenny or self.rake < 0.01):
            log.error("hhc.getRake(): '%s': Amount collected (%s) is greater than the pot (%s)" % (self.handid, str(self.totalcollected), str(self.totalpot)))
            raise FpdbParseError
        elif self.totalpot > 0 and Decimal(self.totalpot/4) < self.rake:
            log.error("hhc.getRake(): '%s': Suspiciously high rake (%s) > 25 pct of pot (%s)" % (self.handid, str(self.rake), str(self.totalpot)))
            raise FpdbParseError

    def recup_data(self, hand):
        HH_id = 'PS:' + self.handid
        stakes = self.gametype['limitType'].upper() + "{:.0f}".format(Decimal(self.bb)*100)
        cards = self.holecards['PREFLOP'][self.hero][1][0]+' '+self.holecards['PREFLOP'][self.hero][1][1]
        if self.hero in self.collectees.keys():
            gain = self.collectees[self.hero] - self.pot.committed[self.hero]
        else:
            gain = -self.pot.committed[self.hero]
        bbs = float(gain/Decimal(self.bb))
        combo = self.Types_Hands(cards)[0]
        hand_type = self.Types_Hands(cards)[1]
        hero_PFAction = ''.join(self.actionsHero['PREFLOP'])
        hero_PFAction_simpl = ''.join(re.findall('[A-Z]', hero_PFAction))
        nb_joueur = len(self.players)
        joueurs = []
        bouton = ''
        Positions = dict()
        position = ''
        Raisers = []
        FirstRaiser = ''
        for ply in self.players:
            joueurs.append(ply[1])
            if ply[0] == self.buttonpos:
                bouton = ply[1]
        # TODO: A revoir et créer dict avec pos + players pour obtenir facilement la position de chaque joueur
        for i in range(joueurs.index(bouton)):
            joueurs.append(joueurs.pop(0))

        if len(self.players) == 2:
            Positions = dict(zip(joueurs, ['SB', 'BB']))
        elif len(self.players) == 3:
            Positions = dict(zip(joueurs, ['BU', 'SB', 'BB']))
        else:
            joueurs_inv = joueurs.copy()
            joueurs_inv.reverse()
            Positions = dict(zip(joueurs[:3]+joueurs_inv[:(len(joueurs)-3)],
                                 ['BU', 'SB', 'BB', 'CO', 'MP', 'UTG']))

        position = Positions[self.hero]

        for a in self.actions['PREFLOP']:
            if a[1] == 'raises':
                Raisers.append(a[0])
        if len(Raisers) > 0:
            firstraiser = Positions[Raisers[0]]
        else:
            firstraiser = 'N/A'

        # TODO: extrait le gagnant de la main.. si plusieurs gagant on prend que le premier -> A améliorer?
        winner = self.collected[0][0]

        facing_preflop = ''
        PFAction = []
        for i in self.actions['PREFLOP']:
            if i[0] != self.hero:
                PFAction.append(i[1])
            else:
                break
        if (len(list(set(PFAction))) == 1 and list(set(PFAction))[0] == 'folds') or len(PFAction) == 0:  # que des folds ou premier de parole
            facing_preflop = 'Unopened'
        else:
            if 'raises' not in PFAction:
                if (PFAction.count('calls') + PFAction.count('checks')) == 1:
                    facing_preflop = '1 Limper'
                else: facing_preflop = '2+ Limpers'
            elif PFAction.count('raises') == 1:
                del PFAction[0:PFAction.index('raises')]
                if 'calls' in PFAction and PFAction.index('calls') > PFAction.index('raises'):
                    facing_preflop = 'Raiser + Caller(s)'
                else: facing_preflop = '1 Raiser'
            else: facing_preflop = '2+ Raisers'

        sawflop = False
        for i in self.actions['FLOP']:
            if i[0] == self.hero:
                sawflop = True
                break

        flop = ''
        turn = ''
        river = ''
        type_flop = ''
        flop_simpl = ''
        hero_line_F_simpl = ''
        hero_line_T_simpl = ''
        hero_line_R_simpl = ''
        hero_line_F = ''
        hero_line_T = ''
        hero_line_R = ''
        hero_line = ''
        nb_joueur_flop = 0
        sawshowdown = False

        if sawflop:
            joueur_flop = []
            for a in self.actions['FLOP']:
                joueur_flop.append(a[0])
            nb_joueur_flop = len(list(set(joueur_flop)))
            flop = ''.join(self.board['FLOP'])
            suit = []
            if flop[0] == flop[2] and flop[2] == flop[4]:
                type_flop = 'T'  #trips 3 cartes identiques
            elif flop[0] != flop[2] and flop[2] != flop[4] and flop[0] != flop[4]:
                type_flop = 'U' #unpaired 3 cartes différentes
            else:
                type_flop = 'P' #paired 2 cartes identiques

            if flop[1] == flop[3] and flop[1] == flop[5]:
                suit = ['sss', 'M'] #monocolore
            elif flop[1] == flop[3] or flop[1] == flop[5] or flop[3] == flop[5]:
                suit = ['ss', 'S'] #suited
            else:
                suit = ['r', 'R'] #rainbow

            list_flop = dict()
            for i in range(0, len(flop), 2):
                list_flop[i] = self.ranks.index(flop[i])
            nb_9 = 0
            for c in sorted(list_flop.items(), key=lambda t: t[1], reverse=True):
                flop_simpl += self.ranks[c[1]]
                if c[1] < 7:
                    nb_9 += 1  # nombre de cartes en dessous de 9
            flop_simpl += suit[0]

            type_flop += str(self.ranks[max(list_flop.values())])+str(suit[1])+str(nb_9)

            hero_line_F = ''.join(self.actionsHero['FLOP'])
            hero_line_F_simpl = ''.join(re.findall('[A-Z]', hero_line_F))

            if len(self.board['TURN']) > 0:
                turn = ''.join(self.board['TURN'])

            hero_line_T = ''.join(self.actionsHero['TURN'])
            hero_line_T_simpl = ''.join(re.findall('[A-Z]', hero_line_T))

            if len(self.board['RIVER']) > 0:
                river = ''.join(self.board['RIVER'])

            hero_line_R = ''.join(self.actionsHero['RIVER'])
            hero_line_R_simpl = ''.join(re.findall('[A-Z]', hero_line_R))

            hero_line = hero_line_F_simpl + ' ' + hero_line_T_simpl + ' ' + hero_line_R_simpl
            hero_line = hero_line.strip()

            sawshowdown = self.sawshowdown

            # Suivi de mains spéciales pour progresser
            if position == 'BB':
                if (firstraiser == 'BU') and (facing_preflop == '1 Raiser') and (nb_joueur > 2) \
                        and (sawshowdown is True):
                    if type_flop in ['UQS1', 'U9S2', 'U5S3', 'UJS1']:
                        send_following_hh(self.handid, '[6maxpokerrange] - Mains à revoir BB vs BU [spot résolu]')
                    else:
                        send_following_hh(self.handid, '[6maxpokerrange] - Mains à revoir BB vs BU')
                elif bbs < -20:
                    send_following_hh(self.handid, '[6maxpokerrange] - Mains à revoir gros pot perdu en BB')
                else:
                    pass

        query = PokerHH.query.filter_by(hand_id='PS:'+self.handid).first()

        if query is None:
            add_hh = PokerHH(hand_id=HH_id, user_id=self.userid, room=self.room,
                             timestamp=self.startTime, level=stakes, cards=cards, bbs=bbs, combo=combo,
                             hand_type=hand_type, hero_PFAction=hero_PFAction, hero_PFAction_simpl=hero_PFAction_simpl,
                             nb_joueur=nb_joueur, position=position, firstraiser=firstraiser, winner=winner,
                             facing_preflop=facing_preflop, sawflop=sawflop, flop=flop, type_flop=type_flop,
                             flop_simpl=flop_simpl, nb_joueur_flop=nb_joueur_flop, hero_line_F=hero_line_F,
                             turn=turn, hero_line_T=hero_line_T, river=river, hero_line_R=hero_line_R,
                             hero_line=hero_line, sawshowdown=sawshowdown)
            db.session.add(add_hh)
            db.session.commit()
        else:
            raise HandDuplicate(HH_id)

    def replace(string):

        substitutions = {'folds': 'F', 'calls': 'C', 'raises': 'R', 'checks': 'X', 'bets': 'B'}
        substrings = sorted(substitutions, key=len, reverse=True)
        regex = re.compile('|'.join(map(re.escape, substrings)))
        return regex.sub(lambda match: substitutions[match.group(0)], string)


    # These functions are parse actions that may be overridden by the inheriting class
    # This function should return a list of lists looking like:
    # return [["ring", "hold", "nl"], ["tour", "hold", "nl"]]
    # Showing all supported games limits and types
    @staticmethod
    def changeTimezone(time, givenTimezone, wantedTimezone):
        """Takes a givenTimezone in format AAA or AAA+HHMM where AAA is a standard timezone
           and +HHMM is an optional offset (+/-) in hours (HH) and minutes (MM)
           (See OnGameToFpdb.py for example use of the +HHMM part)
           Tries to convert the time parameter (with no timezone) from the givenTimezone to
           the wantedTimeZone (currently only allows "UTC")
        """
        #log.debug("raw time: " + str(time) + " given time zone: " + str(givenTimezone))
        if wantedTimezone == "UTC":
            wantedTimezone = pytz.utc
        else:
            log.error("Unsupported target timezone: " + givenTimezone)
            raise FpdbParseError("Unsupported target timezone: " + givenTimezone)

        givenTZ = None
        if HandHistoryConverter.re_tzOffset.match(givenTimezone):
            offset = int(givenTimezone[-5:])
            givenTimezone = givenTimezone[0:-5]
            #log.debug("changeTimeZone: offset=") + str(offset))
        else: offset=0

        if (givenTimezone=="ET" or givenTimezone=="EST" or givenTimezone=="EDT"):
            givenTZ = timezone('US/Eastern')
        elif (givenTimezone=="CET" or givenTimezone=="CEST" or givenTimezone=="MESZ"):
            #since CEST will only be used in summer time it's ok to treat it as identical to CET.
            givenTZ = timezone('Europe/Berlin')
            #Note: Daylight Saving Time is standardised across the EU so this should be fine
        elif givenTimezone == 'GMT': # GMT is always the same as UTC
            givenTZ = timezone('GMT')
            # GMT cannot be treated as WET because some HH's are explicitly
            # GMT+-delta so would be incorrect during the summertime
            # if substituted as WET+-delta
        elif givenTimezone == 'BST':
             givenTZ = timezone('Europe/London')
        elif givenTimezone == 'WET': # WET is GMT with daylight saving delta
            givenTZ = timezone('WET')
        elif givenTimezone == 'HST': # Hawaiian Standard Time
            givenTZ = timezone('US/Hawaii')
        elif givenTimezone == 'AKT': # Alaska Time
            givenTZ = timezone('US/Alaska')
        elif givenTimezone == 'PT': # Pacific Time
            givenTZ = timezone('US/Pacific')
        elif givenTimezone == 'MT': # Mountain Time
            givenTZ = timezone('US/Mountain')
        elif givenTimezone == 'CT': # Central Time
            givenTZ = timezone('US/Central')
        elif givenTimezone == 'AT': # Atlantic Time
            givenTZ = timezone('Canada/Atlantic')
        elif givenTimezone == 'NT': # Newfoundland Time
            givenTZ = timezone('Canada/Newfoundland')
        elif givenTimezone == 'ART': # Argentinian Time
            givenTZ = timezone('America/Argentina/Buenos_Aires')
        elif givenTimezone == 'BRT': # Brasilia Time
            givenTZ = timezone('America/Sao_Paulo')
        elif givenTimezone == 'COT':
            givenTZ = timezone('America/Bogota')
        elif givenTimezone in ('EET', 'EEST'): # Eastern European Time
            givenTZ = timezone('Europe/Bucharest')
        elif givenTimezone in ('MSK', 'MESZ', 'MSKS'): # Moscow Standard Time
            givenTZ = timezone('Europe/Moscow')
        elif givenTimezone in ('YEKT','YEKST'):
            givenTZ = timezone('Asia/Yekaterinburg')
        elif givenTimezone in ('KRAT','KRAST'):
            givenTZ = timezone('Asia/Krasnoyarsk')
        elif givenTimezone == 'IST': # India Standard Time
            givenTZ = timezone('Asia/Kolkata')
        elif givenTimezone == 'CCT': # China Coast Time
            givenTZ = timezone('Australia/West')
        elif givenTimezone == 'JST': # Japan Standard Time
            givenTZ = timezone('Asia/Tokyo')
        elif givenTimezone == 'AWST': # Australian Western Standard Time
            givenTZ = timezone('Australia/West')
        elif givenTimezone == 'ACST': # Australian Central Standard Time
            givenTZ = timezone('Australia/Darwin')
        elif givenTimezone == 'AEST': # Australian Eastern Standard Time
            # Each State on the East Coast has different DSTs.
            # Melbournce is out because I don't like AFL, Queensland doesn't have DST
            # ACT is full of politicians and Tasmania will never notice.
            # Using Sydney.
            givenTZ = timezone('Australia/Sydney')
        elif givenTimezone == 'NZT': # New Zealand Time
            givenTZ = timezone('Pacific/Auckland')

        if givenTZ is None:
            # do not crash if timezone not in list, just return UTC localized time
            log.warn("Timezone conversion not supported" + ": " + givenTimezone + " " + str(time))
            givenTZ = pytz.UTC
            return givenTZ.localize(time)

        localisedTime = givenTZ.localize(time)
        utcTime = localisedTime.astimezone(wantedTimezone) + datetime.timedelta(seconds=-3600*(offset/100)-60*(offset%100))
        return utcTime
    #end @staticmethod def changeTimezone
