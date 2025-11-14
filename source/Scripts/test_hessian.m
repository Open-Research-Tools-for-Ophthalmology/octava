% hessian_test_matlab.m
% Ensure the "tests" directory exists
target_dir = '/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/gui/build/modules/tests';

% 1. Load the .tif image
img_path = '/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/LEI/to_be_rename/MILA_renamed/test/5000.tif';
Iraw = imread(img_path);

% 2. Convert to grayscale if needed
if ndims(Iraw) == 3
    if size(Iraw, 3) == 3
        I = rgb2gray(Iraw);  % uses ITU-R BT.601 weights [oai_citation:0‡mathworks.com](https://www.mathworks.com/help/matlab/ref/rgb2gray.html#:~:text=,R%2C%20G%2C%20and%20B%20components)
    else
        I = Iraw(:,:,1);
    end
else
    I = Iraw;
end
I = double(I);

% 3. Choose sigma values (matching Python)
sigma_values = [1, 3];

% 4. Compute and save each Hessian component for each sigma
for sigma = sigma_values
    [Dxx, Dxy, Dyy] = hessian_filter(I, sigma);
    filename = fullfile(target_dir, sprintf('hessian_matlab_sigma%d.mat', sigma));
    save(filename, 'Dxx', 'Dxy', 'Dyy');
    fprintf('Saved MATLAB Hessian outputs for sigma=%d to %s\n', sigma, filename);
end

