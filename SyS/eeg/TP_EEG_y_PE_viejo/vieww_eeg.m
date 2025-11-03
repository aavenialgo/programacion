clear all;
close all;
clc;

fs=256;

canales=load('Practico_EEGS001R03.mat');
c1=canales.signal(1:256*70,1);
c1=c1-mean(c1);
c2=canales.signal(1:256*70,2);
c2=c2-mean(c2);
c3=canales.signal(1:256*70,3);
c3=c3-mean(c3);
c4=canales.signal(1:256*70,4);
c4=c4-mean(c4);
c5=canales.signal(1:256*70,1);
c5=c5-mean(c5);
c6=canales.signal(1:256*70,2);
c6=c6-mean(c6);
