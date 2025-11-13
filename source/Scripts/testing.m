% % run_matlab_fuzzy.m
% % Generate test inputs from your TIF, run MATLAB fuzzy_thresholding, save results.
% 
% rng(0,'twister');   % deterministic FCM init (if used)
% 
% % --- Test image path ---
% imgPath = '/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/LEI/to_be_rename/MILA_renamed/test/5000.tif';
% 
% % --- Read first page of the TIF (handles multi-page gracefully) ---
% info = imfinfo(imgPath);
% if numel(info) >= 1
%     Iraw = imread(imgPath, 1);
% else
%     error('No readable pages in: %s', imgPath);
% end
% 
% % --- Convert to grayscale if needed (no IPT required) ---
% if ndims(Iraw) == 3
%     Iraw = 0.2989*double(Iraw(:,:,1)) + 0.5870*double(Iraw(:,:,2)) + 0.1140*double(Iraw(:,:,3));
% else
%     Iraw = double(Iraw);
% end
% 
% % --- Scale to [0,1] without Image Processing Toolbox ---
% Imin = min(Iraw(:));
% Imax = max(Iraw(:));
% if Imax > Imin
%     I = (Iraw - Imin) / (Imax - Imin);
% else
%     I = zeros(size(Iraw));  % flat image edge-case
% end
% 
% % Use the same image for both test slots (to avoid toolbox sample images)
% I1 = I;
% I2 = I;
% 
% % --- Params (must match Python) ---
% nth = 2;      % clusters
% w   = 3;      % median window
% 
% % --- Run your MATLAB implementation ---
% Y1 = fuzzy_thresholding(I1, nth, w);
% Y2 = fuzzy_thresholding(I2, nth, w);
% 
% % --- Save for Python comparison ---
% save('mat_results.mat', 'I1', 'I2', 'Y1', 'Y2', 'nth', 'w', '-v7');
% disp('Saved mat_results.mat');



% Read original image
Xraw = imread('/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/LEI/to_be_rename/MILA_renamed/test/5000.tif');

% Ensure it is 2D grayscale
if ndims(Xraw) == 2
    X = Xraw;  % already grayscale
elseif ndims(Xraw) == 3
    if size(Xraw,3) == 3
        % RGB -> convert to grayscale
        X = rgb2gray(Xraw);
    else
        % Likely multi-slice TIF: take first slice
        X = Xraw(:,:,1);
    end
else
    error('Unsupported image shape: %s', mat2str(size(Xraw)));
end

X = double(X);   % match fuzzy_thresholding first line

nth = 2;
w   = 3;

rng(0);
Y_mat = fuzzy_thresholding(X, nth, w);

save('fuzzy_matlab_result.mat', 'Y_mat', 'X', 'nth', 'w');