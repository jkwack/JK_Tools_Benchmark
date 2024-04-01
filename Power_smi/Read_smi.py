#!/usr/bin/python3

#
# Description: Read a CSV file from nvidia-smi, xpu-smi, & rocm-smi (later), and then report its power usage
#
# Bug reports & feature requests: Please reach out to JaeHyuk Kwack (jkwack@anl.gov)
#

# Importing Libraries
from __future__ import division
import os, sys, getopt
import csv
import matplotlib.pyplot as plt
from datetime import datetime


def get_args(argv):
    if len(sys.argv) < 2:
        print ('./Read_smi.py -i <input csv file>')
        sys.exit(2)
    try:
        opts, args = getopt.getopt(argv,"hi:v",["ifile="])
    except getopt.GetoptError:
        print ('./Read_smi.py -i <input csv file>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('./Read_smi.py -i <input csv file>')
            sys.exit()
        if opt in ("-i", "--ifile"):
            csvfilename = arg
        if opt  == '-v':
            isverbose = True
        else:
            isverbose = False

    try: 
        print ('     Input CSV filename = {0} '.format(csvfilename))
    except:
        print ('./Read_smi.py -i <input csv file>')
        sys.exit()

    return csvfilename, isverbose

if __name__ == "__main__":

    T = []
    Freq = []
    Util = []
    P = []
    E = []

    csvfilename, isverbose = get_args(sys.argv[1:])
    with open(csvfilename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames

        for row in reader:
            # For XPU-SMI
            if 'Timestamp' in fieldnames:
                Tstamp = datetime.strptime(row['Timestamp'], "%H:%M:%S.%f")
                Reftime = datetime(1900, 1, 1)
                Treport = Tstamp - Reftime
                T.append(Treport.total_seconds())
            if ' GPU Frequency (MHz)' in fieldnames:
                Freq.append(float(row[' GPU Frequency (MHz)']))
            if ' GPU Utilization (%)' in fieldnames:
                Util.append(float(row[' GPU Utilization (%)']))
            if ' GPU Power (W)' in fieldnames:
                 P.append(float(row[' GPU Power (W)']))
            if ' GPU Energy Consumed (J)' in fieldnames:
                 E.append(float(row[' GPU Energy Consumed (J)']))

            # For NVIDIA-smi
            if 'timestamp' in fieldnames:
                Tstamp = datetime.strptime(row['timestamp'], "%Y/%m/%d %H:%M:%S.%f")
                Reftime = datetime(2024, 1, 1)
                Treport = Tstamp - Reftime
                T.append(Treport.total_seconds())
            if ' clocks.current.graphics [MHz]' in fieldnames:
                Freq.append(float(row[' clocks.current.graphics [MHz]'][:-3]))
            if ' utilization.gpu [%]' in fieldnames:
                Util.append(float(row[' utilization.gpu [%]'][:-1]))
            if ' power.draw [W]' in fieldnames:
                P.append(float(row[' power.draw [W]'][:-1]))

        if isverbose:
            print(reader.fieldnames)

        # Adjust the reference time
        minT = T[0]
        T = [t - minT for t in T]
        dT = max(T)
        # dT = len(T)-1

        # Computing energy (J) using power (W)
        Energy = (sum(P[:-1]) + sum(P[1:]) ) / 2 / (len(P)-1) * dT
        print("        - Energy used     = {0:.3f} Wh".format(Energy/3600))
        print("        - Time Duration   = {0:.1f} sec".format(dT))
        print("        - Power range     = {0:.1f} - {1:.1f} W".format(min(P),max(P)))
        print("        - Frequency range = {0:.1f} - {1:.1f} MHz".format(min(Freq),max(Freq)))


        # Write the time series without units in a csv file
        csvout = 'CSV_OUT_'+csvfilename
        fcsvout = open(csvout,"w")
        fcsvout.write("T(sec), Util(%), Power(Wh), Freq(MHz)\n")
        for i, t in enumerate(T):
            fcsvout.write("{0:f}, {1:f}, {2:f}, {3:f}\n".format(t,Util[i],P[i],Freq[i]))
        fcsvout.close()


        # Draw plots for Util, Power, and Frequency
        fig, ax = plt.subplots(layout='constrained',figsize=(10,3))
        ax2 = ax.twinx()
        ax.plot(Util,color='darkorange')
        ax.plot(P,color='royalblue')
        ax2.plot(Freq,color='dimgrey')
        ax.set_xlabel('T(sec)')
        ax.set_ylim(0,max(max(P),max(Util))*1.1)
        ax.set_ylabel('Power(W) / Utilization(%)')
        ax2.set_ylabel('Frequency(MHz)')
        ax2.set_ylim(0,max(Freq)*1.1)
        plt.savefig(csvfilename+'.png',dpi=300); 


    if isverbose:
        print(T)
        print(Freq)
        print(Util)
        print(P)
        if E:
            print(E)
            print("Energy reported via xpu-smi (J): ",E[-1]-E[0]) 

