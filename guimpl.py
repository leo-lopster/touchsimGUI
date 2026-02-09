from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
from touchsim import Afferent, Response
from PyQt5.QtWidgets import QMessageBox
from touchsim_gui import StimData
import numpy as np

# ------------------------------------------------------------
# Matplotlib canvas for embedding plots in PyQt5
# ------------------------------------------------------------

class MplCanvas(FigureCanvas):
    def __init__(self, timespan):
        self.fig = Figure(figsize=(4, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.timespan = timespan
        super().__init__(self.fig)

    def plot_graph(self, time, amplitude, title="Unnamed Graph"):
        self.ax.clear()
        self.ax.plot(time, amplitude)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Amplitude (mm)")
        self.ax.set_title(title)
        self.ax.set_xlim(0, self.timespan)
        self.ax.grid(True)
        self.draw()

    def plot_spikes(self, response: Response, bin: list=[0, 0], title="Unnamed Spike Series"):
        self.ax.clear()
        bin = [0, response.duration]
        try:
            for i, spikes in enumerate(response.spikes):
                if len(spikes) > 0:
                    self.ax.vlines(spikes, i, i + 0.5, color=Afferent.affcol[response.aff.afferents[i].affclass])
        
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"TouchSim plot failed:\n{e}")
            return
        
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Neuron Index")
        self.ax.set_xlim(0, self.timespan)
        self.ax.set_title(title)
        self.ax.grid(True)
        self.draw()

    def plot_multiple_graphs(self, data: list[StimData]):
        self.ax.clear()

        for stim in data:
            self.ax.plot(
                stim.df["time"],
                stim.df["amplitude"],
                label=stim.name
            )

        self.ax.set_xlim(0, self.timespan)
        self.ax.legend()
        self.draw()

    def plot_multiple_spike_sets(self, responses: dict[str, Response], title="Spike Raster"):
        """Plot multiple spike Response objects on the same axes.

        Each response's neuron indices are shifted up by 1 for each subsequent
        response (i.e., set 0: neurons at 0..N-1, set 1: neurons at 1..N, etc.).
        """
        self.ax.clear()

        try:
            # # determine x limits from responses
            # max_t = 0
            # for r in responses:
            #     if hasattr(r, 'duration'):
            #         max_t = max(max_t, r.duration)

            for set_idx, name in enumerate(responses):
                for i, spikes in enumerate(responses[name].spikes):
                    if len(spikes) > 0:
                        y0 = i + set_idx
                        y1 = y0 + 0.65
                        try:
                            col = Afferent.affcol[responses[name].aff.afferents[i].affclass]
                        except Exception:
                            col = None
                        self.ax.vlines(spikes, y0, y1, color=col)

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"TouchSim plot failed:\n{e}")
            return

        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Stimulus Index")
        self.ax.set_xlim(0, self.timespan)
        self.ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
        self.ax.set_title(title)
        self.ax.grid(True)
        self.draw()

    def plot_psth(self, response: Response, bin_size=10.0, title="PSTH"):
        """Plot Peri-Stimulus Time Histogram (PSTH) for a single Response object.

        Uses the Response.psth() method to compute the histogram data.
        
        Args:
            response: Response object to plot
            bin_size: Time bin size in milliseconds (default: 10.0 ms)
            title: Title for the plot
        """
        self.ax.clear()

        try:
            # Get PSTH data from response object
            # Returns NxB array (N: number of afferents, B: number of bins)
            # Each bin contains the count of spikes that fall within that time interval
            psth_data = response.psth(bin=bin_size)
            
            # Sum across all afferents to get total spike intervals per bin
            spike_counts = np.sum(psth_data, axis=0)
            spike_densities = spike_counts / bin_size
            
            # Create time bin edges (in seconds)
            bin_size_sec = bin_size / 1000.0
            num_bins = len(spike_counts)
            bin_edges = np.arange(num_bins + 1) * bin_size_sec
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            # Plot as histogram bars
            self.ax.bar(bin_centers, spike_densities, width=bin_size_sec * 0.9, 
                       edgecolor='black', linewidth=1.5, align='center')
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Spikes per ms")
            self.ax.set_title(title)
            self.ax.set_xlim(0, self.timespan)
            self.ax.grid(True, alpha=0.3, axis='y')

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to plot PSTH:\n{e}")
            return

        self.draw()

    def plot_multiple_psth(self, responses: dict[str, Response], bin_size=10.0, title="Multiple PSTH"):
        """Plot histogram of average spikes per ms for multiple Response objects.

        Creates a histogram showing the average spike count per millisecond
        for each time bin across all responses. Bins are centered between tick marks.
        
        Args:
            responses: Dictionary mapping names to Response objects
            bin_size: Time bin size in milliseconds (default: 10.0 ms)
            title: Title for the plot
        """
        self.ax.clear()

        try:
            # Collect spike data from all responses
            all_spike_densities = []
            
            for name, response in responses.items():
                # Get PSTH data from response object
                # Returns NxB array (N: number of afferents, B: number of bins)
                # Each bin contains the count of spike intervals in that time window
                psth_data = response.psth(bin=bin_size)
                
                # Sum across all afferents to get total spike intervals per bin
                spike_counts = np.sum(psth_data, axis=0)
                # Calculate average spikes per ms
                spike_densities = spike_counts / bin_size
                all_spike_densities.append(spike_densities)
            
            # Calculate average spike density across all responses for each bin
            max_bins = max(len(densities) for densities in all_spike_densities)
            avg_spike_per_bin = []
            
            for bin_idx in range(max_bins):
                bin_values = [densities[bin_idx] for densities in all_spike_densities 
                             if bin_idx < len(densities)]
                avg_spike_per_bin.append(np.mean(bin_values))
            
            # Create time bin edges and centers (in seconds) following plot_psth convention
            bin_size_sec = bin_size / 1000.0
            num_bins = len(avg_spike_per_bin)
            bin_edges = np.arange(num_bins + 1) * bin_size_sec
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            # Plot as histogram bars centered between ticks
            self.ax.bar(bin_centers, avg_spike_per_bin, width=bin_size_sec * 0.9,
                       edgecolor='black', linewidth=1.5, align='center')
            
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Average Spikes per ms")
            self.ax.set_title(title)
            self.ax.set_xlim(0, self.timespan)
            self.ax.grid(True, alpha=0.3, axis='y')

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to plot PSTH:\n{e}")
            return

        self.draw()