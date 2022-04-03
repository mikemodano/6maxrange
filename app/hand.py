#!/usr/bin/env python3
import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("parser")
from decimal import *
import datetime

import app.handhistoryconverter as hhc
import app.pokerstars as ps
from app.exceptions import *


class Hand(object):

    UPS = {'a':'A', 't':'T', 'j':'J', 'q':'Q', 'k':'K', 'S':'s', 'C':'c', 'H':'h', 'D':'d'}

    def __init__(self, gametype, handText, userid, room):

        self.handText = handText
        self.userid = userid
        self.room = room
        self.allStreets = ['BLINDSANTES', 'PREFLOP', 'FLOP', 'TURN', 'RIVER']
        self.holeStreets = ['PREFLOP']
        self.communityStreets = ['FLOP', 'TURN', 'RIVER']
        self.actionStreets = ['BLINDSANTES','PREFLOP','FLOP','TURN','RIVER']
        self.ranks = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
        self.suits = ['c','s','d','h']
        self.position = ['BU', 'SB', 'BB', 'UTG', 'MP', 'CO']
        self.gametype = gametype
        self.sb = gametype['sb']
        self.bb = gametype['bb']
        self.startTime = 0
        self.handid = 0
        self.tablename = ""
        self.hero = ""
        self.maxseats = None
        self.buttonpos = 0
        self.level = None
        self.players = []
        self.posted = []
        self.stacks = {}
        self.bets = {}
        self.lastBet = {}
        self.streets = {}
        self.actions = {} # [['mct','bets','$10'],['mika','folds'],['carlg','raises','$20']]
        self.actionsHero = {} # ajouter pour avoir les montants en BB PF et rapportés au pot post-flop
        self.board = {} # dict from street names to community cards
        self.holecards = {}
        self.discards = {}
        self.showdownStrings = {}
        self.cancelled = False
        self.uncalledbets = False
        self.sawshowdown = False

        # Sets of players
        self.folded = set()
        self.dealt = set()  # 'dealt to' line to be printed
        self.shown = set()  # cards were shown
        self.mucked = set() # cards were mucked at showdown

        self.collected = [] #list of ?
        self.collectees = {} # dict from player names to amounts collected (?)

        #tourney stuff
        self.tourNo = None
        self.buyin = None
        self.buyinCurrency = None
        self.fee = None  # the Database code is looking for this one .. ?
        self.koBounty = 0
        self.isKO = False

        #ajouter pour tableau
        self.gain = 0

        for street in self.allStreets:
            self.streets[street] = "" # portions of the handText, filled by markStreets()
            self.actions[street] = []
            self.actionsHero[street] = []
        for street in self.actionStreets:
            self.bets[street] = {}
            self.lastBet[street] = 0
            self.board[street] = []
        for street in self.holeStreets:
            self.holecards[street] = {} # dict from player names to holecards
            self.discards[street] = {} # dict from player names to dicts by street ... of tuples ... of discarded holecards

        # Things to do with money
        self.pot = Pot()
        self.totalpot = None
        self.totalcollected = None
        self.rake = None
        self.roundPenny = False

        self.Hero_PFActions = []

        self.start()

    def start(self):

        ps.PokerStars.readHandInfo(self, self.handText)
        if self.gametype['type'] == 'tour':
            self.tablename = "%s %s" % (self.tourNo, self.tablename)
        ps.PokerStars.readPlayerStacks(self, self.handText)
        ps.PokerStars.markStreets(self, self.handText)
        ps.PokerStars.readBlinds(self, self.handText)
        ps.PokerStars.readAntes(self, self.handText)
        ps.PokerStars.readButton(self, self.handText)
        ps.PokerStars.readHeroCards(self, self.handText)
        ps.PokerStars.readShowdownActions(self, self.handText)
        for street, text in self.streets.items():
            if text and (
                    street != "PREFLOP"):  # TODO: the except PREFLOP shouldn't be necessary, but regression-test-files/cash/Everleaf/Flop/NLHE-10max-USD-0.01-0.02-201008.2Way.All-in.pre.txt fails without it
                ps.PokerStars.readCommunityCards(self, self.handText, street)
        for street in self.actionStreets:
            if self.streets[street]:
                ps.PokerStars.readAction(self, self.handText, street)
                self.pot.markTotal(street)
        ps.PokerStars.readCollectPot(self, self.handText)
        ps.PokerStars.readShownCards(self, self.handText)
        self.pot.handid = self.handid  # This is only required so Pot can throw it in totalPot
        self.totalPot()  # finalise it (total the pot)
        hhc.HandHistoryConverter.getRake(self, self.handText)

        p_in = set([x[0] for x in self.actions[self.actionStreets[1]]])
        if self.pot.pots:
            if len(self.pot.pots[0][1]) > 1:
                p_in = p_in.union(self.pot.pots[0][1])
        for (i, street) in enumerate(self.actionStreets):
            actions = self.actions[street]
            p_in = p_in - self.pfba(actions, l=('folds',))
        if len(p_in) > 1:
            self.sawshowdown = True

        hhc.HandHistoryConverter.recup_data(self, self.userid)

    def addPlayer(self, seat, name, chips, position=None):
        if chips is not None:
            chips = chips.replace(u',', u'')  # some sites have commas
            self.players.append([seat, name, chips,
                                 position])  # removed most likely unused 0s from list and added position... former list: [seat, name, chips, 0, 0]
            self.stacks[name] = Decimal(chips)
            self.pot.addPlayer(name)
            for street in self.actionStreets:
                self.bets[street][name] = []
                # self.holecards[name] = {} # dict from street names.
                # self.discards[name] = {} # dict from street names.

    def addPlayer(self, seat, name, chips, position=None):
        if chips is not None:
            chips = chips.replace(u',', u'') #some sites have commas
            self.players.append([seat, name, chips, position]) #removed most likely unused 0s from list and added position... former list: [seat, name, chips, 0, 0]
            self.stacks[name] = Decimal(chips)
            self.pot.addPlayer(name)
            for street in self.actionStreets:
                self.bets[street][name] = []
                #self.holecards[name] = {} # dict from street names.
                #self.discards[name] = {} # dict from street names.

    def addStreets(self, match):
        # go through m and initialise actions to empty list for each street.
        if match:
            self.streets.update(match.groupdict())
        else:
            tmp = self.handText[0:100]
            self.cancelled = True
            raise FpdbHandPartial("Streets didn't match - Assuming hand '%s' was cancelled." % (self.handid) + " " + "First 100 characters: %s" % tmp)

    def addBlind(self, player, blindtype, amount):
        if player is not None:
            self.checkPlayerExists(player, 'addBlind')
            amount = amount.replace(u',', u'') #some sites have commas
            amount = Decimal(amount)
            self.stacks[player] -= amount
            act = (player, blindtype, amount, self.stacks[player]==0)
            self.actions['BLINDSANTES'].append(act)

            if blindtype == 'both':
                # work with the real amount. limit games are listed as $1, $2, where
                # the SB 0.50 and the BB is $1, after the turn the minimum bet amount is $2....
                amount = Decimal(str(self.bb))
                sb = Decimal(str(self.sb))
                self.bets['BLINDSANTES'][player].append(sb)
                self.pot.addCommonMoney(player, sb)

            if blindtype == 'secondsb':
                amount = Decimal(0)
                sb = Decimal(str(self.sb))
                self.bets['BLINDSANTES'][player].append(sb)
                self.pot.addCommonMoney(player, sb)

            street = 'BLAH'

            if self.gametype['base'] == 'hold':
                street = 'PREFLOP'
            elif self.gametype['base'] == 'draw':
                street = 'DEAL'

            self.bets[street][player].append(amount)
            self.pot.addMoney(player, amount)
            if amount > self.lastBet.get(street):
                self.lastBet[street] = amount
            self.posted = self.posted + [[player, blindtype]]

    def checkPlayerExists(self, player, source=None):
        if player not in [p[1] for p in self.players]:
            if source is not None:
                print("Hand.%s: '%s' unknown player: '%s'" % (source, self.handid, player))
            raise FpdbParseError

    def addAnte(self, player, ante):
        if player is not None:
            ante = ante.replace(u',', u'') #some sites have commas
            self.checkPlayerExists(player, 'addAnte')
            ante = Decimal(ante)
            self.bets['BLINDSANTES'][player].append(ante)
            self.stacks[player] -= ante
            act = (player, 'ante', ante, self.stacks[player]==0)
            self.actions['BLINDSANTES'].append(act)
            self.pot.addCommonMoney(player, ante)
            if not 'ante' in self.gametype.keys() or self.gametype['ante'] == 0:
                self.gametype['ante'] = ante
            # I think the antes should be common money, don't have enough hand history to check

    def addHoleCards(self, street, player, open=[], closed=[], shown=False, mucked=False, dealt=False):
        self.checkPlayerExists(player, 'addHoleCards')
        if dealt:  self.dealt.add(player)
        if shown:  self.shown.add(player)
        if mucked: self.mucked.add(player)
        for i in range(len(closed)):
            if closed[i] in ('', 'Xx', 'Null', 'null'):
                closed[i] = '0x'

        try:
            self.holecards[street][player] = [open, closed]
        except KeyError as e:
            print("Hand.addHoleCards: '%s': Major failure while adding holecards: '%s'" % (self.handid, e))
            raise FpdbParseError

    def addShownCards(self, cards, player, shown=True, mucked=False, dealt=False, string=None):
        if player == self.hero: # we have hero's cards just update shown/mucked
            if shown:  self.shown.add(player)
            if mucked: self.mucked.add(player)
        else:
            if len(cards) in (2, 3, 4) or self.gametype['category']=='5_omahahi':  # avoid adding board by mistake (Everleaf problem)
                self.addHoleCards('PREFLOP', player, open=[], closed=cards, shown=shown, mucked=mucked, dealt=dealt)
            elif len(cards) == 5:     # cards holds a winning hand, not hole cards
                # filter( lambda x: x not in b, a )             # calcs a - b where a and b are lists
                # so diff is set to the winning hand minus the board cards, if we're lucky that leaves the hole cards
                diff = filter( lambda x: x not in self.board['FLOP']+self.board['TURN']+self.board['RIVER'], cards )
                if len(diff) == 2 and self.gametype['category'] in ('holdem'):
                    self.addHoleCards('PREFLOP', player, open=[], closed=diff, shown=shown, mucked=mucked, dealt=dealt)
        if string is not None:
            self.showdownStrings[player] = string

    def setCommunityCards(self, street, cards):
        self.board[street] = [self.card(c) for c in cards]
#        print "DEBUG: self.board: %s" % self.board

    def card(self,c):
        """upper case the ranks but not suits, 'atjqk' => 'ATJQK'"""
        for k,v in list(self.UPS.items()):
            c = c.replace(k, v)
        return c

    def addFold(self, street, player):
        self.checkPlayerExists(player, 'addFold')
        self.folded.add(player)
        self.pot.addFold(player)
        self.actions[street].append((player, 'folds'))
        if player == self.hero:
            if street == 'PREFLOP':
                self.actionsHero[street].append('F'+'{:.4g}'.format(self.lastBet[street]/Decimal(str(self.bb))))
            else:
                self.actionsHero[street].append('F'+'{:.2f}'.format(self.lastBet[street]/(sum(self.pot.committed.values()) + sum(self.pot.common.values()) - self.lastBet[street])))

    def addCheck(self, street, player):
        #print "DEBUG: %s %s checked" % (street, player)
        logging.debug("%s %s checks" % (street, player))
        self.checkPlayerExists(player, 'addCheck')
        self.actions[street].append((player, 'checks'))
        if player == self.hero:
            self.actionsHero[street].append('X')

    def addCall(self, street, player=None, amount=None):
        if amount is not None:
            amount = amount.replace(u',', u'') #some sites have commas
        # Potentially calculate the amount of the call if not supplied
        # corner cases include if player would be all in
        if amount is not None:
            self.checkPlayerExists(player, 'addCall')
            amount = Decimal(amount)
            self.bets[street][player].append(amount)
            if street in ('PREFLOP', 'DEAL', 'THIRD') and self.lastBet.get(street) < amount:
                self.lastBet[street] = amount
            self.stacks[player] -= amount
            #print "DEBUG %s calls %s, stack %s" % (player, amount, self.stacks[player])
            act = (player, 'calls', amount, self.stacks[player] == 0)
            self.actions[street].append(act)
            if player == self.hero:
                if street == 'PREFLOP':
                    self.actionsHero[street].append('C'+'{:.4g}'.format(self.lastBet[street]/Decimal(str(self.bb))))
                else:
                    self.actionsHero[street].append('C'+'{:.2f}'.format(self.lastBet[street]/(sum(self.pot.committed.values()) + sum(self.pot.common.values()) - self.lastBet[street])))
            self.pot.addMoney(player, amount)

    def addRaiseBy(self, street, player, amountBy):
        """ Add a raise by amountBy on [street] by [player] """
        #Given only the amount raised by, the amount of the raise can be calculated by
        # working out how much this player has already in the pot
        #   (which is the sum of self.bets[street][player])
        # and how much he needs to call to match the previous player
        #   (which is tracked by self.lastBet)
        # let Bp = previous bet
        #     Bc = amount player has committed so far
        #     Rb = raise by
        # then: C = Bp - Bc (amount to call)
        #      Rt = Bp + Rb (raise to)
        #
        amountBy = amountBy.replace(u',', u'') #some sites have commas
        self.checkPlayerExists(player, 'addRaiseBy')
        Rb = Decimal(amountBy)
        Bp = self.lastBet[street]
        Bc = sum(self.bets[street][player])
        C = Bp - Bc
        Rt = Bp + Rb

        self._addRaise(street, player, C, Rb, Rt)
        #~ self.bets[street][player].append(C + Rb)
        #~ self.stacks[player] -= (C + Rb)
        #~ self.actions[street] += [(player, 'raises', Rb, Rt, C, self.stacks[player]==0)]
        #~ self.lastBet[street] = Rt

    def _addRaise(self, street, player, C, Rb, Rt, action='raises'):
        taille_pot = sum(self.pot.committed.values()) + sum(self.pot.common.values()) - C
        if self.handid == '234301995612':
            print(player, street, taille_pot, self.pot.common, self.pot.committed, C, Rb, Rt, action, self.bb)
        self.bets[street][player].append(C + Rb)
        self.stacks[player] -= (C + Rb)
        act = (player, action, Rb, Rt, C, self.stacks[player] == 0)
        self.actions[street].append(act)
        self.lastBet[street] = Rt  # TODO check this is correct
        if player == self.hero:
            if street == 'PREFLOP':
                self.actionsHero[street].append('R' + '{:.4g}'.format(self.lastBet[street]/Decimal(str(self.bb))) + '('
                                                + '{:.4g}'.format((Rt - Rb) / Decimal(str(self.bb)))+')')
            else:
                self.actionsHero[street].append('R' + '{:.2f}'.format(Rb/C) + 'x(' +
                                                '{:.2f}'.format(C/taille_pot) + ')')
        self.pot.addMoney(player, C + Rb)

    def addBet(self, street, player, amount):
        amount = amount.replace(u',', u'') #some sites have commas
        amount = Decimal(amount)
        self.checkPlayerExists(player, 'addBet')
        self.bets[street][player].append(amount)
        self.stacks[player] -= amount
        #print "DEBUG %s bets %s, stack %s" % (player, amount, self.stacks[player])
        act = (player, 'bets', amount, self.stacks[player] == 0)
        self.actions[street].append(act)
        self.lastBet[street] = amount
        self.pot.addMoney(player, amount)
        if player == self.hero:
            if street == 'PREFLOP':
                self.actionsHero[street].append('B'+'{:.4g}'.format(self.lastBet[street]/Decimal(str(self.bb))))
            else:
                self.actionsHero[street].append('B'+'{:.2f}'.format(self.lastBet[street]/(sum(self.pot.committed.values()) + sum(self.pot.common.values()) - self.lastBet[street])))


    def addDiscard(self, street, player, num, cards=None):
        self.checkPlayerExists(player, 'addCollectPot')
        if cards:
            act = (player, 'discards', Decimal(num), cards)
            self.discardDrawHoleCards(cards, player, street)
        else:
            act = (player, 'discards', Decimal(num))
        self.actions[street].append(act)

    def discardDrawHoleCards(self, cards, player, street):
        self.discards[street][player] = set([cards])

    def addStandsPat(self, street, player, cards=None):
        self.checkPlayerExists(player, 'addStandsPat')
        act = (player, 'stands pat')
        self.actions[street].append(act)
        if cards:
            cards = cards.split(' ')
            self.addHoleCards(street, player, open = [], closed=cards)

    def addCollectPot(self,player, pot):
        self.checkPlayerExists(player, 'addCollectPot')
        self.collected = self.collected + [[player, pot]]
        if player not in self.collectees:
            self.collectees[player] = Decimal(pot)
        else:
            self.collectees[player] += Decimal(pot)

    def totalPot(self):
        """ If all bets and blinds have been added, totals up the total pot size"""

        # This gives us the total amount put in the pot
        if self.totalpot is None:
            self.pot.end()
            self.totalpot = self.pot.total

        def gettempcontainers():
            (collected, collectees, totalcolleted) = ([], {}, 0)
            for i,v in enumerate(self.collected):
                totalcolleted += Decimal(v[1])
                collected.append([v[0], Decimal(v[1])])
            for k, j in self.collectees.items():
                collectees[k] = j
            return collected, collectees, totalcolleted

        if self.uncalledbets:
            collected, collectees, totalcolleted = gettempcontainers()
            for i,v in enumerate(self.collected):
                if v[0] in self.pot.returned:
                    collected[i][1] = Decimal(v[1]) - self.pot.returned[v[0]]
                    collectees[v[0]] -= self.pot.returned[v[0]]
                    self.pot.returned[v[0]] = 0
            if self.totalpot - totalcolleted < 0:
                (self.collected, self.collectees) = (collected, collectees)

        # This gives us the amount collected, i.e. after rake
        if self.totalcollected is None:
            self.totalcollected = 0;
            #self.collected looks like [[p1,amount][px,amount]]
            for entry in self.collected:
                self.totalcollected += Decimal(entry[1])

    def Types_Hands(self, cards):
        self.combo = ''
        self.hand_type = ''
        if cards[0] == cards[3]:
            self.combo = cards[0]+cards[3]
            if self.ranks.index(cards[0]) == 12:
                self.hand_type = 'Pocket Aces'
            elif self.ranks.index(cards[0]) < 12 and self.ranks.index(cards[0]) > 8:
                self.hand_type = 'Big Pairs'
            elif self.ranks.index(cards[0]) < 9 and self.ranks.index(cards[0]) > 4:
                self.hand_type = 'Medium Pairs'
            else:
                self.hand_type = 'Low Pairs'
        elif self.ranks.index(cards[0]) > self.ranks.index(cards[3]) and cards[1] == cards[4]:
            self.combo = cards[0]+cards[3]+'s'
            if (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 21:
                self.hand_type = 'Big Ace Hands'
            elif self.ranks.index(cards[0]) == 12:
                self.hand_type = 'Suited Aces'
            elif self.ranks.index(cards[0]) < 12 and (self.ranks.index(cards[0]) - self.ranks.index(cards[3])) == 1 and (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 1:
                self.hand_type = 'Suited Connectors'
            elif self.ranks.index(cards[0]) < 12 and (self.ranks.index(cards[0]) - self.ranks.index(cards[3])) == 2 and (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 5:
                self.hand_type = 'Suited One Gapper'
            elif self.ranks.index(cards[0]) < 12 and (self.ranks.index(cards[0]) - self.ranks.index(cards[3])) == 3 and (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 4:
                self.hand_type = 'Suited Two Gappers'
            else:
                self.hand_type = 'Other Suited Hands'
        elif self.ranks.index(cards[3]) > self.ranks.index(cards[0]) and cards[1] == cards[4]:
            self.combo = cards[3]+cards[0]+'s'
            if (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 21:
                self.hand_type = 'Big Ace Hands'
            elif self.ranks.index(cards[3]) == 12:
                self.hand_type = 'Suited Aces'
            elif self.ranks.index(cards[3]) < 12 and (self.ranks.index(cards[3]) - self.ranks.index(cards[0])) == 1 and (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 1:
                self.hand_type = 'Suited Connectors'
            elif self.ranks.index(cards[3]) < 12 and (self.ranks.index(cards[3]) - self.ranks.index(cards[0])) == 2 and (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 5:
                self.hand_type = 'Suited One Gapper'
            elif self.ranks.index(cards[3]) < 12 and (self.ranks.index(cards[3]) - self.ranks.index(cards[0])) == 3 and (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 4:
                self.hand_type = 'Suited Two Gappers'
            else:
                self.hand_type = 'Other Suited Hands'
        elif self.ranks.index(cards[0]) > self.ranks.index(cards[3]) and cards[1] != cards[4]:
            self.combo = cards[0]+cards[3]+'o'
            if (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 21:
                self.hand_type = 'Big Ace Hands'
            elif self.ranks.index(cards[0]) == 12:
                self.hand_type = 'Non Suited Aces'
            elif self.ranks.index(cards[0]) < 12 and (self.ranks.index(cards[0]) - self.ranks.index(cards[3])) == 1 and (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 1:
                self.hand_type = 'Non Suited Connectors'
            elif self.ranks.index(cards[0]) < 12 and (self.ranks.index(cards[0]) - self.ranks.index(cards[3])) == 2 and (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 5:
                self.hand_type = 'Non Suited One Gapper'
            elif self.ranks.index(cards[0]) < 12 and (self.ranks.index(cards[0]) - self.ranks.index(cards[3])) == 3 and (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 4:
                self.hand_type = 'Non Suited Two Gappers'
            else:
                self.hand_type = 'Other Non Suited Hands'
        elif self.ranks.index(cards[3]) > self.ranks.index(cards[0]) and cards[1] != cards[4]:
            self.combo = cards[3]+cards[0]+'o'
            if (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 21:
                self.hand_type = 'Big Ace Hands'
            elif self.ranks.index(cards[3]) == 12:
                self.hand_type = 'Non Suited Aces'
            elif self.ranks.index(cards[3]) < 12 and (self.ranks.index(cards[3]) - self.ranks.index(cards[0])) == 1 and (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 1:
                self.hand_type = 'Non Suited Connectors'
            elif self.ranks.index(cards[3]) < 12 and (self.ranks.index(cards[3]) - self.ranks.index(cards[0])) == 2 and (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 5:
                self.hand_type = 'Non Suited One Gapper'
            elif self.ranks.index(cards[3]) < 12 and (self.ranks.index(cards[3]) - self.ranks.index(cards[0])) == 3 and (self.ranks.index(cards[0]) + self.ranks.index(cards[3])) > 4:
                self.hand_type = 'Non Suited Two Gappers'
            else:
                self.hand_type = 'Other Non Suited Hands'
        return self.combo, self.hand_type

    def pfba(self, actions, f=None, l=None):
        """Helper method. Returns set of PlayersFilteredByActions

        f - forbidden actions
        l - limited to actions
        """
        players = set()
        for action in actions:
            if l is not None and action[1] not in l:
                continue
            if f is not None and action[1] in f:
                continue
            players.add(action[0])
        return players


class Pot(object):

    def __init__(self):
        self.contenders   = set()
        self.committed    = {}
        self.streettotals = {}
        self.common       = {}
        self.total        = None
        self.returned     = {}
        self.sym          = u'$' # this is the default currency symbol
        self.pots         = []
        self.handid       = 0

    def addPlayer(self,player):
        self.committed[player] = Decimal(0)
        self.common[player] = Decimal(0)

    def addCommonMoney(self, player, amount):
        self.common[player] += amount

    def addMoney(self, player, amount):
        # addMoney must be called for any actions that put money in the pot, in the order they occur
        #print "DEBUG: %s adds %s" %(player, amount)
        self.contenders.add(player)
        self.committed[player] += amount

    def addFold(self, player):
        # addFold must be called when a player folds
        self.contenders.discard(player)

    def markTotal(self, street):
        self.streettotals[street] = sum(self.committed.values()) + sum(self.common.values())

    def end(self):
        self.total = sum(self.committed.values()) + sum(self.common.values())

        # Return any uncalled bet.
        committed = sorted([ (v,k) for (k,v) in self.committed.items()])
        #print "DEBUG: committed: %s" % committed
        #ERROR below. lastbet is correct in most cases, but wrong when
        #             additional money is committed to the pot in cash games
        #             due to an additional sb being posted. (Speculate that
        #             posting sb+bb is also potentially wrong)
        try:
            lastbet = committed[-1][0] - committed[-2][0]
            if lastbet > 0: # uncalled
                returnto = committed[-1][1]
                #print "DEBUG: returning %f to %s" % (lastbet, returnto)
                self.total -= lastbet
                self.committed[returnto] -= lastbet
                self.returned[returnto] = lastbet
        except IndexError as e:
            print("Pot.end(): '%s': Major failure while calculating pot: '%s'" % (self.handid, e))
            raise FpdbParseError

        # Work out side pots
        commitsall = sorted([(v, k) for (k,v) in self.committed.items() if v > 0])

        try:
            while len(commitsall) > 0:
                commitslive = [(v, k) for (v,k) in commitsall if k in self.contenders]
                v1 = commitslive[0][0]
                self.pots += [(sum([min(v, v1) for (v,k) in commitsall]), set(k for (v, k) in commitsall if k in self.contenders))]
                commitsall = [((v-v1), k) for (v, k) in commitsall if v-v1 > 0]
        except IndexError as e:
            print("Pot.end(): '%s': Major failure while calculating pot: '%s'" % (self.handid, e))
            raise FpdbParseError
