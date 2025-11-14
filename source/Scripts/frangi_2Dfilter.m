% Mila is working on this

function Y= frangi_2Dfilter(X, opts)

% Reference:
%
% A. F. Frangi, W. J. Niessen, K. L. Vincken, and M. A. Viergever, 
% “Multiscale Vessel Enhancement Filtering,” in Medical Image Computing and Computer-Assisted Intervention, 
% Lecture Notes in Computer Science, Wells WM, C. A, and Delp S, Eds. Verlag: Springer, 1998, pp. 130–137.

sigmas=opts.sigmarange(1):opts.sigmastepsize:opts.sigmarange(2);
sigmas = sort(sigmas, 'ascend');

beta  = 2*opts.correctionconst1^2;
c     = 2*opts.correctionconst2^2;

% Make matrices to store all filterd images
filtX_persigma=zeros([size(X) length(sigmas)]);
angles_persigma=zeros([size(X) length(sigmas)]);

for i = 1:length(sigmas)
    [Dxx,Dxy,Dyy] = hessian_filter(X,sigmas(i));
    var= (sigmas(i)^2);
    Dxx= var*Dxx; Dxy= var*Dxy; Dyy= var*Dyy;
    [Xi,Yi,m2,m1]=eig2im(Dxx,Dxy,Dyy);

    % direction of minor eigenvector
    angles = atan2(Xi,Yi);

    % Compute some similarity measures
    m1(m1==0) = eps;
    mratio = (m2./m1).^2;
   
    % Compute the output image
    Xfiltered = exp(-mratio/beta) .*(ones(size(X))-exp(-(m1.^2 + m2.^2)/c)); 
    Xfiltered(m1>0)=0;
    filtX_persigma(:,:,i) = Xfiltered;
    angles_persigma(:,:,i) = angles;
end

Y= max(filtX_persigma,[],3);
Y = reshape(Y,size(X)); 

end

