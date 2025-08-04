function Y=adaptivethresholding(X,w)
% adaptive thresholding algorithm using a local median filter to segment X
% Reference
% Guanglei Xiong (2021). Local Adaptive Thresholding (https://www.mathworks.com/matlabcentral/fileexchange/8647-local-adaptive-thresholding), MATLAB Central File Exchange.
X=mat2gray(X); % normalise image to [0,1]
medianX=imfilter(X,fspecial('average',w),'replicate');
Y=imbinarize(medianX-X,0); % Computes the difference between local mean and actual value
Y=imcomplement(Y); % flips 0 to 1

