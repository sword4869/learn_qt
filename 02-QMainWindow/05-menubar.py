from PySide6.QtWidgets import QApplication, QMainWindow, QToolBar, QStatusBar
from PySide6.QtGui import QAction
from PySide6.QtCore import QSize

import sys

class MainWindow(QMainWindow):
    # 多了个 app 参数, quit_app() 需要
    def __init__(self, app):
        super().__init__()
        
        self.app = app

        self.setWindowTitle('Window')

        ''' 菜单栏 '''

        
        menubar = self.menuBar()    # return a QMenuBar object
        file_menu = menubar.addMenu('&File')    # File 菜单

        # File菜单上的动作，quit_action 是 addAction 返回的QAction对象
        quit_action = file_menu.addAction('Quit')
        quit_action.triggered.connect(self.quit_app)

        
        ''' toolbar '''
        toolbar = QToolBar('Toolbar')
        toolbar.setIconSize(QSize(16, 16))
        # 可以直接添加菜单栏的动作
        toolbar.addAction(quit_action)
        self.addToolBar(toolbar)

        
        ''' separator '''
        toolbar.addSeparator()


        
        ''' QAction '''
        an_action = QAction('an_action', self)
        an_action.setStatusTip('an_action status')
        an_action.triggered.connect(self.printStatus)
        toolbar.addAction(an_action)


        ''' status bar '''
        # 给窗口 添加 QStatusBar对象
        self.setStatusBar(QStatusBar(self))


    def quit_app(self):
        self.app.quit()

    def printStatus(self):
        self.statusBar().showMessage('clicked')
        
    

app = QApplication(sys.argv)
# 传入创建的 QApplication 给 MainWindow
window = MainWindow(app)
window.show()
app.exec()