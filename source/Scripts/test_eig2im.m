% eig2im_test_matlab.m
% Set the target directory (same as Hessian test)
target_dir = '/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/gui/build/modules/tests';

% Sigma values to test
sigma_values = [1, 3];

for sigma = sigma_values
    % Load the Hessian components from the MATLAB test
    hfile = fullfile(target_dir, sprintf('hessian_matlab_sigma%d.mat', sigma));
    data  = load(hfile);  % contains Dxx, Dxy, Dyy
    Dxx = data.Dxx;  Dxy = data.Dxy;  Dyy = data.Dyy;
    
    % Compute eigenvectors and eigenvalues
    [X, Y, m1, m2] = eig2im(Dxx, Dxy, Dyy);
    
    % Save results
    outfile = fullfile(target_dir, sprintf('eig2im_matlab_sigma%d.mat', sigma));
    save(outfile, 'X', 'Y', 'm1', 'm2');
    fprintf('Saved MATLAB eig2im outputs for sigma=%d to %s\n', sigma, outfile);
end