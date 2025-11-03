clear all;
clc;
close all;

for c=1:6
    archivo=['epocas_P300_C' int2str(c) '.dat'];
    x=load(archivo);
    promedios(c,:)=mean(x');
    archivo=['epocas_sinP300_C' int2str(c) '.dat'];
    x=load(archivo);
    promedios_sp(c,:)=mean(x');
end;

