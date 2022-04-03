#!/usr/bin/env python3
import pandas
import numpy as np
import scipy as sp
from scipy import stats
import time


class LeakFinder:

    def __init__(self, dataframe):
        self.hhs = dataframe
        self.nbHH = 0
        self.bbs_100 = 0
        self.std_dev_100 = 0
        self.startdate = 0
        self.enddate = 0
        self.EX_pourcent = {'SB': 0.17, 'BB': 0.35, 'UTG': 0.05, 'MP': 0.1, 'CO': 0.13, 'BU': 0.2}
        self.tables = []
        self.noleak = []
        self.titres = []
        self.rtime = time.time()
        self.rapport_complet()
        self.rtime = time.time() - self.rtime

    def rapport_complet(self):
        self.entete()
        self.position_report()
        self.facing_preflop_report()
        self.facing_preflop_firstraiser_report()
        self.pf_action_report()
        self.pf_action_firstraiser_report()
        self.hand_type_report()
        self.flop_type_report()
        self.joueur_flop_report()

    def entete(self):

        self.nbHH = str(len(self.hhs))
        self.bbs_100 = '{:.3g}'.format(self.hhs['bbs'].sum() / (len(self.hhs) / 100))
        self.std_dev_100 = '{:.3g}'.format((self.hhs['bbs'].std() / (pow(len(self.hhs), 0.5))) * 100)
        self.startdate = '{:%d/%m/%Y}'.format(self.hhs['timestamp'].min())
        self.enddate = '{:%d/%m/%Y}'.format(self.hhs['timestamp'].max())

    def position_report(self):

        tab = self.hhs.groupby(['position'])[['bbs']].agg(['sum', 'count'])
        tab.columns = ['_'.join(x) for x in tab.columns.values]
        tab['bb100'] = round((tab['bbs_sum'] / tab['bbs_count']) * 100, 1)
        tab = tab.reset_index()
        for row in tab.itertuples():
            data = self.hhs[(self.hhs['position'] == row.position)]
            r_winrate = LeakFinder.calculer_rfactor(data)[0]
            tab.loc[row.Index, 'bb100'] = round(row.bbs_sum / len(data) * 100, 1)
            tab.loc[row.Index, 'r_winrate'] = r_winrate
            tab.loc[row.Index, 'r_winratebb100'] = round(r_winrate / len(data) * 100, 1)
            tab.loc[row.Index, 'r_factor'] = LeakFinder.calculer_rfactor(data)[1]
            tab.loc[row.Index, 'EX_bb100'] = round(self.EX_Winrate(row.position, 6)[1], 1)
            tab.loc[row.Index, 'r_diff'] = round(r_winrate -
                                                 (self.EX_Winrate(row.position, 6)[1] * (len(data) / 100)), 1)
        tab = tab.sort_values(by='r_diff')
        tab.columns = ['Position', 'Gain (bb)', 'Nombre de mains', 'Gain (bb/100)', 'Gain ajusté (bb)',
                       'Gain ajusté (bb/100)', 'Corrélation', 'Gain espéré (bb/100)', 'Pertes (bb)']
        tab.to_csv('position_report.csv', index=False)
        self.tables.append(["Rapport par position",
                            tab.to_html(index=False).replace('class="dataframe"',
                                                             'class="table table-striped w-auto mx-auto text-center"')])

    def facing_preflop_report(self):

        tab = self.hhs.groupby(['facing_preflop', 'position'])[['bbs']].agg(['sum', 'count'])
        tab.columns = ['_'.join(x) for x in tab.columns.values]
        tab = tab.reset_index()
        for row in tab.itertuples():
            data = self.hhs[(self.hhs['position'] == row.position) & (self.hhs['facing_preflop'] == row.facing_preflop)]
            r_winrate = LeakFinder.calculer_rfactor(data[data['bbs'] != 0.00])[0]
            tab.loc[row.Index, 'bb100'] = round(row.bbs_sum / len(data) * 100, 1)
            tab.loc[row.Index, 'r_winrate'] = r_winrate
            tab.loc[row.Index, 'r_winratebb100'] = round(r_winrate / len(data) * 100, 1)
            tab.loc[row.Index, 'r_factor'] = LeakFinder.calculer_rfactor(data[data['bbs'] != 0.00])[1]
            tab.loc[row.Index, 'EX_bb100'] = round(self.EX_Winrate(row.position, 6)[1], 1)
            tab.loc[row.Index, 'r_diff'] = round(r_winrate -
                                                 (self.EX_Winrate(row.position, 6)[1] * (len(data) / 100)), 1)
        tab = tab.sort_values(by='r_diff')
        tab.columns = ['Face à (Preflop)', 'Position', 'Gain (bb)', 'Nombre de mains', 'Gain (bb/100)',
                       'Gain ajusté (bb)', 'Gain ajusté (bb/100)', 'Corrélation',
                       'Gain espéré (bb/100)', 'Pertes (bb)']
        tab.to_csv('facing_preflop_report.csv', index=False)
        result = tab[(tab['Corrélation'] >= 0.7) & (tab['Pertes (bb)'] < -len(self.hhs) / 100)]
        if len(result) > 0:
            self.tables.append([
                "Rapport en fonction de l'action avant parole + position",
                result.to_html(index=False).replace('class="dataframe"',
                                                    'class="table table-striped w-auto mx-auto text-center"')])
        else:
            self.noleak.append(
                "Aucun leak n'a été observé pour les actions préflop avant parole de Hero sur cet échantillon")

    def pf_action_report(self):

        tab1 = self.hhs[self.hhs['bbs'] != 0.00]
        tab = tab1.groupby(['hero_PFAction_simpl', 'position'])[['bbs']].agg(['sum', 'count'])
        tab.columns = ['_'.join(x) for x in tab.columns.values]
        tab = tab.reset_index()
        for row in tab.itertuples():
            data = self.hhs[(self.hhs['position'] == row.position) &
                            (self.hhs['hero_PFAction_simpl'] == row.hero_PFAction_simpl)]
            r_winrate = LeakFinder.calculer_rfactor(data[data['bbs'] != 0.00])[0]
            tab.loc[row.Index, 'bb100'] = round(row.bbs_sum / len(data) * 100, 1)
            tab.loc[row.Index, 'r_winrate'] = r_winrate
            tab.loc[row.Index, 'r_winratebb100'] = round(r_winrate / len(data) * 100, 1)
            tab.loc[row.Index, 'r_factor'] = LeakFinder.calculer_rfactor(data[data['bbs'] != 0.00])[1]
            tab.loc[row.Index, 'EX_bb100'] = round(self.EX_Winrate(row.position, 6)[1], 1)
            tab.loc[row.Index, 'r_diff'] = round(r_winrate -
                                                 (self.EX_Winrate(row.position, 6)[1] * (len(data) / 100)), 1)
        tab = tab.sort_values(by='r_diff')
        tab.columns = ['Action preflop hero', 'Position', 'Gain (bb)', 'Nombre de mains', 'Gain (bb/100)',
                       'Gain ajusté (bb)', 'Gain ajusté (bb/100)', 'Corrélation',
                       'Gain espéré (bb/100)', 'Pertes (bb)']
        tab.to_csv('pf_action_report.csv', index=False)
        result = tab[(tab['Corrélation'] >= 0.7) & (tab['Pertes (bb)'] < -len(self.hhs) / 100) &
                     (tab['Action preflop hero'].str.contains('F') is False)]
        if len(result) > 0:
            self.tables.append(
                ["Rapport en fonction de l'action préflop de hero + position (Fold pas pris en compte)",
                 result.to_html(index=False).replace('class="dataframe"',
                                                     'class="table table-striped w-auto mx-auto text-center"')])
        else:
            self.noleak.append("Aucun leak n'a été observé pour les actions préflop de Hero sur cet échantillon")

    def hand_type_report(self):

        tab1 = self.hhs[self.hhs['bbs'] != 0.00]
        tab = tab1.groupby(['hand_type', 'position'])[['bbs']].agg(['sum', 'count'])
        tab.columns = ['_'.join(x) for x in tab.columns.values]
        tab = tab.reset_index()
        for row in tab.itertuples():
            data = self.hhs[(self.hhs['position'] == row.position) & (self.hhs['hand_type'] == row.hand_type)]
            r_winrate = LeakFinder.calculer_rfactor(data[data['bbs'] != 0.00])[0]
            tab.loc[row.Index, 'bb100'] = round(row.bbs_sum / len(data) * 100, 1)
            tab.loc[row.Index, 'r_winrate'] = r_winrate
            tab.loc[row.Index, 'r_winratebb100'] = round(r_winrate / len(data) * 100, 1)
            tab.loc[row.Index, 'r_factor'] = LeakFinder.calculer_rfactor(data[data['bbs'] != 0.00])[1]
            tab.loc[row.Index, 'EX_bb100'] = round(self.EX_Winrate(row.position, 6)[1], 1)
            tab.loc[row.Index, 'r_diff'] = round(r_winrate -
                                                 (self.EX_Winrate(row.position, 6)[1] * (len(data) / 100)), 1)
        tab = tab.sort_values(by='r_diff')
        tab.columns = ['Type de mains', 'Position', 'Gain (bb)', 'Nombre de mains', 'Gain (bb/100)', 'Gain ajusté (bb)',
                       'Gain ajusté (bb/100)', 'Corrélation', 'Gain espéré (bb/100)', 'Pertes (bb)']
        tab.to_csv('hand_type_report.csv', index=False)
        result = tab[(tab['Corrélation'] >= 0.7) & (tab['Pertes (bb)'] < -len(self.hhs) / 100) &
                     (tab['Position'] != 'SB') & (tab['Position'] != 'BB')]
        if len(result) > 0:
            self.tables.append(
                ["Rapport en fonction des différents types de mains joués (BB et SB exclues)",
                 result.to_html(index=False).replace('class="dataframe"',
                                                     'class="table table-striped w-auto mx-auto text-center"')])
        else:
            self.noleak.append(
                "Aucun leak n'a été observé pour les différents types de mains joués sur cet échantillon")

    def flop_type_report(self):

        tab1 = self.hhs[self.hhs['sawflop'] == 1]
        tab = tab1.groupby(['type_flop', 'position'])[['bbs']].agg(['sum', 'count'])
        tab.columns = ['_'.join(x) for x in tab.columns.values]
        tab = tab.reset_index()
        for row in tab.itertuples():
            data = self.hhs[(self.hhs['position'] == row.position) & (self.hhs['type_flop'] == row.type_flop)]
            r_winrate = LeakFinder.calculer_rfactor(data)[0]
            tab.loc[row.Index, 'bb100'] = round(row.bbs_sum / len(data) * 100, 1)
            tab.loc[row.Index, 'r_winrate'] = r_winrate
            tab.loc[row.Index, 'r_winratebb100'] = round(r_winrate / len(data) * 100, 1)
            tab.loc[row.Index, 'r_factor'] = LeakFinder.calculer_rfactor(data)[1]
            tab.loc[row.Index, 'EX_bb100'] = round(self.EX_Winrate(row.position, 6)[1], 1)
            tab.loc[row.Index, 'r_diff'] = round(r_winrate -
                                                 (self.EX_Winrate(row.position, 6)[1] * (len(data) / 100)), 1)
        tab = tab.sort_values(by='r_diff')
        tab.columns = ['Type_de_flop', 'Position', 'Gain (bb)', 'Nombre de mains', 'Gain (bb/100)', 'Gain ajusté (bb)',
                       'Gain ajusté (bb/100)', 'Corrélation', 'Gain espéré (bb/100)', 'Pertes (bb)']
        tab.to_csv('flop_type_report.csv', index=False)
        result = tab[(tab['Corrélation'] >= 0.7) & (tab['Pertes (bb)'] < -len(self.hhs) / 100)]
        if len(result) > 0:
            self.tables.append(["Rapport en fonction du type de flop + position",
                                result.to_html(index=False).replace('class="dataframe"',
                                                                    'class="table table-striped w-auto mx-auto text-center"')])
        else:
            self.noleak.append("Aucun leak n'a été observé pour les différents types de flop joués sur cet échantillon")

    def joueur_flop_report(self):

        tab1 = self.hhs[self.hhs['sawflop'] == 1]
        tab = tab1.groupby(['nb_joueur_flop', 'position'])[['bbs']].agg(['sum', 'count'])
        tab.columns = ['_'.join(x) for x in tab.columns.values]
        tab = tab.reset_index()
        for row in tab.itertuples():
            data = self.hhs[(self.hhs['position'] == row.position) & (self.hhs['nb_joueur_flop'] == row.nb_joueur_flop)]
            r_winrate = LeakFinder.calculer_rfactor(data)[0]
            tab.loc[row.Index, 'bb100'] = round(row.bbs_sum / len(data) * 100, 1)
            tab.loc[row.Index, 'r_winrate'] = r_winrate
            tab.loc[row.Index, 'r_winratebb100'] = round(r_winrate / len(data) * 100, 1)
            tab.loc[row.Index, 'r_factor'] = LeakFinder.calculer_rfactor(data)[1]
            tab.loc[row.Index, 'EX_bb100'] = round(self.EX_Winrate(row.position, 6)[1], 1)
            tab.loc[row.Index, 'r_diff'] = round(
                r_winrate - (self.EX_Winrate(row.position, 6)[1] * (len(data) / 100)), 1)
        tab = tab.sort_values(by='r_diff')
        tab.columns = ['Nombre de joueurs au flop', 'Position', 'Gain (bb)', 'Nombre de mains', 'Gain (bb/100)',
                       'Gain ajusté (bb)', 'Gain ajusté (bb/100)', 'Corrélation',
                       'Gain espéré (bb/100)', 'Pertes (bb)']
        tab.to_csv('joueur_flop_report.csv', index=False)
        result = tab[(tab['Corrélation'] >= 0.7) & (tab['Pertes (bb)'] < -len(self.hhs) / 100) &
                     (tab['Nombre de joueurs au flop'] > 0)]
        if len(result) > 0:
            self.tables.append([
                "Rapport en fonction du nombre de joueurs au flop + position",
                result.to_html(index=False).replace('class="dataframe"',
                                                    'class="table table-striped w-auto mx-auto text-center"')])
        else:
            self.noleak.append(
                "Aucun leak n'a été observé en fonction du nombre de joueurs au flop sur cet échantillon")

    def facing_preflop_firstraiser_report(self):

        tab = self.hhs.groupby(['facing_preflop', 'position', 'firstraiser'])[['bbs']].agg(['sum', 'count'])
        tab.columns = ['_'.join(x) for x in tab.columns.values]
        tab = tab.reset_index()
        for row in tab.itertuples():
            data = self.hhs[(self.hhs['position'] == row.position) & (self.hhs['facing_preflop'] == row.facing_preflop)
                            & (self.hhs['firstraiser'] == row.firstraiser)]
            r_winrate = LeakFinder.calculer_rfactor(data[data['bbs'] != 0.00])[0]
            tab.loc[row.Index, 'bb100'] = round(row.bbs_sum / len(data) * 100, 1)
            tab.loc[row.Index, 'r_winrate'] = r_winrate
            tab.loc[row.Index, 'r_winratebb100'] = round(r_winrate / len(data) * 100, 1)
            tab.loc[row.Index, 'r_factor'] = LeakFinder.calculer_rfactor(data[data['bbs'] != 0.00])[1]
            tab.loc[row.Index, 'EX_bb100'] = round(self.EX_Winrate(row.position, 6)[1], 1)
            tab.loc[row.Index, 'r_diff'] = round(r_winrate -
                                                 (self.EX_Winrate(row.position, 6)[1] * (len(data) / 100)), 1)
        tab = tab.sort_values(by='r_diff')
        tab.columns = ['Face à (Preflop)', 'Position', 'FirstRaiser', 'Gain (bb)', 'Nombre de mains', 'Gain (bb/100)',
                       'Gain ajusté (bb)', 'Gain ajusté (bb/100)', 'Corrélation',
                       'Gain espéré (bb/100)', 'Pertes (bb)']
        tab.to_csv('facing_preflop_firstraiser_report.csv', index=False)
        result = tab[(tab['Corrélation'] >= 0.7) & (tab['Pertes (bb)'] < -len(self.hhs) / 100)]
        if len(result) > 0:
            self.tables.append([
                "Rapport en fonction de l'action avant parole + position + firstraiser",
                result.to_html(index=False).replace('class="dataframe"',
                                                    'class="table table-striped w-auto mx-auto text-center"')])
        else:
            self.noleak.append(
                "Aucun leak n'a été observé pour les actions préflop avant parole de Hero + firstraiser sur cet échantillon")

    def leak_report3(self):

        tab = self.hhs.groupby(['position', 'facing_preflop', 'hero_PFAction_simpl',
                                'hand_type'])[['bbs']].agg(['sum', 'count'])
        tab.columns = ['_'.join(x) for x in tab.columns.values]
        tab = tab.reset_index()
        for row in tab.itertuples():
            data = self.hhs[(self.hhs['position'] == row.position) &
                                     (self.hhs['facing_preflop'] == row.facing_preflop) &
                                     (self.hhs['hero_PFAction_simpl'] == row.hero_PFAction_simpl) &
                                     (self.hhs['hand_type'] == row.hand_type)]
            r_winrate = LeakFinder.calculer_rfactor(data[data['bbs'] != 0.00])[0]
            tab.loc[row.Index, 'bb100'] = round(row.bbs_sum / len(data) * 100, 1)
            tab.loc[row.Index, 'r_winrate'] = r_winrate
            tab.loc[row.Index, 'r_winratebb100'] = round(r_winrate / len(data) * 100, 1)
            tab.loc[row.Index, 'r_factor'] = LeakFinder.calculer_rfactor(data[data['bbs'] != 0.00])[1]
            tab.loc[row.Index, 'EX_bb100'] = round(self.EX_Winrate(row.position, 6)[1], 1)
            tab.loc[row.Index, 'r_diff'] = round(r_winrate -
                                                 (self.EX_Winrate(row.position, 6)[1] * (len(data) / 100)), 1)
        tab = tab.sort_values(by='r_diff')
        tab.to_csv('leak_report3.csv', index=False)
        result = tab[(tab['r_factor'] >= 0.7) & (tab['r_diff'] < -len(self.hhs) / 100) &
                     (tab['hero_PFAction_simpl'].str.contains('F') is False)]
        if len(result) > 0:
            result1 = result.copy()
            result1.columns = ['Position', 'Face à (Preflop)', 'Action preflop hero', 'Type de mains', 'Gain (bb)',
                               'Nombre de mains', 'Gain (bb/100)', 'Gain ajusté (bb)', 'Gain ajusté (bb/100)',
                               'Corrélation', 'Gain espéré (bb/100)', 'Pertes (bb)']
            self.tables.append(["Rapport avec prise en compte de tous les facteurs",
                                result1.to_html(index=False).replace('class="dataframe"',
                                                                     'class="table table-striped w-auto mx-auto text-center"')])
        else:
            self.noleak.append("Aucun leak n'a été observé en prenant en compte tous les facteurs sur cet échantillon")

      # for row in result.itertuples():
        # LeakFinder.Leak_Report2(self, row.Position, row.Facing_Preflop, row.PF_action_simpl, row.Hand_Type, row.r_diff)

    def pf_action_firstraiser_report(self):

        tab1 = self.hhs[self.hhs['bbs'] != 0.00]
        tab = tab1.groupby(['hero_PFAction_simpl', 'position', 'firstraiser'])[['bbs']].agg(['sum', 'count'])
        tab.columns = ['_'.join(x) for x in tab.columns.values]
        tab = tab.reset_index()
        for row in tab.itertuples():
            data = self.hhs[(self.hhs['position'] == row.position) &
                            (self.hhs['hero_PFAction_simpl'] == row.hero_PFAction_simpl)
                            & (self.hhs['firstraiser'] == row.firstraiser)]
            r_winrate = LeakFinder.calculer_rfactor(data[data['bbs'] != 0.00])[0]
            tab.loc[row.Index, 'bb100'] = round(row.bbs_sum / len(data) * 100, 1)
            tab.loc[row.Index, 'r_winrate'] = r_winrate
            tab.loc[row.Index, 'r_winratebb100'] = round(r_winrate / len(data) * 100, 1)
            tab.loc[row.Index, 'r_factor'] = LeakFinder.calculer_rfactor(data[data['bbs'] != 0.00])[1]
            tab.loc[row.Index, 'EX_bb100'] = round(self.EX_Winrate(row.position, 6)[1], 1)
            tab.loc[row.Index, 'r_diff'] = round(r_winrate -
                                                 (self.EX_Winrate(row.position, 6)[1] * (len(data) / 100)), 1)
        tab = tab.sort_values(by='r_diff')
        tab.columns = ['Action preflop hero', 'Position', 'FirstRaiser', 'Gain (bb)', 'Nombre de mains',
                       'Gain (bb/100)',
                       'Gain ajusté (bb)', 'Gain ajusté (bb/100)', 'Corrélation',
                       'Gain espéré (bb/100)', 'Pertes (bb)']
        tab.to_csv('pf_action_report.csv', index=False)
        result = tab[(tab['Corrélation'] >= 0.7) & (tab['Pertes (bb)'] < -len(self.hhs) / 100) &
                     (tab['Action preflop hero'].str.contains('F') is False)]
        if len(result) > 0:
            self.tables.append(
                ["Rapport en fonction de l'action préflop de hero + position + firstraiser (Fold pas pris en compte)",
                 result.to_html(index=False).replace('class="dataframe"',
                                                     'class="table table-striped w-auto mx-auto text-center"')])
        else:
            self.noleak.append("Aucun leak n'a été observé pour les actions préflop de Hero sur cet échantillon")

    @staticmethod
    def calculer_rfactor(df):
        if len(df) >= 50:
            y_data = df['bbs'].to_numpy().cumsum()
            x_data = np.arange(1, len(y_data) + 1, 1)
            A = np.vstack([x_data, np.ones(len(x_data))]).T
            model, resid = np.linalg.lstsq(A, y_data, rcond=None)[:2]
            r_winrate = model[0] * len(y_data) + model[1]  # winrate en bbs
            r_factor = 1 - resid / (y_data.size * y_data.var())
            return r_winrate, r_factor
        else:
            return 0.0, 0.0

    def EX_Winrate(self, Place, EX_win):  # Ex_winrate = bb100 souhaité au total --> 6 bb/100
        tab = self.hhs.groupby(['position'])[['bbs']].agg(['sum', 'count'])
        tab.columns = ['_'.join(x) for x in tab.columns.values]
        sbhands = tab.loc['SB', 'bbs_count']
        bbhands = tab.loc['BB', 'bbs_count']
        totalhands = tab['bbs_count'].sum()
        bbtowin = sbhands * 0.5 + bbhands * 1 + (totalhands / 100) * EX_win
        if Place == 'SB':
            Ex_Winrate = self.EX_pourcent['SB'] * bbtowin - sbhands * 0.5
        elif Place == 'BB':
            Ex_Winrate = self.EX_pourcent['BB'] * bbtowin - bbhands
        else:
            Ex_Winrate = self.EX_pourcent[Place] * bbtowin
        Ex_bbwinrate = Ex_Winrate / (tab.loc[Place, 'bbs_count'] / 100)
        return Ex_Winrate, Ex_bbwinrate
