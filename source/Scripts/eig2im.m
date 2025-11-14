function [X,Y,m1,m2]=eig2im(Dxx,Dxy,Dyy)
% Compute eigenvalues and eigenvectors of the 2D Hessian matrix at each pixel
% Inputs:
%   Dxx, Dxy, Dyy - second-order derivatives (Hessian components)
% Outputs:
%   X, Y  - components of the eigenvector corresponding to the minor eigenvalue
%   m1, m2 - sorted eigenvalues (m1 = minor, m2 = major by absolute value)

% Compute second eigenvector components (unnormalized)
v2x = 2*Dxy; 
v2y = Dyy - Dxx + sqrt((Dxx - Dyy).^2 + 4*Dxy.^2);

% Normalize the eigenvector (v2)
norma = sqrt(v2x.^2 + v2y.^2); 
i = (norma ~= 0);
v2x(i) = v2x(i)./norma(i); % normalize x-component
v2y(i) = v2y(i)./norma(i); % normalize y-component

% Compute the orthogonal eigenvector (v1) from v2
v1x = -v2y; 
v1y = v2x;
 
% Compute eigenvalues using closed-form solution for 2x2 symmetric matrix
eig1 = 0.5*(Dxx + Dyy + sqrt((Dxx - Dyy).^2 + 4*Dxy.^2)); % larger eigenvalue
eig2 = 0.5*(Dxx + Dyy - sqrt((Dxx - Dyy).^2 + 4*Dxy.^2)); % smaller eigenvalue

% Take absolute values for comparison
aeig1= abs(eig1); 
aeig2= abs(eig2); 

% Assign minor eigenvalue to m1, major to m2 based on absolute magnitude
m1 = eig1; 
m1(aeig1 > aeig2) = eig2(aeig1 > aeig2); 
m2 = eig2; 
m2(aeig1 > aeig2) = eig1(aeig1 > aeig2); 

% Assign corresponding eigenvector (X, Y) based on which eigenvalue was smaller
X = v1x; 
X(aeig1 > aeig2) = v2x(aeig1 > aeig2); % For all pixels where the absolute value of eig1 is greater than the absolute value of eig2, set the corresponding value in X to be the corresponding value from v2x

Y = v1y; 
Y(aeig1 > aeig2) = v2y(aeig1 > aeig2);  

end
