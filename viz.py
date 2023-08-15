from io import TextIOWrapper
import sys
from typing import List
import numpy as np

import ipywidgets as ipw
import hvplot as hv # noqa
import hvplot.xarray # noqa
import hvplot.pandas # noqa
import panel as pn
import pandas as pd
import panel.widgets as pnw
import xarray as xr
import matplotlib.pyplot as plt


# this changes the default date converter for better interactive plotting of dates:
#plt.rcParams['date.converter'] = 'concise'
hvplot.extension('bokeh')


class StimIndex:
    def __init__(self) -> None:
        self.raw:List[int] = []

    def add(self, value:int):
        self.raw.append(value)

    def is_full(self) -> bool:
        return len(self.raw) == 10

    def get_index(self):
        return self.raw[0]

    def get_intensity(self):
        return self.raw[1]

    def get_num_milliseconds(self):
        return self.raw[2]


class LapsData:
    def __init__(self, data_ch0:List[int], data_ch1:List[int], stim_indices:List[StimIndex], datetime:List[int]) -> None:
        self.data_ch0 = data_ch0
        self.data_ch1 = data_ch1
        self.stim_indices = stim_indices
        self.datetime = datetime

    def get_stim_data(self):
        data0 = np.array(self.data_ch0)
        data2 = np.zeros(data0.size)
        for stims in self.stim_indices:
            ix = stims.get_index()
            data2[ix] = stims.get_intensity()
        return data2


    def display_hvplot(self, filename:str):
        data0 = np.array(self.data_ch0)
        data1 = np.array(self.data_ch1)
        data2 = self.get_stim_data()

        data = np.column_stack((data0, data1, data2))

        df = pd.DataFrame(data, index=self.datetime, columns=list('ABC'))
        plot = df.hvplot.line()
        hvplot.show(plot)


    def display_matplotlib(self, filename:str):
        print(f"finished reading file: {len(self.data_ch0)} data points")
        data0 = np.array(self.data_ch0)
        data1 = np.array(self.data_ch1)
        data2 = self.get_stim_data()

        fig, (ax0, ax1, ax2) = plt.subplots(3, 1, sharex=True, constrained_layout=True)

        ch0_low = np.convolve(data0, np.ones(48)/48, mode='same')
        ch1_low = np.convolve(data1, np.ones(48)/48, mode='same')

        # ch0:
        ax0.plot(self.datetime, data0, label='ch-0 (ms)')
        ax0.plot(self.datetime, ch0_low, label='smoothed')
        ax0.legend(loc='upper right')
        ax0.set_ylabel('mV $[W\,m^{-2}]$')

        # ch1:
        ax1.plot(self.datetime, data1, label='ch-1 (ms)')
        ax1.plot(self.datetime, ch1_low, label='smoothed')
        ax1.legend(loc='upper right')
        ax1.set_ylabel('mV $[W\,m^{-2}]$')

        # stimulations:
        ax2.plot(self.datetime, data2, label='Stimulation (ms)')
        ax2.legend(loc='upper right')
        ax2.set_ylabel('mV $[W\,m^{-2}]$')

        ax0.set_title('MEP', loc='left')
        ax0.text(0.03, 0.03, filename,
                fontsize='small', fontstyle='italic', transform=ax0.transAxes)

        plt.show(block=True)



def read_file(fp:TextIOWrapper) -> LapsData:
    print("reading file")
    datetime = []
    ix = 0
    data_ch0 = []
    data_ch1 = []

    current_stim_index:StimIndex = StimIndex()
    stim_indices: List[StimIndex] = []

    sectionName = ''
    while True:
        p = fp.readline()
        if len(p) == 0:
            break
        if p.startswith('['):
            sectionName = p.strip()
        else:
            if sectionName == '[StimIndex]':
                if current_stim_index == None or current_stim_index.is_full():
                    current_stim_index = StimIndex()
                    stim_indices.append(current_stim_index)
                current_stim_index.add(int(p))

            if sectionName == '[LapsSignalData]':
                values = p.split()
                data_ch0.append(int(values[0]))
                data_ch1.append(int(values[1]))

                #if int(values[1]) != 0:
                #    print(f"value changes at {ix} to {values[1]}")

                datetime.append(ix)
                ix += 1

    return LapsData(data_ch0, data_ch1, stim_indices, datetime)



def show_usage():
    print("USAGE: python viz [-matplotlib] [-hvplot] <filename.txt>")

def main():
    filename = None
    plotter = 0
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            filename = arg
        elif arg == "-matplotlib":
            plotter = 0
        elif arg == "-hvplot":
            plotter = 1

    if filename == None:
        show_usage();
        sys.exit(1)

    fp = open(filename)
    laps_data = read_file(fp)

    if plotter == 0:
        with plt.ion():
            laps_data.display_matplotlib(filename)
    else:
        laps_data.display_hvplot(filename)
    fp.close()


main()