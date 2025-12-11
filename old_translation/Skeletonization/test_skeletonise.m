target_dir = '/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/code/Skeletonization/matlab_skels';

binarised_result = '/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/code/Skeletonization/matlab_skels/binarise_matlab_result.mat';
data = load(binarised_result);
bin_img = data.Y_mat;

out_path = fullfile(target_dir, 'bwmorph_matlab_result.mat');

%generate the skeletonized image
[Nx,~] = size(bin_img);
L = logical(bin_img);
sk2 = bwmorph(L,'skel',Inf); %skeletonizes


save(out_path, 'sk2');
fprintf('Saved MATLAB bwmorph output to %s\n', out_path);