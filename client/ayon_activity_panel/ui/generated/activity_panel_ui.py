# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'activity_panel.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

try:
    from qtpy.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
        QMetaObject, QObject, QPoint, QRect,
        QSize, QTime, QUrl, Qt)
    from qtpy.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
        QFont, QFontDatabase, QGradient, QIcon,
        QImage, QKeySequence, QLinearGradient, QPainter,
        QPalette, QPixmap, QRadialGradient, QTransform)
    from qtpy.QtWidgets import (QApplication, QComboBox, QDockWidget, QGridLayout,
        QHBoxLayout, QLabel, QLineEdit, QPushButton,
        QSizePolicy, QSpacerItem, QSplitter, QTabWidget,
        QTextBrowser, QTextEdit, QVBoxLayout, QWidget)
except ImportError:
    from PySide2.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
        QMetaObject, QObject, QPoint, QRect,
        QSize, QTime, QUrl, Qt)
    from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
        QFont, QFontDatabase, QGradient, QIcon,
        QImage, QKeySequence, QLinearGradient, QPainter,
        QPalette, QPixmap, QRadialGradient, QTransform)
    from PySide2.QtWidgets import (QApplication, QComboBox, QDockWidget, QGridLayout,
        QHBoxLayout, QLabel, QLineEdit, QPushButton,
        QSizePolicy, QSpacerItem, QSplitter, QTabWidget,
        QTextBrowser, QTextEdit, QVBoxLayout, QWidget)

class Ui_activityCommentDock(object):
    def setupUi(self, activityCommentDock):
        if not activityCommentDock.objectName():
            activityCommentDock.setObjectName(u"activityCommentDock")
        activityCommentDock.resize(276, 729)
        activityCommentDock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        activityCommentDock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.activityCommentWidget = QWidget()
        self.activityCommentWidget.setObjectName(u"activityCommentWidget")
        self.activityCommentLayout = QVBoxLayout(self.activityCommentWidget)
        self.activityCommentLayout.setObjectName(u"activityCommentLayout")

        self.mainSplitter = QSplitter(self.activityCommentWidget)
        self.mainSplitter.setObjectName(u"mainSplitter")
        self.mainSplitter.setOrientation(Qt.Orientation.Vertical)
        self.versionDetailsWidget = QWidget(self.mainSplitter)
        self.versionDetailsWidget.setObjectName(u"versionDetailsWidget")
        self.versionDetailsLayout = QVBoxLayout(self.versionDetailsWidget)
        self.versionDetailsLayout.setObjectName(u"versionDetailsLayout")
        self.versionDetailsLayout.setContentsMargins(0, 0, 0, 0)
        self.versionGridLayout = QGridLayout()
        self.versionGridLayout.setObjectName(u"versionGridLayout")
        self.pathLabel = QLabel(self.versionDetailsWidget)
        self.pathLabel.setObjectName(u"pathLabel")

        self.versionGridLayout.addWidget(self.pathLabel, 0, 0, 1, 1)

        self.pathLabel_value = QLabel(self.versionDetailsWidget)
        self.pathLabel_value.setObjectName(u"pathLabel_value")
        self.pathLabel_value.setWordWrap(True)
        self.pathLabel_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.versionGridLayout.addWidget(self.pathLabel_value, 0, 1, 1, 1)

        self.versionLabel = QLabel(self.versionDetailsWidget)
        self.versionLabel.setObjectName(u"versionLabel")

        self.versionGridLayout.addWidget(self.versionLabel, 1, 0, 1, 1)

        self.versionComboBox = QComboBox(self.versionDetailsWidget)
        self.versionComboBox.setObjectName(u"versionComboBox")

        self.versionGridLayout.addWidget(self.versionComboBox, 1, 1, 1, 1)

        self.statusLabel = QLabel(self.versionDetailsWidget)
        self.statusLabel.setObjectName(u"statusLabel")

        self.versionGridLayout.addWidget(self.statusLabel, 2, 0, 1, 1)

        self.statusComboBox = QComboBox(self.versionDetailsWidget)
        self.statusComboBox.setObjectName(u"statusComboBox")

        self.versionGridLayout.addWidget(self.statusComboBox, 2, 1, 1, 1)

        self.authorLabel = QLabel(self.versionDetailsWidget)
        self.authorLabel.setObjectName(u"authorLabel")

        self.versionGridLayout.addWidget(self.authorLabel, 3, 0, 1, 1)

        self.authorLineEdit = QLineEdit(self.versionDetailsWidget)
        self.authorLineEdit.setObjectName(u"authorLineEdit")
        self.authorLineEdit.setReadOnly(True)

        self.versionGridLayout.addWidget(self.authorLineEdit, 3, 1, 1, 1)

        self.versionDetailsLayout.addLayout(self.versionGridLayout)

        self.mainSplitter.addWidget(self.versionDetailsWidget)
        self.contentTabWidget = QTabWidget(self.mainSplitter)
        self.contentTabWidget.setObjectName(u"contentTabWidget")
        self.activityTab = QWidget()
        self.activityTab.setObjectName(u"activityTab")
        self.activityTabLayout = QVBoxLayout(self.activityTab)
        self.activityTabLayout.setObjectName(u"activityTabLayout")
        self.textBrowser_activity_panel = QTextBrowser(self.activityTab)
        self.textBrowser_activity_panel.setObjectName(u"textBrowser_activity_panel")

        self.activityTabLayout.addWidget(self.textBrowser_activity_panel)

        self.contentTabWidget.addTab(self.activityTab, "")
        self.representationsTab = QWidget()
        self.representationsTab.setObjectName(u"representationsTab")
        self.representationsTabLayout = QVBoxLayout(self.representationsTab)
        self.representationsTabLayout.setObjectName(u"representationsTabLayout")
        self.bakingButton = QPushButton(self.representationsTab)
        self.bakingButton.setObjectName(u"bakingButton")
        self.bakingButton.setCheckable(True)

        self.representationsTabLayout.addWidget(self.bakingButton)

        self.h264Button = QPushButton(self.representationsTab)
        self.h264Button.setObjectName(u"h264Button")
        self.h264Button.setCheckable(True)

        self.representationsTabLayout.addWidget(self.h264Button)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.representationsTabLayout.addItem(self.verticalSpacer)

        self.contentTabWidget.addTab(self.representationsTab, "")
        self.mainSplitter.addWidget(self.contentTabWidget)
        self.commentWidget = QWidget(self.mainSplitter)
        self.commentWidget.setObjectName(u"commentWidget")
        self.commentLayout = QVBoxLayout(self.commentWidget)
        self.commentLayout.setObjectName(u"commentLayout")
        self.commentLayout.setContentsMargins(0, 0, 0, 0)
        self.commentLabel = QLabel(self.commentWidget)
        self.commentLabel.setObjectName(u"commentLabel")

        self.commentLayout.addWidget(self.commentLabel)

        self.textEdit_comment = QTextEdit(self.commentWidget)
        self.textEdit_comment.setObjectName(u"textEdit_comment")

        self.commentLayout.addWidget(self.textEdit_comment)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.horizontalSpacer_comment = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonLayout.addItem(self.horizontalSpacer_comment)

        self.pushButton_comment = QPushButton(self.commentWidget)
        self.pushButton_comment.setObjectName(u"pushButton_comment")

        self.buttonLayout.addWidget(self.pushButton_comment)

        self.commentLayout.addLayout(self.buttonLayout)

        self.mainSplitter.addWidget(self.commentWidget)

        self.activityCommentLayout.addWidget(self.mainSplitter)

        activityCommentDock.setWidget(self.activityCommentWidget)

        self.retranslateUi(activityCommentDock)

        self.contentTabWidget.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(activityCommentDock)

    # setupUi

    def retranslateUi(self, activityCommentDock):
        activityCommentDock.setWindowTitle(QCoreApplication.translate("activityCommentDock", u"Version Info", None))
        self.pathLabel.setText(QCoreApplication.translate("activityCommentDock", u"Path:", None))
        self.pathLabel_value.setText("")
        self.versionLabel.setText(QCoreApplication.translate("activityCommentDock", u"Version:", None))
        self.statusLabel.setText(QCoreApplication.translate("activityCommentDock", u"Status:", None))
        self.authorLabel.setText(QCoreApplication.translate("activityCommentDock", u"Author:", None))
        self.authorLineEdit.setText("")
        self.contentTabWidget.setTabText(self.contentTabWidget.indexOf(self.activityTab),
                                         QCoreApplication.translate("activityCommentDock", u"Activity", None))
        self.bakingButton.setText(QCoreApplication.translate("activityCommentDock", u"baking_h264", None))
        self.h264Button.setText(QCoreApplication.translate("activityCommentDock", u"h264", None))
        self.contentTabWidget.setTabText(self.contentTabWidget.indexOf(self.representationsTab),
                                         QCoreApplication.translate("activityCommentDock", u"Representations", None))
        self.commentLabel.setText(QCoreApplication.translate("activityCommentDock", u"Comments:", None))
        self.textEdit_comment.setPlaceholderText(
            QCoreApplication.translate("activityCommentDock", u"Comment or mention with @user, @@version, @@@task...",
                                       None))
        self.pushButton_comment.setText(QCoreApplication.translate("activityCommentDock", u"Comment", None))
    # retranslateUi
