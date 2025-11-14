function [Dxx,Dxy,Dyy] = hessian_filter(I,sigma)

% Make kernel coordinates
[X,Y]   = ndgrid(-round(3*sigma):round(3*sigma));

% Build the gaussian 2nd derivatives filters
DGaussxx = 1/(2*pi*sigma^4) * (X.^2/sigma^2 - 1) .* exp(-(X.^2 + Y.^2)/(2*sigma^2));
DGaussxy = 1/(2*pi*sigma^6) * (X .* Y)           .* exp(-(X.^2 + Y.^2)/(2*sigma^2));
DGaussyy = DGaussxx';

Dxx = imfilter(I,DGaussxx,'conv');
Dxy = imfilter(I,DGaussxy,'conv');
Dyy = imfilter(I,DGaussyy,'conv');

end

