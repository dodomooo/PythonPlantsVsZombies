__author__ = 'marble_xu'

from . import tool
from . import constants as c
from .state import mainmenu, screen, level, loading, login, report

def main():
    game = tool.Control()
    state_dict = {c.LOADING_SCREEN: loading.LoadingScreen(),
                  c.LOGIN_SCREEN: login.LoginScreen(),
                  c.MAIN_MENU: mainmenu.Menu(),
                  c.GAME_VICTORY: screen.GameVictoryScreen(),
                  c.GAME_LOSE: screen.GameLoseScreen(),
                  c.GAME_REPORT: report.GameReportScreen(),
                  c.LEVEL: level.Level()}
    game.setup_states(state_dict, c.LOGIN_SCREEN)
    game.main()