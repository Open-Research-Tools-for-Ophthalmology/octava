%Added by mila on for testing basic binarization function
%Function for binarizing image in apptest 2
function [Im]= basic_binarise(Im)


%% %% Make sure vessels are white and the rest is black 
[y] = max(Im);
[~,cc] = max(y);
[~,rr] = max(Im(:,cc));

%% median filter
Im = medfilt2(Im,[3 3]);


%% Binarize 

opts.sigmarange = [1 4];
opts.sigmastepsize=2;
opts.correctionconst1=0.8;
opts.correctionconst2=15;

Im=frangi_2Dfilter(Im,opts);


%Implements Fuzzy thrshold binarization 
%Number of sets;
nth=2;
Im=fuzzy_thresholding(Im,nth,3)-1;  
    

Im(Im==Im(rr,cc)) = 255;
Im(Im~=Im(rr,cc)) = 0;

end