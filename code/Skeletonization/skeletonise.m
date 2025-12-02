clear all
clc
clear
clc
% This is the pipeline that skeletonizes the matlab binarized image
% the image is then exported as a .mat file to be compared in python
% the file contains all the functions involved in the skeletonization
% process. If you wish to debug or play around with them separately you can
% also do this by simply calling them. They are all defined below
THR = 1 % hyperparameter (I've been using THR = 1 for all tests)
data = load('binarise_matlab_result.mat')
mat_bin = data.Y_mat
[skel, nodes, links] = skeletonize_main(mat_bin, THR)
% Display the skeletonized image
figure;
imshow(skel, []);
title('Skeletonized Image');
% export
outdir = '/Users/mutrera/Documents/Uchicago College/Uchicago 2024 - 2025/Summer/Octava/octava/code/Skeletonization/matlab_skels';
save(fullfile(outdir, 'full_skel_mat.mat'), 'skel');

% SKEL MAIN LOGIC FROM THE .MLAPP FILE (W/O PLOTTING LOGIC)
function [skel2, nodes, links] = skeletonize_main(bin_img, THR)
    %generate the skeletonized image
    [Nx,~] = size(bin_img);
    L = logical(bin_img);
    sk2 = bwmorph(L,'skel',Inf); %skeletonizes
    
    %removes branches smaller than twig size
    sk2 = bwskel(sk2,'MinBranchLength', THR);
    
    %Local thickness measurement
    D = bwdist(~L)*2; %Distance transform gives euclidean distance to nearest bg pixel
    %D is the closest I can get to the local thickness map so far, so
    %saving as such. Factor of 2 since distance transform gives radius
    %Network analysis
    %Based on code written by Philip Kollmannsberger
    if sum(sum(sk2)) == 0
        nodes = [];
        links = [];
    else
        [~,nodes,links] = Skel2Graph3D(sk2, THR);
        
        
        %Calculate total length of network
        wl = sum(cellfun('length',{nodes.links}));
        
        %iterate to clean up network and get rid of excess nodes
        skel2 = Graph2Skel3D(nodes,links,Nx,Nx,1);
        [~,nodes,links] = Skel2Graph3D(skel2,0);
        wl_new = sum(cellfun('length',{nodes.links}));
        
        % iterate the same steps until network length changed by less than 0.5%
        while(wl_new~=wl)
            
            wl = wl_new;
            
            skel2 = Graph2Skel3D(nodes,links,Nx,Nx,1);
            [~,nodes,links] = Skel2Graph3D(skel2,0);
            
            wl_new = sum(cellfun('length',{nodes.links}));
        end
    end
end
% GRAPH2SKEL3D
function skel = Graph2Skel3D(node,link,w,l,h)
% create binary image
skel = false(w,l,h);
% for all nodes
for i=1:length(node)
    if(~isempty(node(i).links)) % if node has links
        skel(node(i).idx)=true; % node voxels
        a = [link(node(i).links(node(i).links>0)).point];
        if(~isempty(a))
            skel(a)=1; % edge voxels
        end;
    end;
end;
end
% SKEL2GRAPH3D
function [A,node,link] = Skel2Graph3D(skel,THR)
% SKEL2GRAPH3D Calculate the network graph of a 3D voxel skeleton
%
% [A,node,link] = SKEL2GRAPH3D(skel,THR)
%
% where "skel" is the input 3D binary image, and "THR" is a threshold for
% the minimum length of branches. A is the adjacency matrix, and node/link
% are structures describing node and link properties
%
% Philip Kollmannsberger (philipk@gmx.net)
%
% For more information, see <a
% href="matlab:web('http://uk.mathworks.com/matlabcentral/fileexchange/43527-skel2graph-3d')">Skel2Graph3D</a> at the MATLAB File Exchange.
% pad volume with zeros
skel=padarray(skel,[1 1 1]);
% create label matrix for different skeletons
cc_skel=bwconncomp(skel);
lm=labelmatrix(cc_skel);
% image dimensions
w=size(skel,1);
l=size(skel,2);
h=size(skel,3);
% need this for labeling nodes etc.
skel2 = uint16(skel);
% all foreground voxels
list_canal=find(skel);
% 26-nh of all canal voxels
nh = logical(pk_get_nh(skel,list_canal));
% 26-nh indices of all canal voxels
nhi = pk_get_nh_idx(skel,list_canal);
% # of 26-nb of each skel voxel + 1
sum_nh = sum(logical(nh),2);
% all canal voxels with >2 nb are nodes
nodes = list_canal(sum_nh>3);
% all canal voxels with exactly one nb are end nodes
ep = list_canal(sum_nh==2);
% all canal voxels with exactly 2 nb
cans = list_canal(sum_nh==3);
% Nx3 matrix with the 2 nb of each canal voxel
can_nh_idx = pk_get_nh_idx(skel,cans);
can_nh = pk_get_nh(skel,cans);
% remove center of 3x3 cube
can_nh_idx(:,14)=[];
can_nh(:,14)=[];
% keep only the two existing foreground voxels
can_nb = sort(logical(can_nh).*can_nh_idx,2);
% remove zeros
can_nb(:,1:end-2) = [];
% add neighbours to canalicular voxel list (this might include nodes)
cans = [cans can_nb];
% group clusters of node voxels to nodes
node=[];
link=[];
tmp=false(w,l,h);
tmp(nodes)=1;
cc2=bwconncomp(tmp); % number of unique nodes
num_realnodes = cc2.NumObjects;
% create node structure
for i=1:cc2.NumObjects
    node(i).idx = cc2.PixelIdxList{i};
    node(i).links = [];
    node(i).conn = [];
    [x,y,z]=ind2sub([w l h],node(i).idx);
    node(i).comx = mean(x);
    node(i).comy = mean(y);
    node(i).comz = mean(z);
    node(i).ep = 0;
    node(i).label = lm(node(i).idx(1));
   
    % assign index to node voxels
    skel2(node(i).idx) = i+1;
end;
tmp=false(w,l,h);
tmp(ep)=1;
cc3=bwconncomp(tmp); % number of unique nodes
% create node structure
for i=1:cc3.NumObjects
    ni = num_realnodes+i;
    node(ni).idx = cc3.PixelIdxList{i};
    node(ni).links = [];
    node(ni).conn = [];
    [x,y,z]=ind2sub([w l h],node(ni).idx);
    node(ni).comx = mean(x);
    node(ni).comy = mean(y);
    node(ni).comz = mean(z);
    node(ni).ep = 1;
    node(ni).label = lm(node(ni).idx(1));
    % assign index to node voxels
    skel2(node(ni).idx) = ni+1;
end;
l_idx = 1;
c2n=zeros(w*l*h,1);
c2n(cans(:,1))=1:size(cans,1);
s2n=zeros(w*l*h,1);
s2n(nhi(:,14))=1:size(nhi,1);
% visit all nodes
% i = number of clustered node
% j = number of individual node that belongs to the current cluster
for i=1:length(node)
    % find all canal vox in nb of all node idx
    link_idx = s2n(node(i).idx);
    
    for j=1:length(link_idx)
        % visit all voxels of this node
        
        % all potential unvisited links emanating from this voxel
        link_cands = nhi(link_idx(j),nh(link_idx(j),:)==1);
        
	% short branches that only have an endpoint
        ep_cands = intersect(link_cands,ep);
        link_cands = link_cands(skel2(link_cands)==1);
	link_cands = intersect(link_cands,cans(:,1));
        
        for k=1:length(link_cands)
            [vox,n_idx,ept] = pk_follow_link(skel2,node,i,j,link_cands(k),cans,c2n);
            skel2(vox(2:end-1))=0;
            if((ept && length(vox)>THR) || (~ept && i~=n_idx))
                link(l_idx).n1 = i;
                link(l_idx).n2 = n_idx; % node number
                link(l_idx).point = vox;
                link(l_idx).label = lm(vox(1));
		node(i).links = [node(i).links, l_idx];
                node(i).conn = [int16(node(i).conn), int16(n_idx)];
                node(n_idx).links = [node(n_idx).links, l_idx];
                node(n_idx).conn = [int16(node(n_idx).conn), int16(i)];
                l_idx = l_idx + 1;
            end;
        end;
        if (THR==0) % if short branches allowed
            for k=1:length(ep_cands)
                n_idx = skel2(ep_cands(k))-1;
                if(n_idx && n_idx~=i)
                    skel2(ep_cands(k))=0;
                    link(l_idx).n1 = i;
                    link(l_idx).n2 = n_idx; % node number
                    link(l_idx).point = ep_cands(k);
                    link(l_idx).label = lm(ep_cands(k));
                    node(i).links = [node(i).links, l_idx];
                    node(i).conn = [int16(node(i).conn), int16(n_idx)];
                    node(n_idx).links = [node(n_idx).links, l_idx];
                    node(n_idx).conn = [int16(node(n_idx).conn), int16(i)];
                    l_idx = l_idx + 1;
                end;
            end;
        end;
    end;
        
end;
% mark all 1-nodes as end points
if ~isempty(node)
ep_idx = find(cellfun('length',{node.links})==1);
    for i=1:length(ep_idx)
        node(ep_idx(i)).ep = 1;    
    end;
end
% number of nodes
n_nodes = length(node);
% initialize matrix
A = zeros(n_nodes);
% for all nodes, make according entries into matrix for all its links
for i=1:n_nodes
    idx1=find(node(i).conn>0);
    idx2=find(node(i).links>0);
    idx=intersect(idx1,idx2);
    for j=1:length(idx) % for all its links
        if(i==link(node(i).links(idx(j))).n1) % if we are the starting point
            A(i,link(node(i).links(idx(j))).n2)=length(link(node(i).links(idx(j))).point);
            A(link(node(i).links(idx(j))).n2,i)=length(link(node(i).links(idx(j))).point);
        end;
        if(i==link(node(i).links(idx(j))).n2) % if we are the end point
            A(i,link(node(i).links(idx(j))).n1)=length(link(node(i).links(idx(j))).point);
            A(link(node(i).links(idx(j))).n1,i)=length(link(node(i).links(idx(j))).point);
        end;
    end;
end;
% convert to sparse
A = sparse(A);
% transform all voxel and position indices back to non-padded coordinates
for i=1:length(node)
    [x,y,z] = ind2sub([w,l,h],node(i).idx);
    node(i).idx = sub2ind([w-2,l-2,h-2],x-1,y-1,z-1);
    node(i).comx = node(i).comx - 1;
    node(i).comy = node(i).comy - 1;
    node(i).comz = node(i).comz - 1;
end;
% transform all link voxel indices back to non-padded coordinates
for i=1:length(link)
    [x,y,z] = ind2sub([w,l,h],link(i).point);
    link(i).point = sub2ind([w-2,l-2,h-2],x-1,y-1,z-1);
end;
if isempty(node)
    node = struct('idx',[],'links',[],'conn',[],'comx',[],'comy',[],'comz',[],'ep',[],'label',[]);
end
end
% PK FUNCTIONS
function [vox,n_idx,ep] = pk_follow_link(skel,node,k,j,idx,cans,c2n)
vox = [];
n_idx = [];
ep = 0;
% assign start node to first voxel
vox(1) = node(k).idx(j);
i=1;
isdone = false;
while(~isdone) % while no node reached
    i=i+1; % next voxel
    next_cand = c2n(idx);
        cand = cans(next_cand,2);
        if(cand==vox(i-1)) % switch direction
            cand = cans(next_cand,3);
        end;
        if(skel(cand)>1) % node found
            vox(i) = idx;
            vox(i+1) = cand; % first node
            n_idx = skel(cand)-1; % node #
            if(node(n_idx).ep)
                ep=1;
            end;
            isdone = 1;
        else % next voxel
            vox(i) = idx;
            idx = cand;
        end;
end;
end
function nhood = pk_get_nh_idx(img,i)
width = size(img,1);
height = size(img,2);
depth = size(img,3);
[x,y,z]=ind2sub([width height depth],i);
nhood = zeros(length(i),27);
for xx=1:3
    for yy=1:3
        for zz=1:3
            w=sub2ind([3 3 3],xx,yy,zz);
            nhood(:,w) = sub2ind([width height depth],x+xx-2,y+yy-2,z+zz-2);
        end;
    end;
end;
end
function nhood = pk_get_nh(img,i)
width = size(img,1);
height = size(img,2);
depth = size(img,3);
[x,y,z]=ind2sub([width height depth],i);
nhood = false(length(i),27);
for xx=1:3
    for yy=1:3
        for zz=1:3
            w=sub2ind([3 3 3],xx,yy,zz);
            idx = sub2ind([width height depth],x+xx-2,y+yy-2,z+zz-2);
            nhood(:,w)=img(idx);
        end;
    end;
end;
end