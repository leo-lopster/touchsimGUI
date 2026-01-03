from PyQt5.QtWidgets import QPushButton

# --------------------------------------------------------
# Highlight Button
# --------------------------------------------------------
def highlight_button(button: QPushButton):
    button.setStyleSheet(
        """
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border-radius: 6px;
            padding: 6px;
        }
        QPushButton::hover {
            background-color: #45A049;
        }
        """
    )

# --------------------------------------------------------
# Enable Button
# --------------------------------------------------------
def enable_button(button: QPushButton, highlight=False):
    button.setEnabled(True)
    if highlight == True:
        button.setStyleSheet(
        """
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border-radius: 6px;
            padding: 6px;
        }
        QPushButton::hover {
            background-color: #45A049;
        }
        """
    )
    else:
        button.setStyleSheet("")

# --------------------------------------------------------
# Disable Button
# --------------------------------------------------------
def disable_button(button: QPushButton):
    button.setEnabled(False)
    button.setStyleSheet(
        """
        QPushButton {
            background-color: #8A8A8A;
            color: #CCCCCC;
            border-radius: 6px;
            padding: 6px;
        }
        """
    )