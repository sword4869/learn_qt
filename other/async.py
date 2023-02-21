# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import signal
import sys
import traceback
import time
import outcome
import trio
from PySide6.QtCore import QEvent, QObject, Qt, Signal, Slot
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QPushButton,
                               QVBoxLayout, QWidget)


class MainWindow(QMainWindow):

    def __init__(self, async_signal:Signal):
        ###
        # 点击按钮，会更换 QLabel 的文字
        ###
        super().__init__()

        self.async_signal = async_signal

        widget = QWidget()
        self.setCentralWidget(widget)

        layout = QVBoxLayout(widget)

        self.text = QLabel("The answer is 42.")
        layout.addWidget(self.text)

        self.async_trigger = QPushButton(text="What is the question?")
        self.async_trigger.clicked.connect(self.async_start)
        layout.addWidget(self.async_trigger)

        self.setLayout(layout)

    @Slot()
    def async_start(self):
        self.async_signal.emit()

    async def set_text(self):
        ###
        # 异步事件
        ###
        # 不让再按按钮，不然会 raise RuntimeError("Attempted to call run() from inside a run()")
        self.async_trigger.setEnabled(False)
        await trio.sleep(3)
        self.text.setText(f'{time.time()}')
        self.async_trigger.setEnabled(True)



class AsyncHelper(QObject):

    trigger_signal = Signal()

    class ReenterQtObject(QObject):
        """ This is a QObject to which an event will be posted, allowing
            Trio to resume when the event is handled. event.fn() is the
            next entry point of the Trio event loop. """
        def event(self, event):
            if event.type() == QEvent.User + 1:
                event.fn()
                return True
            return False

    class ReenterQtEvent(QEvent):
        """ This is the QEvent that will be handled by the ReenterQtObject.
            self.fn is the next entry point of the Trio event loop. """
        def __init__(self, fn):
            super().__init__(QEvent.Type(QEvent.User + 1))
            self.fn = fn

    def __init__(self, entry=None):
        super().__init__()
        self.reenter_qt = self.ReenterQtObject()
        self.entry = entry

    def set_entry(self, entry):
        self.entry = entry

    @Slot()
    def launch_guest_run(self):
        """ To use Trio and Qt together, one must run the Trio event
            loop as a "guest" inside the Qt "host" event loop. """
        if not self.entry:
            raise Exception("No entry point for the Trio guest run was set.")
        trio.lowlevel.start_guest_run(
            self.entry,
            run_sync_soon_threadsafe=self.next_guest_run_schedule,
            done_callback=self.trio_done_callback,
        )

    def next_guest_run_schedule(self, fn):
        """ This function serves to re-schedule the guest (Trio) event
            loop inside the host (Qt) event loop. It is called by Trio
            at the end of an event loop run in order to relinquish back
            to Qt's event loop. By posting an event on the Qt event loop
            that contains Trio's next entry point, it ensures that Trio's
            event loop will be scheduled again by Qt. """
        QApplication.postEvent(self.reenter_qt, self.ReenterQtEvent(fn))

    def trio_done_callback(self, outcome_):
        """ This function is called by Trio when its event loop has
            finished. """
        if isinstance(outcome_, outcome.Error):
            error = outcome_.error
            traceback.print_exception(type(error), error, error.__traceback__)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    async_helper = AsyncHelper()
    main_window = MainWindow(async_helper.trigger_signal)
    async_helper.set_entry(main_window.set_text)

    # This establishes the entry point for the Trio guest run. It varies
    # depending on how and when its event loop is to be triggered, e.g.,
    # at a specific moment like a button press (as here) or rather from
    # the beginning.
    async_helper.trigger_signal.connect(async_helper.launch_guest_run)

    main_window.show()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec()