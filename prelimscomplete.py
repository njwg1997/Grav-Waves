#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  8 20:18:03 2018

@author: keithstaylor
"""
'''Preface: c = coloured, g = gaussian, w = whitening, td = time domain, fd = frequency domiain '''


import numpy as np
import numpy.fft as fft
import matplotlib.pyplot as pl
import matplotlib.mlab as mlab
from scipy import fftpack as fftp
from scipy import interpolate

MakePlots = 1

"""
Coloured noise generator


Program to take signal in time domain from *.txt file in same directory and
apply noise. Output is a .txt file in time domain. 
Input signal should contain time and signal amplitudes in same file.
Program assumes that the file H1-PSD.txt is in same directory as 
coloured-noise-generator.py, this is generated by noise-psd-ligoH1-GW150914
"""

# load signal from *.txt file, checking user input
filename = input('Enter file name (including \".txt\"): ')
while 1:
    try:
        signal = np.loadtxt(filename)
        break
    except FileNotFoundError:
        filename = input('File not found, please try again... ')

t = signal[:, 0]
h = signal[:, 1]

N = len(h)
Ts = t[1]-t[0]
Fs = 1./Ts

# convert signal to freq domain
xf_h = fft.rfftfreq(N, Ts)
hf = fft.rfft(h) 


#load noise and and scale to signal, also randomise phase
ligo_fft = np.loadtxt('H1-FFT.txt', dtype='complex128')
xf_n = abs(ligo_fft[:, 0])
nf = ligo_fft[:, 1]


# ensure both have same length in the frequency domain
if len(hf) < len(nf):
    hf = np.interp(xf_n, xf_h, hf)
    xf = xf_n
elif len(hf) > len(nf):
    nf = np.interp(xf_h, xf_n, nf)
    xf = xf_h
#get new time scale
t1 = np.linspace(0., 2*(len(xf)-1)*1/(2*xf[-1]), 2*(len(xf)-1))

# combine noise and signal and convert back to time domain
df = nf+hf  
d = fft.irfft(df)



#%%
'''random noise generator'''
m = 0
sd = 10

noise = np.random.normal(m,sd,N) #Gaussian Noise 
ny = h + noise #noisy signal 

#%%
'''ASD'''
#coloured noise
NFFT = len(ny)

Pxx_gaussian, freqs = mlab.psd(ny, NFFT = int(NFFT), Fs = Fs, window=mlab.window_hanning)
PSD_gaussian = interpolate.interp1d(freqs, Pxx_gaussian)

#random noise
Pxx_coloured, freqs = mlab.psd(d, NFFT = int(NFFT), Fs = Fs, window=mlab.window_hanning)
PSD_coloured = interpolate.interp1d(freqs, Pxx_coloured)


#%%
'''Plotting - plotting the original signal, both noisy signals in the time 
   domain, both signals PSD's'''

if MakePlots:    
    #plot original signal 
    pl.figure(1) 
    pl.title('Original Signal')
    pl.plot(t,h)
    pl.xlabel('Time (s)')
    pl.ylabel('Amplitude')
    pl.grid()

    #plot gaussian noisy signal
    pl.figure(2)
    pl.subplot(211)
    pl.title('Original Signal + gaussian noise')
    pl.plot(t, ny)
    pl.xlabel('Time (s)')
    pl.ylabel('Amplitude')
    pl.grid()

    pl.subplot(212)
    pl.title('Original signal + coloured noise')
    pl.plot(t, d)
    pl.xlabel('Time (s)')
    pl.ylabel('Amplitude')
    pl.grid()

    #psd's of gaus and col
    pl.figure(3)

    pl.subplot(211)
    pl.loglog(freqs, np.sqrt(Pxx_gaussian))
    pl.title('ASD, gaussian noise')
    pl.xlabel('Freq (Hz)')
    pl.ylabel('ASD (strain)')
    pl.grid()

    pl.subplot(212)
    pl.loglog(freqs, np.sqrt(Pxx_coloured))
    pl.title('ASD, coloured LIGO noise')
    pl.xlabel('Freq (Hz)')
    pl.ylabel('ASD (strain)')
    pl.grid()

    pl.show


#%%
'''Spectrograms - spectrograms of the gaussian and coloured noisy data'''

NFFT1 = int(Fs/8)
NOVL = int(NFFT1*15./16)
window = np.blackman(NFFT)
spec_cmap='ocean'

if MakePlots:
    pl.figure(4)
    pl.subplot(211)
    Pxx, freqs, bins, im = pl.specgram(ny, NFFT=NFFT1, Fs=Fs, window=window, noverlap=NOVL, cmap=spec_cmap)
    pl.colorbar()

    pl.subplot(212)
    Pxx, freqs, bins, im = pl.specgram(d, NFFT=NFFT1, Fs=Fs, window=window, noverlap=NOVL, cmap=spec_cmap)
    pl.colorbar()

    pl.show()

#%%
'''Whitening  - transform to freq domain, divide by asd, transform back
   also plotting the whitened data in the time domain'''

#gaussian
# xf_h = np.fft.rfftfreq(N, Ts)
#convert to frequency domain
gfd2 = fftp.fft(ny) #2 sided fft
gfd1 = gfd2[0:(N//2)+1] #1 sided fft

#divide by sqrt of psd to whiten
gw = gfd1/ np.sqrt(Pxx_gaussian)

#convert back to time domain
gwtd = np.fft.irfft(gw)


#coloured
cfd2 = fftp.fft(d) #2 sided fft
cfd1 = cfd2[0:(N//2)+1] #1 sided fft

#divide by sqrt of psd to whiten
cw = cfd1/ np.sqrt(Pxx_coloured)
#convert back to time domain
cwtd = np.fft.irfft(cw)

if MakePlots:
    pl.figure(5)

    pl.subplot(211)
    pl.title('Whitened Gaussian Signal')
    pl.plot(t,gwtd, label='Whitened Signal')
    pl.xlabel('Time (s)')
    pl.ylabel('Amplitude')
    pl.grid()

    pl.subplot(212)
    pl.title('Whitened Coloured Signal')
    pl.plot(t,cwtd, label='Whitened Signal')
    pl.xlabel('Time (s)')
    pl.ylabel('Amplitude')
    pl.grid()

    pl.show()

    
#%%
'''Upload templates?'''

#%%
'''Windowing of whitened signals and templates'''

window1 = np.blackman(1000)
'''np.blackman cannot be applied to any 
data with a different # of points than itself'''
data1 = gwtd * window1
window1fft = fftp.fft(window1) / (len(window1)/2.0)
freq = np.linspace(-0.5, 0.5, len(window1fft))
response = 20 * np.log10(np.abs(fftp.fftshift(window1fft / abs(window1fft).max())))


data2 = cwtd * window1

if MakePlots:
    pl.figure(6)

    pl.subplot(3,1,1)
    pl.plot(window1)
    pl.set_xlabel('X')
    pl.set_ylabel('Y')
    pl.grid()
    '''shows spectral leakage of the window in the F domain'''
    pl.subplot(3,1,2)
    pl.plot(freq, response)
    pl.set_xlabel('Frequency')
    pl.set_ylabel('response')
    pl.grid()

    pl.subplot(3,1,3)
    pl.plot(data1)
    pl.set_xlabel('X')
    pl.set_ylabel('Y')
    pl.grid()

    pl.figure(7)

    pl.subplot(3,1,1)
    pl.plot(window1)
    pl.set_xlabel('X')
    pl.set_ylabel('Y')
    pl.grid()
    '''shows spectral leakage of the window in the F domain'''
    pl.subplot(3,1,2)
    pl.plot(freq, response)
    pl.set_xlabel('Frequency')
    pl.set_ylabel('response')
    pl.grid()

    pl.subplot(3,1,3)
    pl.plot(data2)
    pl.set_xlabel('X')
    pl.set_ylabel('Y')
    pl.grid()

    pl.show()



