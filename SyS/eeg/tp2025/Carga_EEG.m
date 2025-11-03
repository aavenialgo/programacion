clear all;
clc;
close all,

% Lectura de datos del registro
registros=load('EEG8C_Alfa.mat');
eeg=registros.ALLEEG.data;
[canales,N]=size(eeg);
Etiquetas=registros.ALLEEG.chanlocs;
fm=registros.ALLEEG.srate;
%Canal1=F3, Canal2=F4, Canal3=C4, Canal4=C3 
%Canal5=P4, Canal6=P3, Canal7=O2, Canal8=O1