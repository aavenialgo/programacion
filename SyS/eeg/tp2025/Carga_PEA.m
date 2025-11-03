clear all;
clc;
close all,

% Lectura de datos del registro
registros=load('PEA.mat');
pe=registros.ALLEEG.data;
[canales,N]=size(pe);
Etiquetas=registros.ALLEEG.chanlocs;
eventos=registros.ALLEEG.event;

for n=1:length(eventos)
    estimulos(n)=eventos(n).latency;
end;
fm=registros.ALLEEG.srate;