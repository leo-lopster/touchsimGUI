import sys
import os
import time
import pandas as pd
import numpy as np
import touchsim as ts
from dataclasses import dataclass
from matplotlib.backends.backend_pdf import PdfPages
from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
    QLabel, QPushButton, QGroupBox, QMessageBox, QSizePolicy, QDoubleSpinBox
)

### LOCAL DEPENDENCIES
from guimpl import *
from modelselector import *
from buttonstyler import *

# ------------------------------------------------------------
# Sorted stimulation sites
# ------------------------------------------------------------
SITES = {
    "Thumb (D1)": ["D1d_t", "D1p_f", "Pw1_p"],
    "Index (D2)": ["D2d_t", "D2m_t", "D2p_f", "Pw2_p"],
    "Middle (D3)": ["D3d_t", "D3m_t", "D3p_f", "Pw3_p"],
    "Ring (D4)": ["D4d_t", "D4m_t", "D4p_f"],
    "Little (D5)": ["D5d_t", "D5m_f", "D5p_f", "Pw4_p"],
    "Palm (Pp)": ["Pp1_p", "Pp2_p"]
}

AFFERENTS = ["PC", "RA", "SA1", "PROP", "HAIR"]

# ------------------------------------------------------------
# Data Classes
# ------------------------------------------------------------

@dataclass
class StimData:
    name: str
    path: str
    df: pd.DataFrame

# ------------------------------------------------------------
# Main GUI Class
# ------------------------------------------------------------
class TouchSimApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TouchSim GUI - PyQt5 Version")
        self.resize(850, 600)

        self.loaded_csvs: list[StimData] = []
        self.r = None
        # PSTH bin size in milliseconds (user-configurable)
        self.psth_bin_size = 100.0

        self.build_ui()

    # CLOCK
    def current_time(self):
        return time.ctime(time.time())

    # DEBUG LOGGER
    def log(self, msg):
        print(f"{self.current_time()[-13:-5]} -> {msg}")

    # --------------------------------------------------------
    # Build UI
    # --------------------------------------------------------
    def build_ui(self):
        layout = QHBoxLayout(self)

        ## LEFT PANEL: afferents, CSV, export
        left_panel = QVBoxLayout()

        # Afferent Selection
        aff_group = QGroupBox("Afferent Type")
        aff_layout = QVBoxLayout()

        # Model Selection
        mod_group = QGroupBox("Simulation Model")
        mod_layout = QVBoxLayout()
        self.model_selector = ModelIdxSelector()
        mod_layout.addWidget(self.model_selector)
        mod_group.setLayout(mod_layout)

        # Afferent
        self.aff_type_combo = QComboBox()
        self.aff_type_combo.addItems(AFFERENTS)
        self.aff_type_combo.currentTextChanged.connect(
            self.model_selector.update_for_afferent
        )
        self.model_selector.update_for_afferent("PC")

        # Connector
        aff_layout.addWidget(self.aff_type_combo)
        aff_group.setLayout(aff_layout)

        # CSV load
        csv_group = QGroupBox("Stimulation Input")
        csv_layout = QVBoxLayout()

        self.csv_label = QLabel("No file loaded.")
        load_btn = QPushButton("Import CSV")
        load_btn.clicked.connect(self.load_csv)

        remove_btn = QPushButton("Remove All CSVs")
        remove_btn.clicked.connect(self.clear_loaded_csvs)

        self.csv_list = QListWidget() # Loaded CSV List
        self.csv_list.setSelectionMode(QListWidget.SingleSelection)
        # Plot graphs when selection changes
        self.csv_list.itemSelectionChanged.connect(lambda: plot_selected())

        def plot_selected():
            selected_row = self.csv_list.currentRow()
            csv_data = self.loaded_csvs[selected_row]
            try:
                self.stim_canvas.plot_graph(
                    time=csv_data.df["time"],
                    amplitude=csv_data.df["amplitude"],
                    title=f"Stimulation - {csv_data.name}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Column Name Error", f"{e} column not found in dataset.")
                return
        
            # If a response exists for this stimulus, show its PSTH preview
            try:
                if hasattr(self, 'all_responses') and csv_data.name in self.all_responses:
                    resp = self.all_responses[csv_data.name]
                    self.psth_canvas.plot_psth(response=resp, bin_size=self.psth_bin_size, title=f"PSTH - {csv_data.name}")
                else:
                    # Clear PSTH canvas if no response yet
                    self.psth_canvas.ax.clear()
                    self.psth_canvas.draw()
            except Exception:
                # ignore preview errors
                pass

        csv_layout.addWidget(load_btn)
        csv_layout.addWidget(remove_btn)
        csv_layout.addWidget(self.csv_label)
        csv_layout.addWidget(self.csv_list)
        csv_group.setLayout(csv_layout)

        # Simulation button
        sim_btn = QPushButton("Generate Afferent Response")
        sim_btn.clicked.connect(self.generate_response)
    
        # Export button
        self.export_btn = QPushButton("Export Response")
        self.export_btn.clicked.connect(self.export_response)
        highlight_button(self.export_btn) # add highlight to the button
        disable_button(self.export_btn)

        # Add all widgets
        left_panel.addWidget(aff_group)
        left_panel.addWidget(mod_group) 
        left_panel.addWidget(csv_group)
        # PSTH bin size input
        bin_layout = QHBoxLayout()
        bin_label = QLabel("PSTH bin (ms)")
        self.psth_bin_input = QDoubleSpinBox()
        self.psth_bin_input.setDecimals(1)
        self.psth_bin_input.setRange(0.1, 100000.0)
        self.psth_bin_input.setSingleStep(1.0)
        self.psth_bin_input.setValue(self.psth_bin_size)
        self.psth_bin_input.setSuffix(" ms")
        self.psth_bin_input.valueChanged.connect(lambda v: setattr(self, 'psth_bin_size', float(v)))
        bin_layout.addWidget(bin_label)
        bin_layout.addWidget(self.psth_bin_input)
        left_panel.addLayout(bin_layout)
        left_panel.addWidget(sim_btn)
        left_panel.addWidget(self.export_btn)
        
        left_panel.addStretch()
        layout.addLayout(left_panel, 1) # Width Ratio
        

        ## RIGHT PANEL: Plot display
        right_panel = QVBoxLayout()

        # Stimulus Plot panel
        stim_plot_group = QGroupBox("Stimulation Profile")
        stim_plot_layout = QVBoxLayout()

        self.stim_canvas = MplCanvas()
        self.stim_canvas.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        stim_plot_layout.addWidget(self.stim_canvas)
        stim_plot_group.setLayout(stim_plot_layout)

        # Response Plot panel
        resp_plot_group = QGroupBox("Response Profile")
        resp_plot_layout = QVBoxLayout()

        self.resp_canvas = MplCanvas()
        resp_plot_layout.addWidget(self.resp_canvas)
        resp_plot_group.setLayout(resp_plot_layout)

        # PSTH Plot panel
        psth_plot_group = QGroupBox("PSTH")
        psth_plot_layout = QVBoxLayout()
        self.psth_canvas = MplCanvas()
        psth_plot_layout.addWidget(self.psth_canvas)
        psth_plot_group.setLayout(psth_plot_layout)

        # Add all widgets
        right_panel.addWidget(stim_plot_group)
        right_panel.addWidget(resp_plot_group)
        right_panel.addWidget(psth_plot_group)
        layout.addLayout(right_panel, 3)

        self.log("UI Build Complete")

        
    # --------------------------------------------------------
    # Load CSV
    # --------------------------------------------------------
    def load_csv(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Stimulation CSVs", "", "CSV Files (*.csv)"
        )
        
        if not paths:
            return
        
        for path in paths:
            try:
                df = pd.read_csv(path)
                self.loaded_csvs.append(
                    StimData(
                        name=os.path.basename(path),
                        path=path,
                        df=df
                    )
                )
                self.log(f"Loaded: {path.split('/')[-1]}")
                # self.plot_stimulation_profile()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to load CSV at '{path}':\n{e}"
                    )
        
        self.refresh_csv_list()
    
    def refresh_csv_list(self):
        self.csv_list.clear()
        if not self.loaded_csvs:
            self.csv_label.setText("No file loaded.")
        else:
            self.csv_label.setText("Files loaded:")
        for stim_csv in self.loaded_csvs:
            self.csv_list.addItem(stim_csv.name)

    def get_loaded_csvs(self):
        items = self.csv_list.selectedItems()
        return [
            self.loaded_csvs[self.csv_list.row(i)]
            for i in items
        ]
    
    def clear_loaded_csvs(self):
        if not self.loaded_csvs:
            return
        else:
            self.csv_list.clear()
            self.loaded_csvs.clear()
            self.csv_label.setText("Removed loaded files.")

    # --------------------------------------------------------
    # Plot Stimulation Profile
    # --------------------------------------------------------
    def plot_stimulation_profile(self):
        self.log("Plotting Stimulation Graph")
        if self.csv_data is None:
            QMessageBox.warning(self, "No CSV", "Please import a stimulation CSV first.")
            return

        if "time" not in self.csv_data.columns or "amplitude" not in self.csv_data.columns:
            QMessageBox.critical(self, "Error", "CSV must contain 'time' and 'amplitude' columns.")
            return

        try:
            time = self.csv_data["time"].astype(float)
            amp = self.csv_data["amplitude"].astype(float)
        except:
            QMessageBox.critical(self, "Error", "Could not parse time/amplitude columns as numbers.")
            return

        # plot it
        self.stim_canvas.plot_graph(
            time=time,
            amplitude=amp,
            title="Stimulation Profile (Amplitude vs Time)"
        )

    # --------------------------------------------------------
    # Plot Response Profile
    # --------------------------------------------------------
    def plot_response_profile(self, response: ts.Response):
        try:    
            self.resp_canvas.plot_spikes(
                response=response,
                title="Response Profile (Spikes)"
                )
                                        
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"TouchSim plot failed:\n{e}")
            return

    # --------------------------------------------------------
    # Generate TouchSim Response
    # --------------------------------------------------------
    def generate_single_response(self, stim_data: StimData, selected_aff: str):

        # Afferent
        idx = self.model_selector.selected_idx()

        a = ts.Afferent(
            affclass=selected_aff,
            idx=idx  # None = Random (Default)
            )
        
        # Stimulus
        stim_df = stim_data.df
        stim_name = stim_data.name
        
        try:
            if not "time" in stim_df:
                QMessageBox.critical(self, "Error", f"Missing 'time' column in '{stim_name}'")
            if not "amplitude" in stim_df:
                QMessageBox.critical(self, "Error", f"Missing 'amp' column in '{stim_name}'")
            
            stimulus_timestamp = stim_df.get("time").to_numpy()
            stimulus_trace = stim_df.get("amplitude").to_numpy()
        except:
            QMessageBox.critical(self, "Error", f"Missing/corrupted stimulus data: '{stim_name}'")
            return

        if len(stimulus_timestamp) <= 1:
            QMessageBox.critical(self, "Insufficient Data", "Stimulus should contain at least 2 data points")
            return

        sampling_freq = 1 / (float(stimulus_timestamp[1]) - float(stimulus_timestamp[0]))
        self.log(f"Generating Stimulus. Detected Sampling Frequency: {sampling_freq}")
        s = ts.Stimulus(trace=stimulus_trace, fs=sampling_freq)

        # Response
        self.log(f"Generating Response for {stim_name}")
        r = a.response(s)
        return r
        
    def generate_response(self):
        if len(self.loaded_csvs) == 0:
            QMessageBox.warning(self, "No CSV", "Please import stimulation CSV first.")
            return

        selected_aff = self.aff_type_combo.currentText()
        if not selected_aff:
            QMessageBox.warning(self, "No Afferents", "Select at least one afferent type.")
            return

        responses: dict[str, Response] = {}
        for stim_data in self.loaded_csvs:
            single_response = self.generate_single_response(
                stim_data=stim_data, selected_aff=selected_aff
            )
            responses[stim_data.name] = single_response
        
        # Plotting
        self.log("Plotting Response")
        self.resp_canvas.plot_multiple_spike_sets(responses=responses)
        # Update PSTH preview (combined)
        try:
            self.psth_canvas.plot_multiple_psth(responses=responses, bin_size=self.psth_bin_size, title="Combined PSTH")
        except Exception:
            pass

        # Enable export
        enable_button(self.export_btn, highlight=True)
        self.all_responses = responses
    
    # --------------------------------------------------------
    # Export TouchSim Response
    # --------------------------------------------------------
    def export_response(self):
        try:
            responses = self.all_responses
        except Exception as e:
            QMessageBox.critical(self, "No Response", f"Generate response results before exporting!")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Response CSV", "", "CSV Files (*.csv)"
        )
        if not out_path:
            return
        
        base_dir = os.path.dirname(out_path)
        base_name = os.path.splitext(os.path.basename(out_path))[0]

        # Export spike series data
        try:            
            spike_series_list = [pd.Series(resp.spikes[0], name=name) for name, resp in responses.items()]
            spike_series_df = pd.concat(spike_series_list, axis=1)
            spike_series_df.to_csv(out_path, index=False)
        except Exception as e:
            QMessageBox.warning(self, "Spike Export Error", f"Failed to export spike series to csv")
        
        self.log(f"Spike data exported to: {out_path}")

        # Export PSTH data
        bin_size = self.psth_bin_size
        try:
            psth_list = [
                pd.Series(
                    np.sum(resp.psth(bin=self.psth_bin_size), axis=0), 
                    name=name
                    ) / bin_size for name, resp in self.all_responses.items()
                ]
            psth_df = pd.concat(psth_list, axis=1)
            
            # Calculate average spikes per ms across all responses
            all_spike_densities = []
            for name, response in self.all_responses.items():
                spike_counts = np.sum(response.psth(bin=bin_size), axis=0)
                spike_densities = spike_counts / bin_size
                all_spike_densities.append(spike_densities)
            
            # Calculate average for each bin
            max_bins = max(len(densities) for densities in all_spike_densities)
            avg_spike_per_bin = []
            for bin_idx in range(max_bins):
                bin_values = [densities[bin_idx] for densities in all_spike_densities 
                             if bin_idx < len(densities)]
                avg_spike_per_bin.append(np.mean(bin_values))
            
            # Insert average column at index 0
            psth_df.insert(0, "Average Spikes per ms", avg_spike_per_bin)
        except Exception as e:
            QMessageBox.warning(self, "PSTH Export Error", f"Failed to export PSTH to csv")

        psth_path = os.path.join(base_dir, f"{base_name}_PSTH.csv")
        psth_df.to_csv(psth_path, index=False)
        self.log(f"Spike data exported to: {psth_path}")

        # Export spike graphs and PSTH plots
        
        temp_canvas = MplCanvas()
        
        # Create a combined PDF with spike raster and PSTH plots
        pdf_path = os.path.join(base_dir, f"{base_name}_graphs.pdf")
        try:
            with PdfPages(pdf_path) as pdf:
                # Page 1: Spike raster plot
                temp_canvas.plot_multiple_spike_sets(responses=responses, title="Spike Raster")
                pdf.savefig(temp_canvas.fig, bbox_inches='tight')
                self.log(f"Added spike raster to PDF")
                
                # Additional pages: Individual PSTH plots for each response
                for name, resp in responses.items():
                    try:
                        temp_canvas.plot_psth(response=resp, bin_size=self.psth_bin_size, title=f"PSTH - {name}")
                        pdf.savefig(temp_canvas.fig, bbox_inches='tight')
                        self.log(f"Added PSTH plot for {name} to PDF")
                    except Exception as e:
                        self.log(f"Could not add PSTH for {name}: {e}")
                        continue
                
                # Final page: Combined PSTH plot if multiple responses
                if len(responses) > 1:
                    try:
                        temp_canvas.plot_multiple_psth(responses=responses, bin_size=self.psth_bin_size, title="Combined PSTH")
                        pdf.savefig(temp_canvas.fig, bbox_inches='tight')
                        self.log(f"Added combined PSTH plot to PDF")
                    except Exception as e:
                        self.log(f"Could not add combined PSTH: {e}")
                
                self.log(f"Analysis PDF exported: {pdf_path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Warning", f"Could not export PDF:\n{e}")
        
        QMessageBox.information(self, "Exported", f"Response data and analysis PDF saved to:\n{base_dir}")

# ------------------------------------------------------------
# Run App
# ------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = TouchSimApp()
    gui.show()
    sys.exit(app.exec_())
