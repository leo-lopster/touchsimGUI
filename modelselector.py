import touchsim as ts
from PyQt5.QtWidgets import (
    QWidget, QComboBox, QVBoxLayout
)
from touchsim import constants

# --------------------------------------------------------
# Model Selector
# --------------------------------------------------------

class ModelIdxSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
    
        self.layout = QVBoxLayout(self)
        # self.label = QLabel("Neuron model (idx)")
        self.combo = QComboBox()

        # self.layout.addWidget(self.label)
        self.layout.addWidget(self.combo)

        self.current_afferent_type = None

    def update_for_afferent(self, afferent_type):
        """
        Rebuild model idx list when afferent type changes
        afferent_type: "SA1", "RA", "PC", "PROP", or "HAIR"
        """
        self.combo.clear()
        self.current_afferent_type = afferent_type

        # Create a temporary afferent to introspect models
        try:
            dummy_aff = ts.Afferent(afferent_type)
        except Exception as e:
            self.combo.addItem("Unavailable")
            self.combo.setEnabled(False)
            return

        models = {
            "SA1": list(range(len(constants.affparamsSA))),
            "RA": list(range(len(constants.affparamsRA))),
            "PC": list(range(len(constants.affparamsPC))),
            "PROP": list(range(len(constants.affparamsPROP))),
            "HAIR": list(range(len(constants.affparamsHAIR))),
            }

        self.combo.setEnabled(True)
        self.combo.addItem("Random (default)", None)

        for idx in range(len(models[afferent_type])):
            self.combo.addItem(f"Model {idx}", idx)

    def selected_idx(self):
        """Returns None (random) or an int idx"""
        return self.combo.currentData()