% frangi_test_matlab.m
% Set the directory where results will be saved
target_dir = '/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/gui/build/modules/tests';

% 1. Load and convert the image to grayscale
img_path = '/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/LEI/to_be_rename/MILA_renamed/test/5000.tif';
Iraw = imread(img_path);
if ndims(Iraw) == 3
    if size(Iraw,3) == 3
        I = rgb2gray(Iraw);  % ITU-R BT.601 weights [oai_citation:0‡mathworks.com](https://www.mathworks.com/help/matlab/ref/rgb2gray.html#:~:text=,R%2C%20G%2C%20and%20B%20components)
    else
        I = Iraw(:,:,1);
    end
else
    I = Iraw;
end
I = double(I);


% 3. Run 
rng(0);  % for reproducibility if needed
Y_mat = basic_binarise(I)

% 4. Save output
out_path = fullfile(target_dir, 'binarise_matlab_result.mat');
save(out_path, 'Y_mat');
fprintf('Saved MATLAB Binarise output to %s\n', out_path);

