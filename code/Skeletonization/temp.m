classdef OCTAVA_2p0_MSD < matlab.apps.AppBase

    % Properties that correspond to app components
    properties (Access = public)
        OCTAVAUIFigure                  matlab.ui.Figure
        SaveMenu                        matlab.ui.container.Menu
        saveBinaryImageMenu             matlab.ui.container.Menu
        saveSessionDataMenu             matlab.ui.container.Menu
        ClearMenu                       matlab.ui.container.Menu
        ClearsessiondataMenu            matlab.ui.container.Menu
        ClearplotsMenu                  matlab.ui.container.Menu
        HelpMenu                        matlab.ui.container.Menu
        ShowOCTAVAhelpMenu              matlab.ui.container.Menu
        GridLayout                      matlab.ui.container.GridLayout
        savefileLabel_single            matlab.ui.control.Label
        BatchProcessingPanel            matlab.ui.container.Panel
        GridLayout5                     matlab.ui.container.GridLayout
        Abort                           matlab.ui.control.StateButton
        ProgressLabel                   matlab.ui.control.Label
        StartbatchprocessButton         matlab.ui.control.Button
        SavebinaryCheckBox              matlab.ui.control.CheckBox
        FiletypeDropDownLabel           matlab.ui.control.Label
        FiletypeDropDown                matlab.ui.control.DropDown
        bachfileLabel                   matlab.ui.control.Label
        RawdatafolderButton             matlab.ui.control.Button
        MetricsPanel                    matlab.ui.container.Panel
        GridLayout3                     matlab.ui.container.GridLayout
        MeantortuosityLabel             matlab.ui.control.Label
        FractaldimensionLabel           matlab.ui.control.Label
        TotalvessellengthLabel          matlab.ui.control.Label
        BranchpointdensityLabel         matlab.ui.control.Label
        MediandiameterLabel             matlab.ui.control.Label
        MeandiameterLabel               matlab.ui.control.Label
        VessellengthdensityLabel        matlab.ui.control.Label
        VesselareadensityLabel          matlab.ui.control.Label
        RetinalAnalysisPanel            matlab.ui.container.Panel
        GridLayout4                     matlab.ui.container.GridLayout
        RapidFAZButton_2                matlab.ui.control.Button
        TuneFAZsegmentationCheckBox     matlab.ui.control.CheckBox
        RapidFAZStringencyfactorSliderLabel  matlab.ui.control.Label
        RapidFAZStringencyfactorSlider  matlab.ui.control.Slider
        GridLayout6                     matlab.ui.container.GridLayout
        GridType                        matlab.ui.control.DropDown
        MeasureFAZButton                matlab.ui.control.Button
        RegionalanalysisButton          matlab.ui.control.Button
        RL                              matlab.ui.control.DropDown
        RetinaCheckBox                  matlab.ui.control.CheckBox
        binsizeDiams                    matlab.ui.control.Spinner
        BinsizeforhistogramsLabel       matlab.ui.control.Label
        ImagesizemmLabel                matlab.ui.control.Label
        SegmentationmethodDropDownLabel  matlab.ui.control.Label
        RealImageSizemm                 matlab.ui.control.NumericEditField
        binsizeTort                     matlab.ui.control.Spinner
        binsizeLength                   matlab.ui.control.Spinner
        SelectSaveFolderButton_single   matlab.ui.control.Button
        BiomarkersButton                matlab.ui.control.Button
        TwigsizeSpinner                 matlab.ui.control.Spinner
        TwigsizeLabel                   matlab.ui.control.Label
        ATkernelsizeSpinner             matlab.ui.control.Spinner
        ATkernelsizeSpinnerLabel        matlab.ui.control.Label
        sigmamaxSpinner                 matlab.ui.control.Spinner
        FrangiBool                      matlab.ui.control.CheckBox
        kernelSize                      matlab.ui.control.Spinner
        MedfiltCheckBox                 matlab.ui.control.CheckBox
        SegmentationmethodDropDown      matlab.ui.control.DropDown
        ImagesubsetButton               matlab.ui.control.Button
        SkeletonizeButton               matlab.ui.control.Button
        InvertButton                    matlab.ui.control.Button
        BinarizeButton                  matlab.ui.control.Button
        ResizeButton                    matlab.ui.control.Button
        LoadimageButton                 matlab.ui.control.Button
        ReadyLamp                       matlab.ui.control.Lamp
        Label                           matlab.ui.control.Label
        ReadyLabel                      matlab.ui.control.Label
        FileLabel                       matlab.ui.control.Label
        OCTAVALabel                     matlab.ui.control.Label
        TortsAxes                       matlab.ui.control.UIAxes
        LengthsAxes                     matlab.ui.control.UIAxes
        DiamsAxes                       matlab.ui.control.UIAxes
        OverlayImageAxes                matlab.ui.control.UIAxes
        SkelImageAxes                   matlab.ui.control.UIAxes
        BinaryImageAxes                 matlab.ui.control.UIAxes
        inputImageAxes                  matlab.ui.control.UIAxes
        ContextMenu                     matlab.ui.container.ContextMenu
        Menu                            matlab.ui.container.Menu
        Menu2                           matlab.ui.container.Menu
    end

    
    properties (Access = public)
        %This section initialzes global variables
        homedir %Home directory of OCTAVA app
        inputImage % Input image for processing
        fullImSizePix %Keeps track of the size of the full image so that pix/mm isn't changed when subset is collected.
        BinarizationMethod % Selected Binarization Method to use
        BinaryImage % Binarized Image
        bin_overlay %Colormap for image overlays
        FileLabelName %Name of filebeing processed
        SaveDir %Path to results with folders for each image
        SaveFolder %Results folder for the current image
        skelReady %Boolean to say the software is ready to run skeletonization
        metrics %Structural array containing metric
        metrics_cumulative %collects all the metric for each dataset run in a given session
        metrics_counter %Keeps count of number of datasets processed in a session
        lastPath %keeps track of the last folder open when selecting save files
        imgShape %notes if image is square or rectangular for area calculation
        imgSkel %Stores the skelton image for calculation of fractal dimension
        imgOriginal %Stores orignial input image in case image cropping is applied to avoid boundary effects
        datanum %Stores a counter in case an image is run multiple times to avoid overwriting
        FAZ_ctr %Center point of the FAZ [x,y]
        Gnodes %nodes matrix from graph structure
        Glinks %links matrix from graph structure
        FAZ_metrics_cumulative  %For cumulative storing of FAZ metrics
        FAZ_metrics_counter %For keeping track of successive FAZ metrics caluclations
        RawFolder %Location of raw data for batch processing
        MatlabVer %keeps track if you have an older version of matlab
        Ffactor %FAZ scaling factor
        FAZmask %FAZ segmentation
    end
    
    methods (Access = private)
        
        
        function init_session(app)
            %Reinitializes variables for saving session results
            app.metrics_counter = 0;
            app.metrics_cumulative = struct('name','filename','nodes',0,'VAD',0,'totalLength',0,'VLD',0,'MeanLength',0,'MedianLength',0,'varLengths',0,'skewLengths',0,'kurtLengths',0,'MeanDiam',0,'MedianDiam',0,'varDiams',0,'skewDiams',0,'kurtDiams',0,'BD',0,'FD',0,'FDerror',0, 'mTort', 0,'varTort',0,'skewTort',0,'kurtTort',0, 'Frangi_sigma_max',0,'MedFilt_Kernel',0,'Binarization','Method');
            
            if app.RetinaCheckBox.Value
                init_session_retina(app)
            end
        end
        
        function init_session_retina(app)
            app.FAZ_metrics_counter = 0;
            app.FAZ_metrics_cumulative = struct('name', 'filename', 'Area', 0,'Centroid',0,'Circularity',0,'Eccentricity', 0,'MajoraxisLength',0,'MinoraxisLength',0,'Perimeter',0,'acircularity_index',0, 'axis_ratio',0, 'FD_300', 0);
        end
        
        
        
        function loadImage(app, Pathname, Filename)
            
            a = fullfile(Pathname, Filename);
            %Display a file browser for user to select image
            
            %Load the image file
            a = imread(a);
            %Convert to grayscale
            if size(a,3) == 3
                a = rgb2gray(a);
            end
            app.inputImage = double(int16(squeeze(a(:,:,1))));
            
            
            inds = strfind(Filename,'.');
            app.FileLabelName = Filename(1:inds(end)-1);
            app.FileLabelName = erase(app.FileLabelName,'_');
            
            app.lastPath = Pathname;
            
            
            app.fullImSizePix = size(app.inputImage);
            app.imgShape = 'rect'; %Initialize image shape to rectange
            app.imgOriginal = app.inputImage; %Stores originial image to avoid boundary effect of binairaztion on cropped images
            app.FAZ_ctr = app.fullImSizePix/2; %FAZ center should be defaulted to the center of the image
            
            %Make directory for each image
            app.SaveFolder = fullfile(app.SaveDir,app.FileLabelName);
            if ~exist(app.SaveFolder, 'dir')
                mkdir(app.SaveFolder)
            end
            
        end
        
        function binarizeImage(app)
            %Load info
            Method = app.SegmentationmethodDropDown.Value; %Check selected binarization method
            
            
            % Make sure vessels are white and the rest is black
            [y] = max(app.inputImage(2:end,2:end));
            [~,cc] = max(y);
            [~,rr] = max(app.inputImage(2:end,cc));
            
            cc=cc+1;
            rr=rr+1;
            
            %%Apply Median filter if selected
            if app.MedfiltCheckBox.Value
                Im = medfilt2(app.inputImage,[app.kernelSize.Value app.kernelSize.Value]);
            else
                Im = app.inputImage;
            end
            
            % Binarize
            if app.FrangiBool.Value
                opts.sigmarange = [1 app.sigmamaxSpinner.Value];
                opts.sigmastepsize=2;
                opts.correctionconst1=0.8;
                opts.correctionconst2=15;
                Im=frangi_2Dfilter(Im,opts);
            end
            
            if strcmp(Method,'Fuzzy means')
                %Implements Fuzzy thrshold binarization
                %Number of sets;
                nth=2;
                app.BinaryImage=fuzzy_thresholding(Im,nth,3)-1;
                
            elseif strcmp(Method,'Adaptive thresholding')
                %Implements adaptive threshold binarization
                app.BinaryImage= double(adaptivethresholding(Im,app.ATkernelsizeSpinner.Value));
                %Maybe make  the number here edjustable?
            else
                warndlg('Incorrect segmentation method') ;
            end
            
            app.BinaryImage(app.BinaryImage==app.BinaryImage(rr,cc)) = 255;
            app.BinaryImage(app.BinaryImage~=app.BinaryImage(rr,cc)) = 0;
            
            
        end
        
        function [sk2, TifFileName] = skeletonize(app, bin_img, fol, disp)
            
            list = dir(fullfile(fol, '*_Skeleton*.tif'));
            imgnum = length(list);
            
            
            %generate the skeletonized image
            [Nx,~] = size(app.inputImage);
            L = logical(bin_img);
            sk2 = bwmorph(L,'skel',Inf); %skeletonizes
            
            %removes branches smaller than twig size
            sk2 = bwskel(sk2,'MinBranchLength',app.TwigsizeSpinner.Value);
            app.imgSkel = sk2;
            
            if disp == 1
                %Prepare display and save skeleton image
                sk2 = bwmorph(sk2,'thicken');
                fig = figure;
                fig.Visible = 'off';
                figAxes = axes(fig);
                imagesc(app.inputImage*3/4+10, 'Parent', figAxes);
                hold(figAxes,'on');
                axis(figAxes,'equal',[0 Nx 0 Nx])
                colormap(fig,app.bin_overlay)
                imagesc(sk2*255, 'Parent', figAxes, 'AlphaData', .5);
                caxis(figAxes, [0 255])
                figAxes.YDir = 'reverse';
                axis(figAxes,'off')
                fig.Position = fig.Position.*[1 1 5 5];
                TifFileName=fullfile(fol,[ app.FileLabelName  '_Skeleton_' num2str(imgnum) '.tif']);
                export_fig(fig, TifFileName);
                close(fig)
            end
            
            %Local thickness measurement
            D = bwdist(~L)*2; %Distance transform gives euclidean distance to nearest bg pixel
            %D is the closest I can get to the local thickness map so far, so
            %saving as such. Factor of 2 since distance transform gives radius
            if disp == 1
                pngFileName=fullfile(fol,[ app.FileLabelName  '_Local thickness_' num2str(imgnum) '.png']);
                D_output = D./max(max(D))*255;
                imwrite(D_output,hot,pngFileName);
            end
            
            %Network analysis
            %Based on code written by Philip Kollmannsberger
            if sum(sum(app.imgSkel)) == 0
                nodes = [];
                links = [];
            else
                [~,nodes,links] = Skel2Graph3D(app.imgSkel, app.TwigsizeSpinner.Value);
                
                
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
            
            app.Gnodes = nodes;
            app.Glinks = links;
            
            %Add parameters to links structure that are required for
            %calculating metrics
            for i = 1:length(app.Glinks)
                [app.Glinks(i).x, app.Glinks(i).y, ~] = ind2sub([Nx,Nx,1],app.Glinks(i).point); %Adds the x and y coordinates for each point on the link
                d = diff([app.Glinks(i).y', app.Glinks(i).x']);
                app.Glinks(i).pixLength = sum(sqrt(sum(d.*d,2))); %Length of branch in pixels
                app.Glinks(i).end2endLength = sqrt((app.Glinks(i).x(end) - app.Glinks(i).x(1)).^2 + (app.Glinks(i).y(end) - app.Glinks(i).y(1)).^2); %arc length
                app.Glinks(i).tortuosity = app.Glinks(i).pixLength./ app.Glinks(i).end2endLength;
                app.Glinks(i).diameterMeasurements = D(app.Glinks(i).point); %Diameter measurement at each point within the link
                app.Glinks(i).diameter = mean(app.Glinks(i).diameterMeasurements); %Mean diameter for a given link
            end
            
            if disp == 1
                %display result
                %First, display the full graph structure in its own window
                fig = figure;
                fig.Visible = 'off'; %Visible is off because we are just using this to save the data for now
                figAxes = axes(fig);
                imagesc(app.inputImage, 'Parent', figAxes);
                hold(figAxes,'on');
                axis(figAxes,'equal',[0 Nx 0 Nx])
                colormap(fig,'gray')
                caxis(figAxes, [0 255])
                
                for i=1:length(nodes)
                    x1 = nodes(i).comx;
                    y1 = nodes(i).comy;
                    z1 = nodes(i).comz;
                    
                    
                    
                    for j=1:length(nodes(i).links)    % draw all connections of each node
                        if(nodes(nodes(i).conn(j)).ep==1)
                            col='g'; % branches are black
                        else
                            col='y'; % links are red
                        end
                        if(nodes(i).ep==1)
                            col='g';
                        end
                        if(nodes(nodes(i).conn(j)).ep==1) && (nodes(i).ep==1)
                            col = 'b';
                        end
                        
                        
                        %                 % draw edges as lines using voxel positions
                        plot(figAxes,app.Glinks(nodes(i).links(j)).y, app.Glinks(nodes(i).links(j)).x,'Color',col,'LineWidth',2);
                        
                    end
                    
                    if(nodes(i).ep==1)
                        ncol = 'c';
                    else
                        ncol = 'm';
                        % draw all nodes as circles
                        plot3(figAxes,y1,x1,z1,'o','Markersize',4,...
                            'MarkerFaceColor',ncol,...
                            'Color','k');
                    end
                    
                    
                    
                    
                end
                axis image;axis off;
                drawnow;
                fig.Position = fig.Position.*[1 1 5 5];
                
                %Save as tif
                TifFileName=fullfile(fol,[ app.FileLabelName  '_Overlay_' num2str(imgnum) '.tif']);
                export_fig(fig, TifFileName);
                close(fig)
                
            end
            
        end
        
        function generateMetrics(app)
            app.metrics.name = app.FileLabelName;
            [Nx, ~] = size(app.inputImage); %Assuming square images for now - this is typically the case
            pix_to_mm = app.RealImageSizemm.Value/app.fullImSizePix(1);
            
            %Calcuate image area based on the actual image used after cropping
            if strcmp(app.imgShape,'rect')
                imgArea_mm = Nx*Nx*pix_to_mm^2; %This will now be correct for images that are rectangular
                imgArea_pix = Nx*Nx;
            else
                imgArea_mm = pi*(Nx/2)^2*pix_to_mm^2; %This will now be correct for images that are circular
                imgArea_pix = pi*(Nx/2)^2;
            end
            
            
            
            % Calulate metrics
            
            %Vessel area density
            app.metrics.VAD = round(sum(sum(app.BinaryImage))/255/imgArea_pix,2)*100;
            
            %Total length, average length, VLD
            app.metrics.Lengths = [app.Glinks.pixLength]*pix_to_mm; %length of each branch and segment in mm
            app.metrics.totalLength = round(sum(app.metrics.Lengths),2); %In mm
            app.metrics.VLD = round(app.metrics.totalLength*pix_to_mm/imgArea_mm,4)*100; %in percent
            app.metrics.MeanLength = round(mean(app.metrics.Lengths*1000)); %in microns
            app.metrics.MedianLength = round(median(app.metrics.Lengths*1000)); %in microns
            
            %Average diameter
            app.metrics.Diams = [app.Glinks.diameter]*pix_to_mm*1000; %diameter of each branch and segment in microns
            app.metrics.MeanDiam = round(mean(app.metrics.Diams)); %In microns
            app.metrics.MedianDiam = round(median(app.metrics.Diams));
            
            %Branchpoint density
            app.metrics.nodes = sum(~[app.Gnodes.ep]);
            app.metrics.BD =  round(app.metrics.nodes/app.metrics.totalLength,2); %in 1/mm
            
            %Tortuosity
            app.metrics.Tortuosity = [app.Glinks.tortuosity];
            app.metrics.MeanTortuosity = round(mean(app.metrics.Tortuosity(~isinf(app.metrics.Tortuosity))),2);
            
            %Fractal dimension - box counting method
            img = logical(imcomplement(app.imgSkel));
            Nx = max(size(img));
            numIterations = ceil(log10(Nx)/log10(2));
            width = 2^numIterations;
            %pad img with zeros so that it is square with lengths = to a power of 2
            temp = zeros(width,width);
            temp(1:size(img,1), 1:size(img,2)) = img;
            img = temp;
            clear temp
            n_r = zeros(1,numIterations+1); %Initialize variable for counts
            
            %Perform box counting
            n_r(numIterations+1) = sum(sum(img));
            
            for ii = (numIterations-1):-1:0
                boxSize = 2^(numIterations-ii);
                boxRad = round(boxSize/2);
                
                for jj = 1:boxSize:(width-boxSize+1)
                    for kk = 1:boxSize:(width-boxSize+1)
                        img(jj,kk) = ( img(jj,kk) || img(jj+boxRad,kk) || img(jj,kk+boxRad) || img(jj+boxRad,kk+boxRad) );
                    end
                end
                
                n_r(ii+1) = sum(sum(img(1:boxSize:(width-boxSize+1),1:boxSize:(width-boxSize+1))));
            end
            
            n_r = n_r(end:-1:1);
            r = 2.^(0:numIterations);
            slope = -gradient(log10(n_r))./gradient(log10(r));
            app.metrics.FD = round(mean(slope),2);
            app.metrics.FDerror = round(std(slope),2);
            
            
            %Additional metrics to describe distribution of metircs,
            %legnths, and tortuosity: variance, kurtosis, skewness
            
            app.metrics.varDiams = round(var(app.metrics.Diams));
            app.metrics.skewDiams = round(skewness(app.metrics.Diams),2);
            app.metrics.kurtDiams = round(kurtosis(app.metrics.Diams),2);
            
            app.metrics.varLengths = round(var(app.metrics.Lengths*1000));
            app.metrics.skewLengths = round(skewness(app.metrics.Lengths*1000),2);
            app.metrics.kurtLengths = round(kurtosis(app.metrics.Lengths*1000),2);
            
            app.metrics.varTort = round(var(app.metrics.Tortuosity(~isinf(app.metrics.Tortuosity))),3);
            app.metrics.skewTort = round(skewness(app.metrics.Tortuosity(~isinf(app.metrics.Tortuosity))),2);
            app.metrics.kurtTort = round(kurtosis(app.metrics.Tortuosity(~isinf(app.metrics.Tortuosity))));
            
            
            %Add to cumulative thing for saving session
            app.metrics_counter = app.metrics_counter+1;
            app.metrics_cumulative(app.metrics_counter).name = app.metrics.name;
            app.metrics_cumulative(app.metrics_counter).nodes = app.metrics.nodes;
            app.metrics_cumulative(app.metrics_counter).VAD = app.metrics.VAD;
            app.metrics_cumulative(app.metrics_counter).totalLength = app.metrics.totalLength;
            app.metrics_cumulative(app.metrics_counter).VLD = app.metrics.VLD;
            app.metrics_cumulative(app.metrics_counter).MeanLength = app.metrics.MeanLength;
            app.metrics_cumulative(app.metrics_counter).MedianLength = app.metrics.MedianLength;
            app.metrics_cumulative(app.metrics_counter).MeanDiam = app.metrics.MeanDiam;
            app.metrics_cumulative(app.metrics_counter).MedianDiam = app.metrics.MedianDiam;
            app.metrics_cumulative(app.metrics_counter).BD = app.metrics.BD;
            app.metrics_cumulative(app.metrics_counter).FD = app.metrics.FD;
            app.metrics_cumulative(app.metrics_counter).FDerror = app.metrics.FDerror;
            app.metrics_cumulative(app.metrics_counter).mTort = app.metrics.MeanTortuosity;
            app.metrics_cumulative(app.metrics_counter).varDiams = app.metrics.varDiams;
            app.metrics_cumulative(app.metrics_counter).skewDiams = app.metrics.skewDiams;
            app.metrics_cumulative(app.metrics_counter).kurtDiams = app.metrics.kurtDiams;
            app.metrics_cumulative(app.metrics_counter).varLengths = app.metrics.varLengths;
            app.metrics_cumulative(app.metrics_counter).skewLengths = app.metrics.skewLengths;
            app.metrics_cumulative(app.metrics_counter).kurtLengths = app.metrics.kurtLengths;
            app.metrics_cumulative(app.metrics_counter).varTort = app.metrics.varTort;
            app.metrics_cumulative(app.metrics_counter).skewTort = app.metrics.skewTort;
            app.metrics_cumulative(app.metrics_counter).kurtTort = app.metrics.kurtTort;
            
            if app.FrangiBool.Value
                app.metrics_cumulative(app.metrics_counter).Frangi_sigma_max = app.sigmamaxSpinner.Value;
            else
                app.metrics_cumulative(app.metrics_counter).Frangi_sigma_max = 0;
            end
            if app.MedfiltCheckBox.Value
                app.metrics_cumulative(app.metrics_counter).MedFilt_Kernel = app.kernelSize.Value;
            else
                app.metrics_cumulative(app.metrics_counter).MedFilt_Kernel = 0;
            end
            app.metrics_cumulative(app.metrics_counter).Binarization = app.SegmentationmethodDropDown.Value;
            
            
            %Save to excell file for that dataset
            
            datatable = struct2table(app.metrics_cumulative(app.metrics_counter));
            ExcelFilename = fullfile(app.SaveFolder, [app.FileLabelName '_' app.datanum' '.xlsx']);
            writetable(datatable,ExcelFilename, 'Sheet', 'General metrics');
            
            writematrix(app.metrics.Diams,ExcelFilename, 'Sheet', 'Diameters');
            writematrix(app.metrics.Lengths,ExcelFilename, 'Sheet', 'Lengths');
            writematrix(app.metrics.Tortuosity,ExcelFilename, 'Sheet', 'Tortuosities');
            
            
            
        end
        
        function FAZAnalysis(app)
            I = app.BinaryImage;
            
            %pull faz outline to send to measure faz
            %dilate to initialize
            %erode for stop condition
            fmask = app.FAZmask;
            [fr,fc] = size(fmask);
            dfactor = ceil(mean(fr,fc)*0.15);
            chv_init = imdilate(fmask,offsetstrel('ball',dfactor,dfactor));
            chv_init = chv_init > mode(chv_init);
            %chv_stop = imerode(fmask,offsetstrel('ball',dfactor,dfactor));
            %chv_stop = chv_stop > mode(chv_stop);
            chv_stop=fmask;
            chv_stop_area = sum(sum(chv_stop));
            
            
            %Setup figure window with UI controls
            
            fid = uifigure('Name','find FAZ','NumberTitle','off',"Color",[0.55,0.75,0.88]);
            imaxs = uiaxes("Parent",fid,'Position',[120,20,400,400]);
            
            my = 20;
            lambda1 = 5;
            lambda2 = 1;
            stopping = false;
            
            imshow(I,"Parent",imaxs);
            stopbutton = uibutton(fid,"push",'Text','Stop','Position',[30 35 60 20]);
            stopbutton.ButtonPushedFcn = {@(src,evnt)stopButtonPushed};
            
            %Check value of AutoFAZ - if true, start with automatically
            %generated circle. Otherwise, let user select starting points.
            
            if app.TuneFAZsegmentationCheckBox.Value
                
                chv_init_pts = bwboundaries(chv_init);
                chv_init_pts = chv_init_pts{1};
                chv_stop_pts = bwboundaries(chv_stop);
                chv_stop_pts = chv_stop_pts{1};
                size(chv_init_pts)
                x1 = chv_init_pts(:,2);
                y1 = chv_init_pts(:,1);
                %x2 = chv_stop_pts(:,2);
                %y2 = chv_stop_pts(:,1);
                
                %figure(3);
                %title('Active Contour Initialization and Hard Stop')
                %imshow(app.BinaryImage); hold on;
                %plot(x1,y1,'g','LineWidth',2);
                %plot(x2,y2,'r','LineWidth',2);
                
                % the levelset function
                [x,y] = meshgrid(1:size(I,2),1:size(I,1));
                m = inpolygon(x,y,x1,y1);
                phi = bwdist(1-m)-bwdist(m)-m;
                
                % get the initial contour
                hold(imaxs, "on")
                %title('Initial contour');
                contour(phi, [0 0], 'r', 'LineWidth',2,"Parent",imaxs);
                drawnow;
                hold(imaxs, "off")
                
                
                %Apply iterations to optimize contour
                dt = 1;
                a_check = fr*fc;
                
                for i=1:1000 %Change to while loop so it looks for convergence?
                    %This works, but it takes a long time - alternative to
                    %add a "stop" button when convergence is reached
                    %get the c- and c+
                    heavi = heaviside(phi);
                    cp = sum(sum(heavi.*I))/length(find(phi>=0)); %inside mean gray level
                    cm = sum(sum((1-heavi).*I))/length(find(phi<0)); %outside mean gray level
                    % Curvature
                    kappa = curvature(phi);
                    
                    % Iterative step
                    phi_t = diracdelta(phi).*(my*kappa - lambda1*(I-cp).^2 + lambda2*(I-cm).^2);
                    phi = phi + dt.*(phi_t./(max(max(abs(phi_t)))));
                    
                    phi = reinitialization(phi, 0.5);
                    
                    if length(find(phi>=0)) < 0.75*chv_stop_area
                        FAZ_Mask=chv_stop;
                        break;
                    end
                    
                    % Print contour
                    if(mod(i-1,10) == 0)
                        imshow(app.BinaryImage,"Parent",imaxs);
                        hold(imaxs, "on")
                        contour(phi, [0 0], 'r', 'LineWidth',2,"Parent",imaxs);
                        imaxs.Title.String = [ num2str(i) ' iterations'];
                        drawnow;
                        hold(imaxs,"off")
                        % check if area n*10th iteraion is less than
                        % (n-1)*10th; if not --> stop active contour
                        
                        if length(find(phi>=0)) < a_check
                            FAZ_Mask=zeros(1,1);
                            a_check=length(find(phi>=0));
                        else
                            FAZ_Mask=chv_stop;
                            break;
                        end
                        
                        %xlabel('The iteration can be stopped by pressing the OK button')
                    end
                    % Reinitialize the level set equation phi
                    
                    if stopping
                        break
                    end
                    
                end
                
                imshow(imcomplement(I),"Parent",imaxs);
                hold(imaxs,'on');
                imaxs.Title.String = ['Finally contour on original image after ' num2str(i) ' iterations'];
                [c,h]=contour(phi, [0 0], 'y', 'LineWidth',2,"Parent",imaxs,"Visible","off"); drawnow; %hold off;
                %To remove the small circles
                [s,index]=get_lines(c);
                %s(index).x,s(index).y are the co
                plot(s(index).x,s(index).y,'r','LineWidth',2,"Parent",imaxs);
                %get the center of the avascular zone
                [Cx,Cy]=get_central(s(index).x,s(index).y);
                plot(Cx,Cy,'r*',"Parent",imaxs);
                drawnow
                
                % Calculate foveal FAZ
                %calculate position vectors for points relative to centroid
                app.FAZ_ctr = [Cx,Cy];
                cnt = s(index);
                mask1 = poly2mask(cnt.x,cnt.y,app.fullImSizePix(1),app.fullImSizePix(2));
                
                cnt.x = cnt.x-Cx;
                cnt.y = cnt.y-Cy;
                %convert to polar coordinates
                [cnt.theta, cnt.rho] = cart2pol(cnt.x,cnt.y);
                %Increase length of vectors by 300 microns
                radSize = .3*app.fullImSizePix(1)/app.RealImageSizemm.Value;
                cnt.rho = cnt.rho+radSize;
                %Convert back to cartesian
                [cnt.x, cnt.y] = pol2cart(cnt.theta, cnt.rho);
                cnt.x = cnt.x+Cx;
                cnt.y = cnt.y+Cy;
                %Generate mask based on 2 contours - sets everything to NaN and only keeps the data between the two rings
                mask1 = poly2mask(cnt.x,cnt.y,app.fullImSizePix(1),app.fullImSizePix(2))-mask1;
                mask1(mask1==0) = nan;
                nPix = nansum(nansum(mask1));
                %Apply mask to binary image
                maskBin = mask1.*app.BinaryImage;
                FD_300 = nansum(nansum(maskBin))/255/nPix*100;
                
                %Save figure so contour can be checked later
                fol = fullfile(app.SaveFolder,'images');
                if ~exist(fol, 'dir')
                    mkdir(fol)
                    imgnum = 0;
                else
                    list = dir(fullfile(fol, '*FAZ_Countour*.png'));
                    imgnum = length(list);
                end
                
                savename = fullfile(fol,['FAZ_Countour_' num2str(imgnum) '.png']);
                fid2 = figure;
                set(fid2,'Visible','off')
                imshow(imcomplement(I))
                title(['Finally contour on original image after ' num2str(i) ' iterations']);
                hold on
                contour(phi, [0 0], 'y', 'LineWidth',2,"Visible","off");
                plot(s(index).x,s(index).y,'r','LineWidth',2);
                plot(Cx,Cy,'r*');
                plot(cnt.x, cnt.y,'y','LineWidth',2)
                drawnow;
                saveas(fid2, savename,'png');
                
                %Second method using binarization
                [ca,cb]=size(FAZ_Mask);
                if ca==1
                    FAZ_Mask = poly2mask(s(index).x,s(index).y,size(I,1),size(I,2));      
                else  
                    FAZ_Mask=app.FAZmask;
                    FD_300=0; %FIX THIS???  
                end
            end
            FAZ_stats = regionprops(FAZ_Mask,'Area','Centroid','Circularity','Eccentricity', 'MajoraxisLength','MinoraxisLength','Perimeter');
            FAZ_stats.acircularity_index = FAZ_stats.Perimeter/(2*pi*sqrt(FAZ_stats.Area/pi));
            FAZ_stats.axis_ratio = FAZ_stats.MajorAxisLength/FAZ_stats.MinorAxisLength;
            FAZ_stats.FD_300 = round(FD_300,1);
            FAZ_stats.name = app.FileLabelName;
            
            %Convert from pixels to mm
            pix_to_mm = app.RealImageSizemm.Value/app.fullImSizePix(1);
            FAZ_stats.Area = round(FAZ_stats.Area*pix_to_mm^2,3); %In mm^2
            FAZ_stats.Centroid = round(FAZ_stats.Centroid*pix_to_mm,3); %in mm
            FAZ_stats.MajorAxisLength = round(FAZ_stats.MajorAxisLength*pix_to_mm,3); %in mm
            FAZ_stats.MinorAxisLength = round(FAZ_stats.MinorAxisLength*pix_to_mm,3); %in mm
            FAZ_stats.Perimeter = round(FAZ_stats.Perimeter * pix_to_mm,3); %in mm
            
            %Eccentricity, circularity, acircularity index, axis ratio
            %are unitless but should still be rounded
            FAZ_stats.Eccentricity = round(FAZ_stats.Eccentricity,2);
            FAZ_stats.Circularity = round(FAZ_stats.Circularity,2);
            FAZ_stats.acircularity_index = round(FAZ_stats.acircularity_index,2);
            FAZ_stats.axis_ratio = round(FAZ_stats.axis_ratio,2);
            
            
            %Save Excel file with results summary
            datatable = struct2table(FAZ_stats);
            ExcelFilename = fullfile(app.SaveFolder, [app.FileLabelName '_' app.datanum' '.xlsx']);
            writetable(datatable,ExcelFilename, 'Sheet', 'FAZ metrics');
            close(fid)
            
            
            %Add data to saved session
            app.FAZ_metrics_counter = 1; %app.FAZ_metrics_counter+1;
            app.FAZ_metrics_cumulative(app.FAZ_metrics_counter).name = app.FileLabelName;
            app.FAZ_metrics_cumulative(app.FAZ_metrics_counter).Area = FAZ_stats.Area;
            app.FAZ_metrics_cumulative(app.FAZ_metrics_counter).Centroid = FAZ_stats.Centroid;
            app.FAZ_metrics_cumulative(app.FAZ_metrics_counter).Circularity = FAZ_stats.Circularity;
            app.FAZ_metrics_cumulative(app.FAZ_metrics_counter).Eccentricity = FAZ_stats.Eccentricity;
            app.FAZ_metrics_cumulative(app.FAZ_metrics_counter).MajoraxisLength = FAZ_stats.MajorAxisLength;
            app.FAZ_metrics_cumulative(app.FAZ_metrics_counter).MinoraxisLength = FAZ_stats.MinorAxisLength;
            app.FAZ_metrics_cumulative(app.FAZ_metrics_counter).Perimeter = FAZ_stats.Perimeter;
            app.FAZ_metrics_cumulative(app.FAZ_metrics_counter).acircularity_index = FAZ_stats.acircularity_index;
            app.FAZ_metrics_cumulative(app.FAZ_metrics_counter).axis_ratio = FAZ_stats.axis_ratio;
            app.FAZ_metrics_cumulative(app.FAZ_metrics_counter).FD_300 = FAZ_stats.FD_300;
            
            
            function Y = heaviside(X)
                epsilon = 0.3;
                Y=1/2*(1+2/pi*atan(X/epsilon));
            end
            
            function d = diracdelta(X)
                epsilon = 0.3;
                d = (pi*(epsilon^2+X.^2)).\epsilon;
            end
            
            function stopButtonPushed()
                stopping = true;
            end
        end
        
        function regionalAnalysis(app)
            pix_to_mm = app.RealImageSizemm.Value/app.fullImSizePix(1);
            %Make a folder for storing the regional analysis results
            
            fol = fullfile(app.SaveFolder);
            
            
            %Initialize a new structure array for the regional analysis
            %metrics
            
            grid_type = app.GridType.Value;
            
            if strcmp(grid_type,'Square grid')
                regionsize = floor(app.fullImSizePix./3);
                
                binaryReg{1} = app.BinaryImage(1:regionsize(1),1:regionsize(2));
                binaryReg{2}  = app.BinaryImage(1:regionsize(1),regionsize(2)+1:2*regionsize(2));
                binaryReg{3} = app.BinaryImage(1:regionsize(1),2*regionsize(2)+1:3*regionsize(2));
                binaryReg{4} = app.BinaryImage(regionsize(1)+1:2*regionsize(1),1:regionsize(2));
                binaryReg{5}  = app.BinaryImage(regionsize(1)+1:2*regionsize(1),regionsize(2)+1:2*regionsize(2));
                binaryReg{6} = app.BinaryImage(regionsize(1)+1:2*regionsize(1),2*regionsize(2)+1:3*regionsize(2));
                binaryReg{7}  = app.BinaryImage(2*regionsize(1)+1:3*regionsize(1),1:regionsize(2));
                binaryReg{8} = app.BinaryImage(2*regionsize(1)+1:3*regionsize(1),regionsize(2)+1:2*regionsize(2));
                binaryReg{9}  = app.BinaryImage(2*regionsize(1)+1:3*regionsize(1),2*regionsize(2)+1:3*regionsize(2));
                
                %Prepare for metric generation
                imgArea_pix = regionsize(1)*regionsize(2);
                imgArea_mm = imgArea_pix*pix_to_mm^2;
                
                
                if strcmp(app.RL.Value,'Right Eye')
                    RAlabels = ["Supero-nasal" "Superior" "Supero-temporal" "Nasal" "Central" "Supero-temporal" "Infero-nasal" "Inferior" "Infero-temporal"];
                else
                    RAlabels = ["Supero-temporal" "Superior" "Supero-nasal" "Temporal" "Central" "Supero-Nasal" "Infero-temporal" "Inferior" "Infero-nasal"];
                end
                
            else
                %Calculate each ring radius in pixels
                rad_1mm = .5*app.fullImSizePix(1)/app.RealImageSizemm.Value;
                rad_3mm = 1.5*app.fullImSizePix(1)/app.RealImageSizemm.Value;
                
                fig = figure;
                image(app.inputImage)
                fig.Visible = 'off';
                colormap gray
                axis equal
                xlim([0 app.fullImSizePix(1)])
                ylim([0 app.fullImSizePix(2)])
                hold on
                if isempty(app.FAZ_ctr)
                    app.FAZ_ctr = app.fullImSizePix/2;
                end
                
                roi_1mm = images.roi.Circle(gca,"Center",app.FAZ_ctr,"Radius",rad_1mm,"LineWidth",2,"Color",'y');
                roi_3mm = images.roi.Circle(gca,"Center",app.FAZ_ctr,"Radius",rad_3mm,"LineWidth",2,"Color",'y');
                
                foveal_mask = roi_1mm.createMask;
                parafoveal_mask = roi_3mm.createMask-roi_1mm.createMask;
                
                %Create a mask for each segment - start with assumption
                %of OS (right eye?) and swap labels after if needed...
                
                sector_masks = zeros(app.fullImSizePix(1), app.fullImSizePix(2), 6);
                
                for ii = 1:6
                    theta = linspace(0, -60, 1000)-60*(ii-1);
                    x_sector = [app.FAZ_ctr(1) rad_3mm*cosd(theta)+app.FAZ_ctr(1) app.FAZ_ctr(1)];
                    y_sector = [app.FAZ_ctr(2) rad_3mm*sind(theta)+app.FAZ_ctr(2) app.FAZ_ctr(2)];
                    plot(x_sector,y_sector,'LineWidth',2,"Color",'r')
                    mask = poly2mask(x_sector, y_sector,app.fullImSizePix(1),app.fullImSizePix(2));
                    sector_masks(:,:,ii) = (mask-foveal_mask) > 0;
                end
                drawnow
                close(fig)
                
                binaryReg{1} = app.BinaryImage.*foveal_mask; %foveal circle
                binaryReg{1} = binaryReg{1}(max(app.FAZ_ctr(1)-rad_3mm,1):min(app.FAZ_ctr(1)+rad_3mm,app.fullImSizePix(1)), max(app.FAZ_ctr(2)-rad_3mm,1):min(app.FAZ_ctr(2)+rad_3mm,app.fullImSizePix(2)));
                binaryReg{2} = app.BinaryImage.*parafoveal_mask; %Parafoveal rim
                binaryReg{3} = app.BinaryImage.*(sector_masks(:,:,1)+sector_masks(:,:,2)+sector_masks(:,:,3)); %superior hemi-parafoveal rim
                binaryReg{3} = binaryReg{3}(1:app.fullImSizePix(1)/2,:);
                binaryReg{4} = app.BinaryImage.*(sector_masks(:,:,4)+sector_masks(:,:,5)+sector_masks(:,:,6)); %inferior hemi-parafoveal rim
                binaryReg{4} = binaryReg{4}(app.fullImSizePix(1)/2+1:end,:);
                binaryReg{5} = app.BinaryImage.*(sector_masks(:,:,1)+sector_masks(:,:,6)); %tempo/nasal parafoveal rim
                binaryReg{5} = binaryReg{5}(:,app.fullImSizePix(1)/2+1:end);
                binaryReg{6} = app.BinaryImage.*(sector_masks(:,:,3)+sector_masks(:,:,4));%tempo/nasal parafoveal rim
                binaryReg{6} = binaryReg{6}(:,1:app.fullImSizePix(1)/2);
                binaryReg{7} = app.BinaryImage.*sector_masks(:,:,2); %superior-parafoveal rim
                binaryReg{7} = binaryReg{7}(1:app.fullImSizePix(1)/2,:);
                binaryReg{8} = app.BinaryImage.*sector_masks(:,:,5); %inferior-parafoveal rim
                binaryReg{8} = binaryReg{8}(app.fullImSizePix(1)/2+1:end,:);
                
                if strcmp(app.RL.Value,'Right Eye')
                    RAlabels = ["Foveal circle" "Parafoveal rim " "Superior hemi-parafoveal rim" "Inferior hemi-parafoveal rim" "Tempo parafoveal rim" "Nasal parafoveal rim" "Superior parafoveal rim" "Inferior parafoveal rim"];
                else
                    RAlabels = ["Foveal circle" "Parafoveal rim " "Superior hemi-parafoveal rim" "Inferior hemi-parafoveal rim" "Nasal parafoveal rim" "Tempo parafoveal rim" "Superior parafoveal rim" "Inferior parafoveal rim"];
                end
                
                imgArea_pix_vec = [sum(sum(foveal_mask)) sum(sum(parafoveal_mask)) sum(sum(sector_masks(:,:,1)+sector_masks(:,:,2)+sector_masks(:,:,3)))...
                    sum(sum(sector_masks(:,:,4)+sector_masks(:,:,5)+sector_masks(:,:,6))) sum(sum(sector_masks(:,:,1)+sector_masks(:,:,6))) sum(sum(sector_masks(:,:,3)+sector_masks(:,:,4)))...
                    sum(sum(sector_masks(:,:,2))) sum(sum(sector_masks(:,:,2)))];
            end
            
            %Run metrics generation for each of the regions seperately
            for i = 1:size(binaryReg,2)
                skeletonize(app, binaryReg{i}, fol, 0);
                
                if ~strcmp(grid_type,'Square grid')
                    imgArea_pix = imgArea_pix_vec(i);
                    imgArea_mm = imgArea_pix *pix_to_mm^2;
                end
                regionalmetrics(i).Region = RAlabels(i);
                regionalmetrics(i).VAD = round(sum(sum(binaryReg{i}))/255/imgArea_pix,2)*100;
                
                if ~isempty(app.Glinks)
                    regionalmetrics(i).nodes = sum(~[app.Gnodes.ep]);
                    regionalmetrics(i).totalLength = round(sum([app.Glinks.pixLength]*pix_to_mm),2); %In mm
                    regionalmetrics(i).VLD = round(regionalmetrics(i).totalLength*pix_to_mm/imgArea_mm,4)*100; %in percent
                    regionalmetrics(i).MeanLength = round(mean([app.Glinks.pixLength]*pix_to_mm*1000)); %in microns
                    regionalmetrics(i).MedianLength = round(median([app.Glinks.pixLength]*pix_to_mm*1000)); %in microns
                    regionalmetrics(i).MeanDiam = round(mean([app.Glinks.diameter]*pix_to_mm*1000)); %In microns
                    regionalmetrics(i).MedianDiam = round(median([app.Glinks.diameter]*pix_to_mm*1000));
                    regionalmetrics(i).BD = round(regionalmetrics(i).nodes./regionalmetrics(i).totalLength,2); %in 1/mm
                    tortuosity = [app.Glinks.tortuosity];
                    regionalmetrics(i).mTort = round(mean(tortuosity(~isinf(tortuosity))),2);
                else
                    regionalmetrics(i).nodes = 0;
                    regionalmetrics(i).totalLength = 0;
                    regionalmetrics(i).VLD = 0;
                    regionalmetrics(i).MeanLength = 0;
                    regionalmetrics(i).MedianLength = 0;
                    regionalmetrics(i).MeanDiam = 0;
                    regionalmetrics(i).MedianDiam = 0;
                    regionalmetrics(i).BD = 0;
                    regionalmetrics(i).mTort = 0;
                end
            end
            
            %Save Excel file with results summary
            datatable = struct2table(regionalmetrics);
            ExcelFilename = fullfile(app.SaveFolder, [app.FileLabelName '_' app.datanum' '.xlsx']);
            writetable(datatable,ExcelFilename, 'Sheet', ['Regional analysis_' grid_type]);
            
        end
    end
    

    % Callbacks that handle component events
    methods (Access = private)

        % Code that executes after component creation
        function startupFcn(app)
            warning('off')  %Suppresses warning output
            app.MatlabVer = verLessThan('matlab', 'R2022a');
            %Establish path to app for loading dependency files
            appdir = mfilename('fullpath');
            inds = strfind(appdir,'\')';
            
            if isempty(inds)
                %This should help with mac compatability
                inds = strfind(appdir,'/')';
            end
            app.homedir = appdir(1:inds(end));
            app.lastPath = app.homedir;
            
            %load dpendency stripts
            scriptPath = fullfile(app.homedir,'Scripts');
            addpath(genpath(scriptPath));
            load 'bin overlay colormaps.mat' bin_overylay
            app.bin_overlay = bin_overylay;
            
            %Initialize save path to home directory
            app.SaveDir = app.homedir;
            app.savefileLabel_single.Text = app.SaveDir;
            
            %Initialize dataset counter and setup to record all metrics
            %from session
            init_session(app)
            
            %Initialize variables for seting checks
            app.skelReady = 0;
            
            
            warning('on')
        end

        % Button pushed function: LoadimageButton
        function LoadimageButtonPushed(app, event)
            app.ReadyLabel.Text = 'Wait';
            app.ReadyLamp.Color = [1.00,0.00,0.00];
            drawnow
            
            [Filename, Pathname] = uigetfile(fullfile(app.lastPath,'*.*'), 'Select MIP');
            
            if Filename == 0
                warndlg('You did not choose an image file') ;
                app.inputImage = [];
            else
                
                loadImage(app,Pathname, Filename)
            end
            
            app.datanum = '0'; %Initialize value
            
            
            %Display input image on front panel
            imshow( app.inputImage, 'Parent', app.inputImageAxes);
            caxis(app.inputImageAxes, [0 255]);
            app.FileLabel.Text = app.FileLabelName;
            
            
            app.inputImageAxes.Colormap = gray;
            app.ReadyLabel.Text = 'Ready';
            app.ReadyLamp.Color = [0.00,1.00,0.00];
        end

        % Button pushed function: BinarizeButton
        function BinarizeButtonPushed(app, event)
            if isempty(app.inputImage)
                warndlg('You did not choose an image file') ;
                cla(app.BinaryImageAxes);
            else
                app.ReadyLabel.Text = 'Wait';
                app.ReadyLamp.Color = [1.00,0.00,0.00];
                drawnow
                %Run binarization function
                binarizeImage(app);
                
                %Display on front panel binary mask overlaid on original
                %image
                
                imshow( app.inputImage*3/4+10, 'Parent', app.BinaryImageAxes);
                hold(app.BinaryImageAxes,'on');
                
                t = app.BinaryImage;
                t(t==0) = nan;
                imagesc(t, 'Parent', app.BinaryImageAxes, 'AlphaData', .5*~isnan(t));
                
                app.BinaryImageAxes.Colormap = app.bin_overlay;
                caxis(app.BinaryImageAxes, [0 255]);
                hold(app.BinaryImageAxes,'off');
                
                app.datanum = datestr(datetime);
                app.datanum = erase(app.datanum,':')';
                
                app.ReadyLabel.Text = 'Ready';
                app.ReadyLamp.Color = [0.00,1.00,0.00];
                app.skelReady = 1;
            end
        end

        % Button pushed function: InvertButton
        function InvertButtonPushed(app, event)
            %Inverts the colormap of the binary mask
            app.BinaryImage(app.BinaryImage == 0) = 1;
            app.BinaryImage(app.BinaryImage == 255) = 0;
            app.BinaryImage(app.BinaryImage == 1) = 255;
            
            
            imshow( app.inputImage*3/4+10, 'Parent', app.BinaryImageAxes);
            hold(app.BinaryImageAxes,'on');
            
            t = app.BinaryImage;
            t(t==0) = nan;
            imagesc(t, 'Parent', app.BinaryImageAxes, 'AlphaData', .5*~isnan(t));
            
            app.BinaryImageAxes.Colormap = app.bin_overlay;
            caxis(app.BinaryImageAxes, [0 255]);
            hold(app.BinaryImageAxes,'off');
            
        end

        % Button pushed function: SkeletonizeButton
        function SkeletonizeButtonPushed(app, event)
            if ~app.skelReady
                if isempty(app.inputImage)
                    warndlg('You did not choose an image file') ;
                else
                    warndlg('Binary mask required for skeletonization') ;
                end
            else
                app.ReadyLabel.Text = 'Wait'; %sets wait label
                app.ReadyLamp.Color = [1,0,0];
                drawnow
                
                %Setup folder for saving results.
                fol = fullfile(app.SaveFolder,'images');
                if ~exist(fol, 'dir')
                    mkdir(fol)
                end
                
                
                
                [sk2, ovrlyFileName] = skeletonize(app, app.BinaryImage, fol, 1);
                
                %display skeleton overlaid on original image on front panel
                imshow( app.inputImage*3/4+10, 'Parent', app.SkelImageAxes);
                hold(app.SkelImageAxes,'on');
                app.SkelImageAxes.Colormap = app.bin_overlay;
                caxis(app.SkelImageAxes, [0 255]);
                imagesc(sk2*255, 'Parent', app.SkelImageAxes, 'AlphaData', .5);
                hold(app.SkelImageAxes,'off');
                
                
                %Load tif of overlay image and display in front panel
                %This is done to help save memeory
                ovrly = imread(ovrlyFileName);
                imshow(ovrly, 'Parent', app.OverlayImageAxes);
                
                
                app.ReadyLabel.Text = 'Ready';
                app.ReadyLamp.Color = [0 1 0];
                drawnow
                app.skelReady = 3;
                
                
            end
        end

        % Button pushed function: BiomarkersButton
        function BiomarkersButtonPushed(app, event)
            if app.skelReady ~= 3
                warndlg('Vessel Analysis results not yet available') ;
            else
                app.ReadyLabel.Text = 'Wait';
                app.ReadyLamp.Color = [1.00,0.00,0.00];
                drawnow
                
                
                generateMetrics(app)
                
                
                %Display results in window on front panel - caluclulated metrics
                app.VesselareadensityLabel.Text = ['Vessel area density = ' num2str(app.metrics.VAD) '%'];
                app.VessellengthdensityLabel.Text = ['Vessel length density = ' num2str(app.metrics.VLD) '%'];
                app.TotalvessellengthLabel.Text = ['Total vessel length = ' num2str(app.metrics.totalLength) ' mm'];
                app.MeandiameterLabel.Text = ['Mean diameter = ' num2str(app.metrics.MeanDiam) ' ' char(181) 'm'];
                app.MediandiameterLabel.Text = ['Median diameter = ' num2str(app.metrics.MedianDiam) ' ' char(181) 'm'];
                app.BranchpointdensityLabel.Text = ['Branchpoint density = ' num2str(app.metrics.BD) ' (1/mm)'];
                app.FractaldimensionLabel.Text = ['Fractal dimension = ' num2str(app.metrics.FD) ' +/- ' num2str(app.metrics.FDerror)];
                app.MeantortuosityLabel.Text = ['Mean tortuosity = ' num2str(app.metrics.MeanTortuosity)];
                
                %Histograms
                histogram(app.metrics.Diams,'BinWidth',app.binsizeDiams.Value,'Parent',app.DiamsAxes);
                histogram(app.metrics.Tortuosity,'BinWidth',app.binsizeTort.Value,'Parent', app.TortsAxes);
                histogram(app.metrics.Lengths,'BinWidth',app.binsizeLength.Value,'Parent', app.LengthsAxes);
                app.TortsAxes.XLim = [1 max(app.metrics.Tortuosity)];
                
                
                app.ReadyLabel.Text = 'Ready';
                app.ReadyLamp.Color = [0.00,1.00,0.00];
            end
        end

        % Button pushed function: ResizeButton
        function ResizeButtonPushed(app, event)
            if isempty(app.inputImage)
                warndlg('You did not choose an image file') ;
            else
                app.ReadyLabel.Text = 'Wait';
                app.ReadyLamp.Color = [1.00,0.00,0.00];
                prompt = {'x pixels:', 'y pixels'};
                dlgtitle = 'New image size';
                [Ny,Nx] = size(app.inputImage);
                definput = {num2str(Nx), num2str(Ny)};
                newsize = inputdlg(prompt,dlgtitle,[1 35],definput);
                if ~isempty(newsize)
                    app.inputImage = imresize(app.inputImage,[str2double(newsize{2}), str2double(newsize{1})]);
                    imagesc( app.inputImage, 'Parent', app.inputImageAxes);
                end
                app.fullImSizePix = size(app.inputImage); %Changing the size changes the pix/mm
                app.FAZ_ctr = app.fullImSizePix/2;
                app.ReadyLabel.Text = 'Ready';
                app.ReadyLamp.Color = [0.00,1.00,0.00];
            end
        end

        % Button pushed function: ImagesubsetButton
        function ImagesubsetButtonPushed(app, event)
            if isempty(app.inputImage)
                warndlg('You did not choose an image file') ;
            else
                ne = newline;
                fid = uifigure('Name','Select subregion of interest','NumberTitle','off',"Color",[0.55,0.75,0.88]);
                imaxs = uiaxes("Parent",fid,'Position',[120,20,400,400]);
                imagesc(app.inputImage, 'Parent',imaxs)
                imaxs.Colormap = gray;
                [Ny,Nx] = size(app.inputImage);
                imaxs.XLim = [0 Nx];
                imaxs.YLim = [0 Ny];
                imaxs.Title.String = 'Please press start to select ROI';
                imaxs.Title.FontSize = 16;
                donebutton = uibutton(fid,"push",'Text','Done','Position',[30 60 60 20]);
                cancelbutton = uibutton(fid,"push",'Text','Cancel','Position',[30 10 60 20]);
                roiSizebutton = uibutton(fid,"push",'Text','Get ROI size', 'Position', [20 135 80 20]);
                startbutton = uibutton(fid,"push",'Text','Start','Position',[30 295 60 20]);
                clearbutton = uibutton(fid,"push",'Text','Clear','Position',[30 35 60 20]);
                sizelabel = uilabel(fid,'Position',[20,160,80,40],"Text",'ROI size',"BackgroundColor",[1 1 1]);
                roiTypGrp = uibuttongroup(fid, 'Position', [20 320  80 60 ]);
                roi1 = uiradiobutton(roiTypGrp,"Text",'Rectangle','Position',[5 30 80 20]);
                uiradiobutton(roiTypGrp,"Text",'Round','Position',[5 10 60 20]);
                resizeCheckBox = uicheckbox(fid,"Text",['Use ROI size' ne 'as image size?'],"Position",[15 175 100 80]);
                realSizeField = uieditfield(fid, 'numeric',"Position",[20,245,80,20],"Value",5);
                uilabel(fid,'Position',[20,253,100,40],"Text",'Img width (mm)');
                pixmmswitch = uiswitch(fid, 'slider',"Position",[40 110 80 20],"Items",{'pix','mm'});
                
                
                roiTypGrp.SelectionChangedFcn = {@roiselection,roi1};
                startbutton.ButtonPushedFcn = {@startButtonPushed};
                donebutton.ButtonPushedFcn = {@doneButtonPushed,fid,app,resizeCheckBox};
                cancelbutton.ButtonPushedFcn = {@cancelcallback, fid};
                roiSizebutton.ButtonPushedFcn = {@roiSizeCallback,fid,sizelabel,realSizeField,pixmmswitch,Nx};
                clearbutton.ButtonPushedFcn = {@clearButtonPushed};
                
                
                roishape = 'rect';
                h_rect = [];
                
            end
            
            function cancelcallback(~,~,fid)
                close(fid)
            end
            
            
            
            function app = doneButtonPushed(~,~,fid,app,resizeCheckBox)
                if strcmp(roishape,'rect')
                    pos_rect = round(h_rect.Position);
                    pos_rect(pos_rect<1) =1;
                    [y,~] = size(app.inputImage);
                    pos_rect(pos_rect>(y)) =y;
                    app.inputImage = app.inputImage(pos_rect(2) + (0:pos_rect(4)), pos_rect(1) + (0:pos_rect(3)));
                    if resizeCheckBox.Value
                        app.fullImSizePix = pos_rect(3);
                    end
                    app.FAZ_ctr = [pos_rect(3)/2,pos_rect(4)/2];
                else
                    t = h_rect.createMask;
                    app.inputImage = app.inputImage.*t;
                    Cx = round(h_rect.Center(1));
                    Cy = round(h_rect.Center(2));
                    r = round(h_rect.Radius);
                    app.inputImage = app.inputImage(Cy-r:Cy+r,Cx-r:Cx+r);
                    if resizeCheckBox.Value
                        app.fullImSizePix = h_rect.Radius*2;
                    end
                    app.FAZ_ctr = [Cx,Cy];
                end
                
                app.imgShape = roishape;
                
                close(fid)
                imagesc( app.inputImage, 'Parent', app.inputImageAxes);
            end
            
            function  roiselection(~,~,roi1)
                if roi1.Value
                    roishape = 'rect';
                else
                    roishape = 'round';
                end
                
            end
            
            function roiSizeCallback(~,~,~,sizelabel,realSizeField,pixmmswitch,Nx)
                if ~isempty(h_rect)
                    c = newline;
                    if strcmp(pixmmswitch.Value,'pix')
                        if strcmp(roishape,'rect')
                            pos_rect = round(h_rect.Position);
                            sizelabel.Text = ['x = ' num2str(pos_rect(3)) ' pixels'  c 'y = ' num2str(pos_rect(4)) ' pixels'];
                        else
                            sizelabel.Text = ['r = ' num2str(round(h_rect.Radius)) ' pixels'];
                        end
                    else
                        pix_to_mm = realSizeField.Value/Nx;
                        if strcmp(roishape,'rect')
                            pos_rect = round(h_rect.Position.*pix_to_mm,2);
                            sizelabel.Text = ['x = ' num2str(pos_rect(3)) ' mm'  c 'y = ' num2str(pos_rect(4)) ' mm'];
                        else
                            sizelabel.Text = ['r = ' num2str(round(h_rect.Radius*pix_to_mm,2)) ' mm'];
                        end
                    end
                    
                else
                    sizelabel.Text = 'ROI not found';
                end
            end
            
            function startButtonPushed(~,~)
                if strcmp(roishape,'rect')
                    h_rect = drawrectangle(imaxs);
                else
                    h_rect = drawcircle(imaxs);
                end
            end
            
            function clearButtonPushed(~,~)
                delete(h_rect)
                h_rect = [];
            end
        end

        % Menu selected function: saveBinaryImageMenu
        function saveBinaryImageMenuSelected(app, event)
            %Saves binary mask and overlay image
            app.ReadyLabel.Text = 'Wait'; %sets wait label
            app.ReadyLamp.Color = [1,0,0];
            drawnow
            
            fol = fullfile(app.SaveFolder,'images');
            if ~exist(fol, 'dir')
                mkdir(fol)
                imgnum = 0;
            else
                list = dir(fullfile(fol, '*_Binary mask*.tif'));
                imgnum = length(list);
            end
            
            if ~app.skelReady
                warndlg('No binary mask found') ;
            else
                TifFileName=fullfile(fol,[ app.FileLabelName  '_Binary mask_' num2str(imgnum) '.tif']);
                imwrite(app.BinaryImage,TifFileName,'tif','WriteMode','append','Compression','none','Description','none');
                
                %Save the overlay image
                fig = figure;
                fig.Visible = 'off';
                figAxes = axes(fig);
                allChildren = app.BinaryImageAxes.XAxis.Parent.Children;
                copyobj(allChildren, figAxes)
                fig.Colormap = app.bin_overlay;
                figAxes.XLim = app.BinaryImageAxes.XLim;
                figAxes.YLim = app.BinaryImageAxes.YLim;
                figAxes.ZLim = app.BinaryImageAxes.ZLim;
                figAxes.DataAspectRatio = app.BinaryImageAxes.DataAspectRatio;
                figAxes.YDir = 'reverse';
                axis(figAxes,'off')
                fig.Position = fig.Position.*[1 1 5 5];
                TifFileName=fullfile(fol,[ app.FileLabelName  '_Binary overlay_' num2str(imgnum) '.tif']);
                export_fig(fig, TifFileName);
                
                
                app.ReadyLabel.Text = 'Ready';
                app.ReadyLamp.Color = [0 1 0];
                drawnow
                
            end
            
            
        end

        % Menu selected function: saveSessionDataMenu
        function saveSessionDataMenuSelected(app, event)
            savedir = uigetdir(app.lastPath);
            if savedir ~=0
                app.lastPath=savedir;
            end
            datatable = struct2table(app.metrics_cumulative);
            t = datestr(datetime);
            t = erase(t,':')';
            ExcelFilename = [savedir '/OCTAVA Results ' t' '.xlsx']; %This may have issues on mac?!
            writetable(datatable,ExcelFilename,'Sheet', 'General metrics');
            
            
            datatable = struct2table(app.FAZ_metrics_cumulative);
            writetable(datatable,ExcelFilename, 'Sheet', 'FAZ metrics');
        end

        % Menu selected function: ClearsessiondataMenu
        function ClearsessiondataMenuSelected(app, event)
            %Reinitializes variables for saving session results
            init_session(app)
        end

        % Menu selected function: ClearplotsMenu
        function ClearplotsMenuSelected(app, event)
            %Clear all plots
            cla(app.inputImageAxes);
            cla(app.BinaryImageAxes);
            cla(app.SkelImageAxes);
            cla(app.OverlayImageAxes);
            cla(app.DiamsAxes);
            cla(app.LengthsAxes);
            cla(app.TortsAxes);
            axis(app.OverlayImageAxes,'on')
            
            %Reset display for caluclulated biomarkers
            app.VesselareadensityLabel.Text = 'Vessel area density = ';
            app.VessellengthdensityLabel.Text = 'Vessel length density = ';
            app.TotalvessellengthLabel.Text = 'Total velles length = ';
            app.MeandiameterLabel.Text = 'Mean diameter = '  ;
            app.MediandiameterLabel.Text = 'Median diameter = ';
            app.BranchpointdensityLabel.Text = 'Branchpoint density = ';
            app.FractaldimensionLabel.Text = 'Fractal dimension = ';
            app.MeantortuosityLabel.Text = 'Mean tortuosity = ';
            
            %Reset ready label
            app.ReadyLabel.Text = 'Ready';
            app.ReadyLamp.Color = [0 1 0];
        end

        % Menu selected function: ShowOCTAVAhelpMenu
        function ShowOCTAVAhelpMenuSelected(app, event)
            helpfile = fullfile(app.homedir,'OCTAVA2.0_Readme.txt');
            open(helpfile)
        end

        % Value changed function: RetinaCheckBox
        function RetinaCheckBoxValueChanged(app, event)
            if app.RetinaCheckBox.Value
                init_session_retina(app)
            end
        end

        % Button pushed function: MeasureFAZButton
        function MeasureFAZButtonPushed(app, event)
            if isempty(app.BinaryImage)
                warndlg('Binary image required') ;
            else
                app.ReadyLabel.Text = 'Wait';
                app.ReadyLamp.Color = [1.00,0.00,0.00];
                drawnow
                
                FAZAnalysis(app);
                
            end
            
            app.ReadyLabel.Text = 'Ready';
            app.ReadyLamp.Color = [0.00,1.00,0.00];
        end

        % Button pushed function: RegionalanalysisButton
        function RegionalanalysisButtonPushed(app, event)
            if isempty(app.BinaryImage)
                warndlg('Binary image required') ;
            else
                app.ReadyLabel.Text = 'Wait';
                app.ReadyLamp.Color = [1.00,0.00,0.00];
                drawnow
                
                regionalAnalysis(app);
                
                app.ReadyLabel.Text = 'Ready';
                app.ReadyLamp.Color = [0.00,1.00,0.00];
            end
        end

        % Button pushed function: SelectSaveFolderButton_single
        function SelectSaveFolderButton_singlePushed(app, event)
            [app.SaveFolder] = uigetdir(app.lastPath);
            app.savefileLabel_single.Text = app.SaveFolder;
            
            if ~exist(app.SaveFolder, 'dir')
                mkdir(app.SaveFolder)
            end
            
            app.SaveDir = fullfile(app.SaveFolder,app.FileLabelName);
            if ~exist(app.SaveDir, 'dir')
                mkdir(app.SaveDir)
            end
            
            app.lastPath = app.SaveFolder;
        end

        % Button pushed function: RawdatafolderButton
        function RawdatafolderButtonPushed(app, event)
            [app.RawFolder] = uigetdir(app.lastPath);
            app.bachfileLabel.Text = app.RawFolder;
            
        end

        % Button pushed function: StartbatchprocessButton
        function StartbatchprocessButtonPushed(app, event)
            ready = questdlg('Are you sure you are ready to start batch processing?' ,'Batch processing', 'Yes', 'No', 'No');
            
            if strcmp(ready,'Yes')
                app.ReadyLabel.Text = 'Wait';
                app.ReadyLamp.Color = [1.00,0.00,0.00];
                app.Abort.Value = false;
                app.Abort.FontColor = [1, 0, 0];
                drawnow
                
                
                %Setup variables for saving metrics
                init_session(app)
                
                if app.RetinaCheckBox.Value
                    init_session_retina(app)
                end
                
                %Generate list of all files in the directory
                filetype = app.FiletypeDropDown.Value;
                
                if strcmp(filetype,'binary mask')
                    filetype = 'tif';
                    prebin = 1;
                else
                    prebin = 0;
                    
                end
                list = dir(fullfile(app.RawFolder,['*.' filetype]));
                
                %Timestamp for saving cumulative data
                t = datestr(datetime);
                t = erase(t,':');
                
                for nn = 1:length(list)
                    app.ProgressLabel.Text = ['Processing ' num2str(nn) ' of ' num2str(length(list))];
                    drawnow
                    
                    %Load each image
                    loadImage(app, app.RawFolder, list(nn).name)
                    
                    fol = fullfile(app.SaveFolder,'images');
                    if ~exist(fol, 'dir')
                        mkdir(fol)
                    end
                    
                    %Run the binarization
                    if prebin == 0
                        binarizeImage(app)
                    end
                    
                    pause(0.1)
                    if get(app.Abort, 'value')
                        break;
                    end
                    
                    if app.SavebinaryCheckBox.Value
                        list = dir(fullfile(fol, '*_Binary mask*.tif'));
                        imgnum = length(list);
                        TifFileName=fullfile(fol,[ app.FileLabelName  '_Binary mask_' num2str(imgnum) '.tif']);
                        imwrite(app.BinaryImage,TifFileName,'tif','WriteMode','append','Compression','none','Description','none');
                        
                        %Save the overlay image
                        fig = figure;
                        fig.Visible = 'off';
                        figAxes = axes(fig);
                        allChildren = app.BinaryImageAxes.XAxis.Parent.Children;
                        copyobj(allChildren, figAxes)
                        fig.Colormap = app.bin_overlay;
                        figAxes.XLim = app.BinaryImageAxes.XLim;
                        figAxes.YLim = app.BinaryImageAxes.YLim;
                        figAxes.ZLim = app.BinaryImageAxes.ZLim;
                        figAxes.DataAspectRatio = app.BinaryImageAxes.DataAspectRatio;
                        figAxes.YDir = 'reverse';
                        axis(figAxes,'off')
                        fig.Position = fig.Position.*[1 1 5 5];
                        TifFileName=fullfile(fol,[ app.FileLabelName  '_Binary overlay_' num2str(imgnum) '.tif']);
                        export_fig(fig, TifFileName);
                    end
                    
                    %skeletonization
                    
                    skeletonize(app, app.BinaryImage, fol, 1);
                    
                    pause(0.1)
                    if get(app.Abort, 'value')
                        break;
                    end
                    
                    %Generate metrics
                    generateMetrics(app)
                    
                    if app.RetinaCheckBox.Value
                        pause(0.1)
                        if get(app.Abort, 'value')
                            break;
                        end
                        FAZAnalysis(app)
                        
                        pause(0.1)
                        if get(app.Abort, 'value')
                            break;
                        end
                        
                        regionalAnalysis(app)
                    end
                end
                
                if  ~isempty(list) && ~app.Abort.Value
                    %Save spreadsheet with summary metrics and FAZ metrics
                    datatable = struct2table(app.metrics_cumulative);
                    
                    ExcelFilename = [app.SaveDir '/OCTAVA Results ' t '.xlsx']; %This may have issues on mac?!
                    writetable(datatable,ExcelFilename,'Sheet', 'General metrics');
                    
                    datatable = struct2table(app.FAZ_metrics_cumulative);
                    writetable(datatable,ExcelFilename, 'Sheet', 'FAZ metrics');
                end
                
                init_session(app)
                
                app.ReadyLabel.Text = 'Ready';
                app.ReadyLamp.Color = [0.00,1.00,0.00];
                app.Abort.Value = false;
                app.Abort.FontColor = [0.00,0.00,0.00];
                drawnow
                
                
            end
        end

        % Value changing function: RapidFAZStringencyfactorSlider
        function RapidFAZStringencyfactorSliderValueChanging(app, event)
            changingValue = event.Value;
            [r,c] = size(app.BinaryImage);
            sz = mean(r,c);
            D = ceil(sz*changingValue);
            app.Ffactor.Value=D;
            
        end

        % Value changed function: TuneFAZsegmentationCheckBox
        function TuneFAZsegmentationCheckBoxValueChanged(app, event)
            value = app.TuneFAZsegmentationCheckBox.Value;
            
        end

        % Button pushed function: RapidFAZButton_2
        function RapidFAZButton_2Pushed(app, event)
            fval = app.RapidFAZStringencyfactorSlider.Value;
            [r,c] = size(app.BinaryImage);
            
            if fval==0
                sz = mean(r,c);
                D = ceil(sz*0.0075);
            else
                F = app.RapidFAZStringencyfactorSlider.Value;
                sz = mean(r,c);
                D = ceil(sz*F);
            end
            
            dilIm = imdilate(app.BinaryImage,offsetstrel('ball',D,ceil(D/2)));
            gdIm = imgaussfilt(dilIm,D/2);
            th = gdIm<192;
            objs = regionprops('table',th,'Area','BoundingBox','FilledImage','Centroid');
            [a,b] = size(objs);
            if a == 1
                faz_obj = objs;
                bb=uint16(faz_obj.BoundingBox);
                bbox = double(faz_obj.FilledImage{1});
            elseif a > 1
                objs.CentroidDists = pdist2(objs.Centroid,app.FAZ_ctr,'euclidean');
                var = min(objs.CentroidDists);
                faz_obj = objs(objs.CentroidDists==var,:);
                %var = max(objs.Area);
                %faz_obj = objs(objs.Area==var,:);
                bb=uint16(faz_obj.BoundingBox);
                bbox = double(faz_obj.FilledImage{1});
            else
                bb = [1,1,1,1];
                bbox=zeros(1,1);
            end
            faz = zeros(r,c);
            faz(bb(2):bb(2)+bb(4)-1,bb(1):bb(1)+bb(3)-1)=bbox;
            app.FAZmask=faz;
            figure(1);
            imshowpair(app.BinaryImage,faz);
        end
    end

    % Component initialization
    methods (Access = private)

        % Create UIFigure and components
        function createComponents(app)

            % Get the file path for locating images
            pathToMLAPP = fileparts(mfilename('fullpath'));

            % Create OCTAVAUIFigure and hide until all components are created
            app.OCTAVAUIFigure = uifigure('Visible', 'off');
            app.OCTAVAUIFigure.Position = [100 100 1286 810];
            app.OCTAVAUIFigure.Name = 'OCTAVA';
            app.OCTAVAUIFigure.Icon = fullfile(pathToMLAPP, 'OCTAVAicon.png');

            % Create SaveMenu
            app.SaveMenu = uimenu(app.OCTAVAUIFigure);
            app.SaveMenu.Text = 'Save';

            % Create saveBinaryImageMenu
            app.saveBinaryImageMenu = uimenu(app.SaveMenu);
            app.saveBinaryImageMenu.MenuSelectedFcn = createCallbackFcn(app, @saveBinaryImageMenuSelected, true);
            app.saveBinaryImageMenu.Text = 'Binary Image ';

            % Create saveSessionDataMenu
            app.saveSessionDataMenu = uimenu(app.SaveMenu);
            app.saveSessionDataMenu.MenuSelectedFcn = createCallbackFcn(app, @saveSessionDataMenuSelected, true);
            app.saveSessionDataMenu.Text = 'Session Data';

            % Create ClearMenu
            app.ClearMenu = uimenu(app.OCTAVAUIFigure);
            app.ClearMenu.Text = 'Clear';

            % Create ClearsessiondataMenu
            app.ClearsessiondataMenu = uimenu(app.ClearMenu);
            app.ClearsessiondataMenu.MenuSelectedFcn = createCallbackFcn(app, @ClearsessiondataMenuSelected, true);
            app.ClearsessiondataMenu.Text = 'Clear session data';

            % Create ClearplotsMenu
            app.ClearplotsMenu = uimenu(app.ClearMenu);
            app.ClearplotsMenu.MenuSelectedFcn = createCallbackFcn(app, @ClearplotsMenuSelected, true);
            app.ClearplotsMenu.Text = 'Clear plots';

            % Create HelpMenu
            app.HelpMenu = uimenu(app.OCTAVAUIFigure);
            app.HelpMenu.Text = 'Help';

            % Create ShowOCTAVAhelpMenu
            app.ShowOCTAVAhelpMenu = uimenu(app.HelpMenu);
            app.ShowOCTAVAhelpMenu.MenuSelectedFcn = createCallbackFcn(app, @ShowOCTAVAhelpMenuSelected, true);
            app.ShowOCTAVAhelpMenu.Text = 'Show OCTAVA help';

            % Create GridLayout
            app.GridLayout = uigridlayout(app.OCTAVAUIFigure);
            app.GridLayout.ColumnWidth = {'1.1x', '0.9x', '1.2x', '0.8x', '1x', '1x', '1x', '1x', '0.9x', '0.8x', '1.3x', '1x', '1x', '1x', '1x', '1x', '1x', '1x', '1x', '1x'};
            app.GridLayout.RowHeight = {'fit', '0.5x', '0.25x', '0.25x', 'fit', 'fit', '1x', 'fit'};

            % Create inputImageAxes
            app.inputImageAxes = uiaxes(app.GridLayout);
            title(app.inputImageAxes, 'Original Image')
            app.inputImageAxes.DataAspectRatio = [1 1 1];
            app.inputImageAxes.PlotBoxAspectRatio = [1 1 1];
            app.inputImageAxes.XTick = [];
            app.inputImageAxes.YTick = [];
            app.inputImageAxes.ClippingStyle = 'rectangle';
            app.inputImageAxes.FontSize = 16;
            app.inputImageAxes.Layout.Row = [2 4];
            app.inputImageAxes.Layout.Column = [1 4];

            % Create BinaryImageAxes
            app.BinaryImageAxes = uiaxes(app.GridLayout);
            title(app.BinaryImageAxes, 'Segmented Image ')
            app.BinaryImageAxes.DataAspectRatio = [1 1 1];
            app.BinaryImageAxes.PlotBoxAspectRatio = [1 1 1];
            app.BinaryImageAxes.XTick = [];
            app.BinaryImageAxes.YTick = [];
            app.BinaryImageAxes.ClippingStyle = 'rectangle';
            app.BinaryImageAxes.FontSize = 16;
            app.BinaryImageAxes.Layout.Row = [2 4];
            app.BinaryImageAxes.Layout.Column = [5 8];

            % Create SkelImageAxes
            app.SkelImageAxes = uiaxes(app.GridLayout);
            title(app.SkelImageAxes, 'Skeletonized Image')
            app.SkelImageAxes.DataAspectRatio = [1 1 1];
            app.SkelImageAxes.PlotBoxAspectRatio = [1 1 1];
            app.SkelImageAxes.XTick = [];
            app.SkelImageAxes.YTick = [];
            app.SkelImageAxes.ClippingStyle = 'rectangle';
            app.SkelImageAxes.FontSize = 16;
            app.SkelImageAxes.Layout.Row = [2 4];
            app.SkelImageAxes.Layout.Column = [9 12];

            % Create OverlayImageAxes
            app.OverlayImageAxes = uiaxes(app.GridLayout);
            title(app.OverlayImageAxes, 'Overlay')
            app.OverlayImageAxes.DataAspectRatio = [1 1 1];
            app.OverlayImageAxes.PlotBoxAspectRatio = [1 1 1];
            app.OverlayImageAxes.XTick = [];
            app.OverlayImageAxes.YTick = [];
            app.OverlayImageAxes.ClippingStyle = 'rectangle';
            app.OverlayImageAxes.FontSize = 16;
            app.OverlayImageAxes.Layout.Row = [2 4];
            app.OverlayImageAxes.Layout.Column = [13 16];

            % Create DiamsAxes
            app.DiamsAxes = uiaxes(app.GridLayout);
            title(app.DiamsAxes, 'Diameters')
            xlabel(app.DiamsAxes, 'Diameters (\mum)')
            ylabel(app.DiamsAxes, 'Frequency')
            zlabel(app.DiamsAxes, 'Z')
            app.DiamsAxes.PlotBoxAspectRatio = [1.28782287822878 1 1];
            app.DiamsAxes.FontSize = 16;
            app.DiamsAxes.Layout.Row = 7;
            app.DiamsAxes.Layout.Column = [6 9];
            app.DiamsAxes.Tag = 'Diams';

            % Create LengthsAxes
            app.LengthsAxes = uiaxes(app.GridLayout);
            title(app.LengthsAxes, 'Lengths')
            xlabel(app.LengthsAxes, 'Length (mm)')
            ylabel(app.LengthsAxes, 'Frequency')
            zlabel(app.LengthsAxes, 'Z')
            app.LengthsAxes.PlotBoxAspectRatio = [1.27322404371585 1 1];
            app.LengthsAxes.FontSize = 16;
            app.LengthsAxes.Layout.Row = 7;
            app.LengthsAxes.Layout.Column = [10 13];
            app.LengthsAxes.Tag = 'Torts';

            % Create TortsAxes
            app.TortsAxes = uiaxes(app.GridLayout);
            title(app.TortsAxes, 'Tortuosity')
            xlabel(app.TortsAxes, 'Tortuosity')
            ylabel(app.TortsAxes, 'Frequency')
            zlabel(app.TortsAxes, 'Z')
            app.TortsAxes.PlotBoxAspectRatio = [1.27322404371585 1 1];
            app.TortsAxes.FontSize = 16;
            app.TortsAxes.Layout.Row = 7;
            app.TortsAxes.Layout.Column = [14 17];
            app.TortsAxes.Tag = 'Torts';

            % Create OCTAVALabel
            app.OCTAVALabel = uilabel(app.GridLayout);
            app.OCTAVALabel.FontSize = 24;
            app.OCTAVALabel.FontWeight = 'bold';
            app.OCTAVALabel.FontColor = [0 0.451 0.7412];
            app.OCTAVALabel.Layout.Row = 1;
            app.OCTAVALabel.Layout.Column = [1 2];
            app.OCTAVALabel.Text = 'OCTAVA';

            % Create FileLabel
            app.FileLabel = uilabel(app.GridLayout);
            app.FileLabel.FontSize = 16;
            app.FileLabel.Layout.Row = 1;
            app.FileLabel.Layout.Column = [3 4];
            app.FileLabel.Text = 'Filename';

            % Create ReadyLabel
            app.ReadyLabel = uilabel(app.GridLayout);
            app.ReadyLabel.FontSize = 20;
            app.ReadyLabel.FontWeight = 'bold';
            app.ReadyLabel.FontColor = [0.149 0.149 0.149];
            app.ReadyLabel.Layout.Row = 1;
            app.ReadyLabel.Layout.Column = [15 16];
            app.ReadyLabel.Text = 'Ready';

            % Create Label
            app.Label = uilabel(app.GridLayout);
            app.Label.HorizontalAlignment = 'right';
            app.Label.Layout.Row = 1;
            app.Label.Layout.Column = 13;
            app.Label.Text = '';

            % Create ReadyLamp
            app.ReadyLamp = uilamp(app.GridLayout);
            app.ReadyLamp.Layout.Row = 1;
            app.ReadyLamp.Layout.Column = 14;

            % Create LoadimageButton
            app.LoadimageButton = uibutton(app.GridLayout, 'push');
            app.LoadimageButton.ButtonPushedFcn = createCallbackFcn(app, @LoadimageButtonPushed, true);
            app.LoadimageButton.FontSize = 16;
            app.LoadimageButton.Layout.Row = 5;
            app.LoadimageButton.Layout.Column = [1 2];
            app.LoadimageButton.Text = 'Load image';

            % Create ResizeButton
            app.ResizeButton = uibutton(app.GridLayout, 'push');
            app.ResizeButton.ButtonPushedFcn = createCallbackFcn(app, @ResizeButtonPushed, true);
            app.ResizeButton.WordWrap = 'on';
            app.ResizeButton.FontSize = 16;
            app.ResizeButton.Layout.Row = 6;
            app.ResizeButton.Layout.Column = 2;
            app.ResizeButton.Text = 'Re-size';

            % Create BinarizeButton
            app.BinarizeButton = uibutton(app.GridLayout, 'push');
            app.BinarizeButton.ButtonPushedFcn = createCallbackFcn(app, @BinarizeButtonPushed, true);
            app.BinarizeButton.FontSize = 16;
            app.BinarizeButton.Layout.Row = 5;
            app.BinarizeButton.Layout.Column = [5 6];
            app.BinarizeButton.Text = 'Binarize';

            % Create InvertButton
            app.InvertButton = uibutton(app.GridLayout, 'push');
            app.InvertButton.ButtonPushedFcn = createCallbackFcn(app, @InvertButtonPushed, true);
            app.InvertButton.FontSize = 16;
            app.InvertButton.Layout.Row = 5;
            app.InvertButton.Layout.Column = 7;
            app.InvertButton.Text = 'Invert';

            % Create SkeletonizeButton
            app.SkeletonizeButton = uibutton(app.GridLayout, 'push');
            app.SkeletonizeButton.ButtonPushedFcn = createCallbackFcn(app, @SkeletonizeButtonPushed, true);
            app.SkeletonizeButton.FontSize = 16;
            app.SkeletonizeButton.Layout.Row = 5;
            app.SkeletonizeButton.Layout.Column = [9 10];
            app.SkeletonizeButton.Text = 'Skeletonize ';

            % Create ImagesubsetButton
            app.ImagesubsetButton = uibutton(app.GridLayout, 'push');
            app.ImagesubsetButton.ButtonPushedFcn = createCallbackFcn(app, @ImagesubsetButtonPushed, true);
            app.ImagesubsetButton.WordWrap = 'on';
            app.ImagesubsetButton.FontSize = 16;
            app.ImagesubsetButton.Layout.Row = 6;
            app.ImagesubsetButton.Layout.Column = 1;
            app.ImagesubsetButton.Text = 'Image subset';

            % Create SegmentationmethodDropDown
            app.SegmentationmethodDropDown = uidropdown(app.GridLayout);
            app.SegmentationmethodDropDown.Items = {'Fuzzy means', 'Adaptive thresholding'};
            app.SegmentationmethodDropDown.FontSize = 16;
            app.SegmentationmethodDropDown.Layout.Row = 6;
            app.SegmentationmethodDropDown.Layout.Column = [7 9];
            app.SegmentationmethodDropDown.Value = 'Fuzzy means';

            % Create MedfiltCheckBox
            app.MedfiltCheckBox = uicheckbox(app.GridLayout);
            app.MedfiltCheckBox.Text = 'Med filt';
            app.MedfiltCheckBox.FontSize = 16;
            app.MedfiltCheckBox.Layout.Row = 5;
            app.MedfiltCheckBox.Layout.Column = [3 4];

            % Create kernelSize
            app.kernelSize = uispinner(app.GridLayout);
            app.kernelSize.Limits = [0 Inf];
            app.kernelSize.Layout.Row = 5;
            app.kernelSize.Layout.Column = 4;
            app.kernelSize.Value = 3;

            % Create FrangiBool
            app.FrangiBool = uicheckbox(app.GridLayout);
            app.FrangiBool.Text = 'Frangi';
            app.FrangiBool.FontSize = 16;
            app.FrangiBool.Layout.Row = 6;
            app.FrangiBool.Layout.Column = 3;
            app.FrangiBool.Value = true;

            % Create sigmamaxSpinner
            app.sigmamaxSpinner = uispinner(app.GridLayout);
            app.sigmamaxSpinner.Limits = [0 30];
            app.sigmamaxSpinner.RoundFractionalValues = 'on';
            app.sigmamaxSpinner.ValueDisplayFormat = '%d';
            app.sigmamaxSpinner.FontSize = 16;
            app.sigmamaxSpinner.Layout.Row = 6;
            app.sigmamaxSpinner.Layout.Column = 4;
            app.sigmamaxSpinner.Value = 8;

            % Create ATkernelsizeSpinnerLabel
            app.ATkernelsizeSpinnerLabel = uilabel(app.GridLayout);
            app.ATkernelsizeSpinnerLabel.HorizontalAlignment = 'right';
            app.ATkernelsizeSpinnerLabel.FontSize = 14;
            app.ATkernelsizeSpinnerLabel.Layout.Row = 6;
            app.ATkernelsizeSpinnerLabel.Layout.Column = 10;
            app.ATkernelsizeSpinnerLabel.Text = {'AT'; 'kernel'; 'size'};

            % Create ATkernelsizeSpinner
            app.ATkernelsizeSpinner = uispinner(app.GridLayout);
            app.ATkernelsizeSpinner.Step = 10;
            app.ATkernelsizeSpinner.Limits = [0 Inf];
            app.ATkernelsizeSpinner.FontSize = 14;
            app.ATkernelsizeSpinner.Layout.Row = 6;
            app.ATkernelsizeSpinner.Layout.Column = 11;
            app.ATkernelsizeSpinner.Value = 70;

            % Create TwigsizeLabel
            app.TwigsizeLabel = uilabel(app.GridLayout);
            app.TwigsizeLabel.HorizontalAlignment = 'right';
            app.TwigsizeLabel.WordWrap = 'on';
            app.TwigsizeLabel.FontSize = 16;
            app.TwigsizeLabel.Layout.Row = 5;
            app.TwigsizeLabel.Layout.Column = 11;
            app.TwigsizeLabel.Text = 'Twig size ';

            % Create TwigsizeSpinner
            app.TwigsizeSpinner = uispinner(app.GridLayout);
            app.TwigsizeSpinner.Limits = [0 30];
            app.TwigsizeSpinner.RoundFractionalValues = 'on';
            app.TwigsizeSpinner.ValueDisplayFormat = '%.0f';
            app.TwigsizeSpinner.FontSize = 16;
            app.TwigsizeSpinner.Layout.Row = 5;
            app.TwigsizeSpinner.Layout.Column = 12;
            app.TwigsizeSpinner.Value = 20;

            % Create BiomarkersButton
            app.BiomarkersButton = uibutton(app.GridLayout, 'push');
            app.BiomarkersButton.ButtonPushedFcn = createCallbackFcn(app, @BiomarkersButtonPushed, true);
            app.BiomarkersButton.FontSize = 16;
            app.BiomarkersButton.Layout.Row = 5;
            app.BiomarkersButton.Layout.Column = [13 15];
            app.BiomarkersButton.Text = 'Generate metrics';

            % Create SelectSaveFolderButton_single
            app.SelectSaveFolderButton_single = uibutton(app.GridLayout, 'push');
            app.SelectSaveFolderButton_single.ButtonPushedFcn = createCallbackFcn(app, @SelectSaveFolderButton_singlePushed, true);
            app.SelectSaveFolderButton_single.WordWrap = 'on';
            app.SelectSaveFolderButton_single.FontSize = 16;
            app.SelectSaveFolderButton_single.Layout.Row = 4;
            app.SelectSaveFolderButton_single.Layout.Column = [17 18];
            app.SelectSaveFolderButton_single.Text = 'Select save folder';

            % Create binsizeLength
            app.binsizeLength = uispinner(app.GridLayout);
            app.binsizeLength.Step = 0.1;
            app.binsizeLength.Limits = [0 Inf];
            app.binsizeLength.Layout.Row = 8;
            app.binsizeLength.Layout.Column = 12;
            app.binsizeLength.Value = 0.1;

            % Create binsizeTort
            app.binsizeTort = uispinner(app.GridLayout);
            app.binsizeTort.Step = 0.1;
            app.binsizeTort.Limits = [0 Inf];
            app.binsizeTort.Layout.Row = 8;
            app.binsizeTort.Layout.Column = 15;
            app.binsizeTort.Value = 0.1;

            % Create RealImageSizemm
            app.RealImageSizemm = uieditfield(app.GridLayout, 'numeric');
            app.RealImageSizemm.FontSize = 16;
            app.RealImageSizemm.FontWeight = 'bold';
            app.RealImageSizemm.Layout.Row = 6;
            app.RealImageSizemm.Layout.Column = 15;
            app.RealImageSizemm.Value = 5;

            % Create SegmentationmethodDropDownLabel
            app.SegmentationmethodDropDownLabel = uilabel(app.GridLayout);
            app.SegmentationmethodDropDownLabel.HorizontalAlignment = 'right';
            app.SegmentationmethodDropDownLabel.WordWrap = 'on';
            app.SegmentationmethodDropDownLabel.FontSize = 16;
            app.SegmentationmethodDropDownLabel.Layout.Row = 6;
            app.SegmentationmethodDropDownLabel.Layout.Column = [5 6];
            app.SegmentationmethodDropDownLabel.Text = 'Segmentation method';

            % Create ImagesizemmLabel
            app.ImagesizemmLabel = uilabel(app.GridLayout);
            app.ImagesizemmLabel.FontSize = 16;
            app.ImagesizemmLabel.FontWeight = 'bold';
            app.ImagesizemmLabel.Layout.Row = 6;
            app.ImagesizemmLabel.Layout.Column = [13 15];
            app.ImagesizemmLabel.Text = 'Image size (mm)';

            % Create BinsizeforhistogramsLabel
            app.BinsizeforhistogramsLabel = uilabel(app.GridLayout);
            app.BinsizeforhistogramsLabel.HorizontalAlignment = 'right';
            app.BinsizeforhistogramsLabel.FontSize = 14;
            app.BinsizeforhistogramsLabel.Layout.Row = 8;
            app.BinsizeforhistogramsLabel.Layout.Column = [6 8];
            app.BinsizeforhistogramsLabel.Text = 'Bin size for histograms';

            % Create binsizeDiams
            app.binsizeDiams = uispinner(app.GridLayout);
            app.binsizeDiams.Limits = [0 Inf];
            app.binsizeDiams.FontSize = 14;
            app.binsizeDiams.Layout.Row = 8;
            app.binsizeDiams.Layout.Column = 9;
            app.binsizeDiams.Value = 10;

            % Create RetinalAnalysisPanel
            app.RetinalAnalysisPanel = uipanel(app.GridLayout);
            app.RetinalAnalysisPanel.ForegroundColor = [0 0.451 0.7412];
            app.RetinalAnalysisPanel.TitlePosition = 'centertop';
            app.RetinalAnalysisPanel.Title = 'Retinal Analysis ';
            app.RetinalAnalysisPanel.Layout.Row = [5 8];
            app.RetinalAnalysisPanel.Layout.Column = [18 20];
            app.RetinalAnalysisPanel.FontWeight = 'bold';
            app.RetinalAnalysisPanel.FontSize = 18;

            % Create GridLayout4
            app.GridLayout4 = uigridlayout(app.RetinalAnalysisPanel);
            app.GridLayout4.ColumnWidth = {'1x', '1x', '1x'};
            app.GridLayout4.RowHeight = {'fit', '0.5x', '0.5x', '0.5x', '1x', '1x', '1x'};

            % Create RetinaCheckBox
            app.RetinaCheckBox = uicheckbox(app.GridLayout4);
            app.RetinaCheckBox.ValueChangedFcn = createCallbackFcn(app, @RetinaCheckBoxValueChanged, true);
            app.RetinaCheckBox.Text = 'Retina';
            app.RetinaCheckBox.FontSize = 10;
            app.RetinaCheckBox.Layout.Row = 1;
            app.RetinaCheckBox.Layout.Column = 1;

            % Create RL
            app.RL = uidropdown(app.GridLayout4);
            app.RL.Items = {'Right Eye', 'Left Eye'};
            app.RL.FontSize = 14;
            app.RL.Layout.Row = 1;
            app.RL.Layout.Column = [2 3];
            app.RL.Value = 'Right Eye';

            % Create RegionalanalysisButton
            app.RegionalanalysisButton = uibutton(app.GridLayout4, 'push');
            app.RegionalanalysisButton.ButtonPushedFcn = createCallbackFcn(app, @RegionalanalysisButtonPushed, true);
            app.RegionalanalysisButton.FontSize = 16;
            app.RegionalanalysisButton.Layout.Row = 6;
            app.RegionalanalysisButton.Layout.Column = [1 3];
            app.RegionalanalysisButton.Text = {'Regional'; 'analysis'};

            % Create MeasureFAZButton
            app.MeasureFAZButton = uibutton(app.GridLayout4, 'push');
            app.MeasureFAZButton.ButtonPushedFcn = createCallbackFcn(app, @MeasureFAZButtonPushed, true);
            app.MeasureFAZButton.FontSize = 16;
            app.MeasureFAZButton.Layout.Row = 5;
            app.MeasureFAZButton.Layout.Column = [1 3];
            app.MeasureFAZButton.Text = 'Measure FAZ';

            % Create GridType
            app.GridType = uidropdown(app.GridLayout4);
            app.GridType.Items = {'Square grid', 'Circular grid'};
            app.GridType.FontSize = 16;
            app.GridType.Layout.Row = 7;
            app.GridType.Layout.Column = [1 3];
            app.GridType.Value = 'Square grid';

            % Create GridLayout6
            app.GridLayout6 = uigridlayout(app.GridLayout4);
            app.GridLayout6.Layout.Row = 2;
            app.GridLayout6.Layout.Column = 3;

            % Create RapidFAZStringencyfactorSlider
            app.RapidFAZStringencyfactorSlider = uislider(app.GridLayout4);
            app.RapidFAZStringencyfactorSlider.Limits = [0.005 0.02];
            app.RapidFAZStringencyfactorSlider.MajorTicks = [0.005 0.0125 0.02];
            app.RapidFAZStringencyfactorSlider.MajorTickLabels = {'Lax', '', 'Strict'};
            app.RapidFAZStringencyfactorSlider.ValueChangingFcn = createCallbackFcn(app, @RapidFAZStringencyfactorSliderValueChanging, true);
            app.RapidFAZStringencyfactorSlider.MinorTicks = [];
            app.RapidFAZStringencyfactorSlider.Layout.Row = 3;
            app.RapidFAZStringencyfactorSlider.Layout.Column = [2 3];
            app.RapidFAZStringencyfactorSlider.FontSize = 9;
            app.RapidFAZStringencyfactorSlider.Value = 0.0075;

            % Create RapidFAZStringencyfactorSliderLabel
            app.RapidFAZStringencyfactorSliderLabel = uilabel(app.GridLayout4);
            app.RapidFAZStringencyfactorSliderLabel.HorizontalAlignment = 'center';
            app.RapidFAZStringencyfactorSliderLabel.FontSize = 11;
            app.RapidFAZStringencyfactorSliderLabel.Layout.Row = 2;
            app.RapidFAZStringencyfactorSliderLabel.Layout.Column = [2 3];
            app.RapidFAZStringencyfactorSliderLabel.Text = {'Rapid FAZ '; 'Stringency factor '};

            % Create TuneFAZsegmentationCheckBox
            app.TuneFAZsegmentationCheckBox = uicheckbox(app.GridLayout4);
            app.TuneFAZsegmentationCheckBox.ValueChangedFcn = createCallbackFcn(app, @TuneFAZsegmentationCheckBoxValueChanged, true);
            app.TuneFAZsegmentationCheckBox.Text = 'Tune FAZ segmentation';
            app.TuneFAZsegmentationCheckBox.FontSize = 10;
            app.TuneFAZsegmentationCheckBox.Layout.Row = 4;
            app.TuneFAZsegmentationCheckBox.Layout.Column = [1 3];

            % Create RapidFAZButton_2
            app.RapidFAZButton_2 = uibutton(app.GridLayout4, 'push');
            app.RapidFAZButton_2.ButtonPushedFcn = createCallbackFcn(app, @RapidFAZButton_2Pushed, true);
            app.RapidFAZButton_2.Layout.Row = [2 3];
            app.RapidFAZButton_2.Layout.Column = 1;
            app.RapidFAZButton_2.Text = {'Rapid '; 'FAZ'};

            % Create MetricsPanel
            app.MetricsPanel = uipanel(app.GridLayout);
            app.MetricsPanel.ForegroundColor = [0 0.451 0.7412];
            app.MetricsPanel.TitlePosition = 'centertop';
            app.MetricsPanel.Title = 'Metrics';
            app.MetricsPanel.Layout.Row = [7 8];
            app.MetricsPanel.Layout.Column = [1 5];
            app.MetricsPanel.FontWeight = 'bold';
            app.MetricsPanel.FontSize = 18;

            % Create GridLayout3
            app.GridLayout3 = uigridlayout(app.MetricsPanel);
            app.GridLayout3.ColumnWidth = {'1x'};
            app.GridLayout3.RowHeight = {'1x', '1x', '1x', '1x', '1x', '1x', '1x', '1x'};

            % Create VesselareadensityLabel
            app.VesselareadensityLabel = uilabel(app.GridLayout3);
            app.VesselareadensityLabel.FontSize = 18;
            app.VesselareadensityLabel.Layout.Row = 1;
            app.VesselareadensityLabel.Layout.Column = 1;
            app.VesselareadensityLabel.Text = 'Vessel area density = ';

            % Create VessellengthdensityLabel
            app.VessellengthdensityLabel = uilabel(app.GridLayout3);
            app.VessellengthdensityLabel.FontSize = 18;
            app.VessellengthdensityLabel.Layout.Row = 2;
            app.VessellengthdensityLabel.Layout.Column = 1;
            app.VessellengthdensityLabel.Text = 'Vessel length density = ';

            % Create MeandiameterLabel
            app.MeandiameterLabel = uilabel(app.GridLayout3);
            app.MeandiameterLabel.FontSize = 18;
            app.MeandiameterLabel.Layout.Row = 4;
            app.MeandiameterLabel.Layout.Column = 1;
            app.MeandiameterLabel.Text = 'Mean diameter = ';

            % Create MediandiameterLabel
            app.MediandiameterLabel = uilabel(app.GridLayout3);
            app.MediandiameterLabel.FontSize = 18;
            app.MediandiameterLabel.Layout.Row = 5;
            app.MediandiameterLabel.Layout.Column = 1;
            app.MediandiameterLabel.Text = 'Median diameter = ';

            % Create BranchpointdensityLabel
            app.BranchpointdensityLabel = uilabel(app.GridLayout3);
            app.BranchpointdensityLabel.FontSize = 18;
            app.BranchpointdensityLabel.Layout.Row = 6;
            app.BranchpointdensityLabel.Layout.Column = 1;
            app.BranchpointdensityLabel.Text = 'Branchpoint density = ';

            % Create TotalvessellengthLabel
            app.TotalvessellengthLabel = uilabel(app.GridLayout3);
            app.TotalvessellengthLabel.FontSize = 18;
            app.TotalvessellengthLabel.Layout.Row = 3;
            app.TotalvessellengthLabel.Layout.Column = 1;
            app.TotalvessellengthLabel.Text = 'Total vessel length = ';

            % Create FractaldimensionLabel
            app.FractaldimensionLabel = uilabel(app.GridLayout3);
            app.FractaldimensionLabel.FontSize = 18;
            app.FractaldimensionLabel.Layout.Row = 7;
            app.FractaldimensionLabel.Layout.Column = 1;
            app.FractaldimensionLabel.Text = 'Fractal dimension = ';

            % Create MeantortuosityLabel
            app.MeantortuosityLabel = uilabel(app.GridLayout3);
            app.MeantortuosityLabel.FontSize = 18;
            app.MeantortuosityLabel.Layout.Row = 8;
            app.MeantortuosityLabel.Layout.Column = 1;
            app.MeantortuosityLabel.Text = 'Mean tortuosity = ';

            % Create BatchProcessingPanel
            app.BatchProcessingPanel = uipanel(app.GridLayout);
            app.BatchProcessingPanel.ForegroundColor = [0 0.451 0.7412];
            app.BatchProcessingPanel.TitlePosition = 'centertop';
            app.BatchProcessingPanel.Title = 'Batch Processing';
            app.BatchProcessingPanel.Layout.Row = [1 3];
            app.BatchProcessingPanel.Layout.Column = [17 20];
            app.BatchProcessingPanel.FontWeight = 'bold';
            app.BatchProcessingPanel.FontSize = 18;

            % Create GridLayout5
            app.GridLayout5 = uigridlayout(app.BatchProcessingPanel);
            app.GridLayout5.RowHeight = {'fit', '1x', 'fit', 'fit', '1x'};

            % Create RawdatafolderButton
            app.RawdatafolderButton = uibutton(app.GridLayout5, 'push');
            app.RawdatafolderButton.ButtonPushedFcn = createCallbackFcn(app, @RawdatafolderButtonPushed, true);
            app.RawdatafolderButton.FontSize = 16;
            app.RawdatafolderButton.Layout.Row = 2;
            app.RawdatafolderButton.Layout.Column = 1;
            app.RawdatafolderButton.Text = {'Raw data '; 'folder'};

            % Create bachfileLabel
            app.bachfileLabel = uilabel(app.GridLayout5);
            app.bachfileLabel.WordWrap = 'on';
            app.bachfileLabel.Layout.Row = 2;
            app.bachfileLabel.Layout.Column = 2;
            app.bachfileLabel.Text = 'Raw folder';

            % Create FiletypeDropDown
            app.FiletypeDropDown = uidropdown(app.GridLayout5);
            app.FiletypeDropDown.Items = {'tif', 'png', 'jpg', 'binary mask'};
            app.FiletypeDropDown.FontSize = 16;
            app.FiletypeDropDown.Layout.Row = 3;
            app.FiletypeDropDown.Layout.Column = 2;
            app.FiletypeDropDown.Value = 'tif';

            % Create FiletypeDropDownLabel
            app.FiletypeDropDownLabel = uilabel(app.GridLayout5);
            app.FiletypeDropDownLabel.HorizontalAlignment = 'right';
            app.FiletypeDropDownLabel.FontSize = 16;
            app.FiletypeDropDownLabel.Layout.Row = 3;
            app.FiletypeDropDownLabel.Layout.Column = 1;
            app.FiletypeDropDownLabel.Text = 'File type';

            % Create SavebinaryCheckBox
            app.SavebinaryCheckBox = uicheckbox(app.GridLayout5);
            app.SavebinaryCheckBox.Text = 'Save binary?';
            app.SavebinaryCheckBox.FontSize = 14;
            app.SavebinaryCheckBox.Layout.Row = 4;
            app.SavebinaryCheckBox.Layout.Column = 1;

            % Create StartbatchprocessButton
            app.StartbatchprocessButton = uibutton(app.GridLayout5, 'push');
            app.StartbatchprocessButton.ButtonPushedFcn = createCallbackFcn(app, @StartbatchprocessButtonPushed, true);
            app.StartbatchprocessButton.FontSize = 16;
            app.StartbatchprocessButton.Layout.Row = 5;
            app.StartbatchprocessButton.Layout.Column = [1 2];
            app.StartbatchprocessButton.Text = 'Start batch process';

            % Create ProgressLabel
            app.ProgressLabel = uilabel(app.GridLayout5);
            app.ProgressLabel.HorizontalAlignment = 'center';
            app.ProgressLabel.WordWrap = 'on';
            app.ProgressLabel.FontSize = 16;
            app.ProgressLabel.Layout.Row = 1;
            app.ProgressLabel.Layout.Column = [1 2];
            app.ProgressLabel.Text = 'Progress ';

            % Create Abort
            app.Abort = uibutton(app.GridLayout5, 'state');
            app.Abort.Text = 'Abort';
            app.Abort.FontSize = 16;
            app.Abort.Layout.Row = 4;
            app.Abort.Layout.Column = 2;

            % Create savefileLabel_single
            app.savefileLabel_single = uilabel(app.GridLayout);
            app.savefileLabel_single.WordWrap = 'on';
            app.savefileLabel_single.Layout.Row = 4;
            app.savefileLabel_single.Layout.Column = [19 20];

            % Create ContextMenu
            app.ContextMenu = uicontextmenu(app.OCTAVAUIFigure);

            % Create Menu
            app.Menu = uimenu(app.ContextMenu);
            app.Menu.Text = 'Menu';

            % Create Menu2
            app.Menu2 = uimenu(app.ContextMenu);
            app.Menu2.Text = 'Menu2';
            
            % Assign app.ContextMenu
            app.inputImageAxes.ContextMenu = app.ContextMenu;

            % Show the figure after all components are created
            app.OCTAVAUIFigure.Visible = 'on';
        end
    end

    % App creation and deletion
    methods (Access = public)

        % Construct app
        function app = OCTAVA_2p0_MSD

            % Create UIFigure and components
            createComponents(app)

            % Register the app with App Designer
            registerApp(app, app.OCTAVAUIFigure)

            % Execute the startup function
            runStartupFcn(app, @startupFcn)

            if nargout == 0
                clear app
            end
        end

        % Code that executes before app deletion
        function delete(app)

            % Delete UIFigure when app is deleted
            delete(app.OCTAVAUIFigure)
        end
    end
end