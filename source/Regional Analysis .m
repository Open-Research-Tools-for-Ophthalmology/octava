function regionalmetrics = regionalAnalysis(app)
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

                imgReg{1} = app.inputImage(1:regionsize(1),1:regionsize(2));
                imgReg{2}  = app.inputImage(1:regionsize(1),regionsize(2)+1:2*regionsize(2));
                imgReg{3} = app.inputImage(1:regionsize(1),2*regionsize(2)+1:3*regionsize(2));
                imgReg{4} = app.inputImage(regionsize(1)+1:2*regionsize(1),1:regionsize(2));
                imgReg{5}  = app.inputImage(regionsize(1)+1:2*regionsize(1),regionsize(2)+1:2*regionsize(2));
                imgReg{6} = app.inputImage(regionsize(1)+1:2*regionsize(1),2*regionsize(2)+1:3*regionsize(2));
                imgReg{7}  = app.inputImage(2*regionsize(1)+1:3*regionsize(1),1:regionsize(2));
                imgReg{8} = app.inputImage(2*regionsize(1)+1:3*regionsize(1),regionsize(2)+1:2*regionsize(2));
                imgReg{9}  = app.inputImage(2*regionsize(1)+1:3*regionsize(1),2*regionsize(2)+1:3*regionsize(2));
                
                %Prepare for metric generation
                imgArea_pix = regionsize(1)*regionsize(2);
                imgArea_mm = imgArea_pix*pix_to_mm^2;
                
                
                if strcmp(app.RL.Value,'Right Eye')
                    app.RAlabels = ["Supero-temporal" "Superior" "Supero-nasal" "Temporal" "Central" "Nasal" "Infero-temporal" "Inferior" "Infero-nasal"];
                else
                    app.RAlabels = ["Supero-nasal" "Superior" "Supero-temporal" "Nasal" "Central" "Temporal" "Infero-nasal" "Inferior" "Infero-temporal"];
                end
                
            elseif strcmp(grid_type,'ETDRS grid')
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
                
                foveal_mask = roi_1mm.createMask; %Foveal circle
                parafoveal_mask = roi_3mm.createMask-roi_1mm.createMask; %Parafoveal rim
                
                %Create a mask for each segment - start with assumption
                %of OS (right eye?) and swap labels after if needed...
                
                sector_masks = zeros(app.fullImSizePix(1), app.fullImSizePix(2), 6);
                
                for ii = 1:6
                    theta = linspace(0, -60, 1000)-60*(ii-1);
                    x_sector = [app.FAZ_ctr(1) rad_3mm*cosd(theta)+app.FAZ_ctr(1) app.FAZ_ctr(1)];
                    y_sector = [app.FAZ_ctr(2) rad_3mm*sind(theta)+app.FAZ_ctr(2) app.FAZ_ctr(2)];
                    plot(x_sector,y_sector,'LineWidth',2,"Color",'r')
                    %p=area(x_sector,y_sector);
                    mask = poly2mask(x_sector, y_sector,app.fullImSizePix(1),app.fullImSizePix(2));
                    sector_masks(:,:,ii) = (mask-foveal_mask) > 0;
                end
                drawnow
                close(fig)
                
                binaryReg{1} = app.BinaryImage.*foveal_mask; %foveal circle
                binaryReg{1} = binaryReg{1}(round(max(app.FAZ_ctr(1)-rad_3mm,1)):round(min(app.FAZ_ctr(1)+rad_3mm,app.fullImSizePix(1))), round(max(app.FAZ_ctr(2)-rad_3mm,1)):round(min(app.FAZ_ctr(2)+rad_3mm,app.fullImSizePix(2))));
                binaryReg{2} = app.BinaryImage.*parafoveal_mask; %Parafoveal rim
                binaryReg{3} = app.BinaryImage.*(sector_masks(:,:,1)+sector_masks(:,:,2)+sector_masks(:,:,3)); %superior hemi-parafoveal rim
                binaryReg{3} = binaryReg{3}(1:round(app.fullImSizePix(1)/2),:);
                binaryReg{4} = app.BinaryImage.*(sector_masks(:,:,4)+sector_masks(:,:,5)+sector_masks(:,:,6)); %inferior hemi-parafoveal rim
                binaryReg{4} = binaryReg{4}(round(app.fullImSizePix(1)/2+1):end,:);
                binaryReg{5} = app.BinaryImage.*(sector_masks(:,:,1)+sector_masks(:,:,6)); %tempo/nasal parafoveal rim
                binaryReg{5} = binaryReg{5}(:,round(app.fullImSizePix(1)/2+1):end);
                binaryReg{6} = app.BinaryImage.*(sector_masks(:,:,3)+sector_masks(:,:,4));%tempo/nasal parafoveal rim
                binaryReg{6} = binaryReg{6}(:,1:floor(app.fullImSizePix(1)/2));
                binaryReg{7} = app.BinaryImage.*sector_masks(:,:,2); %superior-parafoveal rim
                binaryReg{7} = binaryReg{7}(1:round(app.fullImSizePix(1)/2),:);
                binaryReg{8} = app.BinaryImage.*sector_masks(:,:,5); %inferior-parafoveal rim
                binaryReg{8} = binaryReg{8}(round(app.fullImSizePix(1)/2+1):end,:);

                imgReg{1} = app.inputImage.*foveal_mask; %foveal circle
                imgReg{1} = imgReg{1}(round(max(app.FAZ_ctr(1)-rad_3mm,1)):round(min(app.FAZ_ctr(1)+rad_3mm,app.fullImSizePix(1))), round(max(app.FAZ_ctr(2)-rad_3mm,1)):round(min(app.FAZ_ctr(2)+rad_3mm,app.fullImSizePix(2))));
                imgReg{2} = app.inputImage.*parafoveal_mask; %Parafoveal rim
                imgReg{3} = app.inputImage.*(sector_masks(:,:,1)+sector_masks(:,:,2)+sector_masks(:,:,3)); %superior hemi-parafoveal rim
                imgReg{3} = imgReg{3}(1:round(app.fullImSizePix(1)/2),:);
                imgReg{4} = app.inputImage.*(sector_masks(:,:,4)+sector_masks(:,:,5)+sector_masks(:,:,6)); %inferior hemi-parafoveal rim
                imgReg{4} = imgReg{4}(round(app.fullImSizePix(1)/2+1):end,:);
                imgReg{5} = app.inputImage.*(sector_masks(:,:,1)+sector_masks(:,:,6)); %tempo/nasal parafoveal rim
                imgReg{5} = imgReg{5}(:,round(app.fullImSizePix(1)/2+1):end);
                imgReg{6} = app.inputImage.*(sector_masks(:,:,3)+sector_masks(:,:,4));%tempo/nasal parafoveal rim
                imgReg{6} = imgReg{6}(:,1:floor(app.fullImSizePix(1)/2));
                imgReg{7} = app.inputImage.*sector_masks(:,:,2); %superior-parafoveal rim
                imgReg{7} = imgReg{7}(1:round(app.fullImSizePix(1)/2),:);
                imgReg{8} = app.inputImage.*sector_masks(:,:,5); %inferior-parafoveal rim
                imgReg{8} = imgReg{8}(round(app.fullImSizePix(1)/2+1):end,:);
                
                if strcmp(app.RL.Value,'Right Eye')
                    app.RAlabels = ["Foveal circle" "Parafoveal rim " "Superior hemi-parafoveal rim" "Inferior hemi-parafoveal rim" "Nasal parafoveal rim" "Tempo parafoveal rim" "Superior parafoveal rim" "Inferior parafoveal rim"];
                else
                    app.RAlabels = ["Foveal circle" "Parafoveal rim " "Superior hemi-parafoveal rim" "Inferior hemi-parafoveal rim" "Tempo parafoveal rim" "Nasal parafoveal rim" "Superior parafoveal rim" "Inferior parafoveal rim"];
                end
                
                imgArea_pix_vec = [sum(sum(foveal_mask)) sum(sum(parafoveal_mask)) sum(sum(sector_masks(:,:,1)+sector_masks(:,:,2)+sector_masks(:,:,3)))...
                    sum(sum(sector_masks(:,:,4)+sector_masks(:,:,5)+sector_masks(:,:,6))) sum(sum(sector_masks(:,:,1)+sector_masks(:,:,6))) sum(sum(sector_masks(:,:,3)+sector_masks(:,:,4)))...
                    sum(sum(sector_masks(:,:,2))) sum(sum(sector_masks(:,:,2)))]; %is the last one a bug? Repeated sector_masks(:,:,2)
            elseif strcmp(grid_type,'Extended ETDRS grid')  
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
                
                for ii = 1:8
                    theta = linspace(0, -45, 1000)-45*(ii-1);
                    x_sector = [app.FAZ_ctr(1) rad_3mm*cosd(theta)+app.FAZ_ctr(1) app.FAZ_ctr(1)];
                    y_sector = [app.FAZ_ctr(2) rad_3mm*sind(theta)+app.FAZ_ctr(2) app.FAZ_ctr(2)];
                    plot(x_sector,y_sector,'LineWidth',2,"Color",'r')
                    mask = poly2mask(x_sector, y_sector,app.fullImSizePix(1),app.fullImSizePix(2));
                    sector_masks(:,:,ii) = (mask-foveal_mask) > 0;
                end
                drawnow
                close(fig)
                
                %Regions include 8 45-degree wedges + Nasal and Temporal 90
                %degree wedges 
                
                binaryReg{1} = app.BinaryImage.*sector_masks(:,:,1);
                binaryReg{1} = binaryReg{1}(1:round(app.fullImSizePix(1)/2),round(app.fullImSizePix(1)/2):end);
                binaryReg{2} = app.BinaryImage.*sector_masks(:,:,2);
                binaryReg{2} = binaryReg{2}(1:round(app.fullImSizePix(1)/2),round(app.fullImSizePix(1)/2):end);
                binaryReg{3} = app.BinaryImage.*sector_masks(:,:,3);
                binaryReg{3} = binaryReg{3}(1:round(app.fullImSizePix(1)/2),1:round(app.fullImSizePix(1)/2));
                binaryReg{4} = app.BinaryImage.*sector_masks(:,:,4);
                binaryReg{4} = binaryReg{4}(1:round(app.fullImSizePix(1)/2),1:round(app.fullImSizePix(1)/2));
                binaryReg{5} = app.BinaryImage.*sector_masks(:,:,5);
                binaryReg{5} = binaryReg{5}(round(app.fullImSizePix(1)/2):end,1:round(app.fullImSizePix(1)/2));
                binaryReg{6} = app.BinaryImage.*sector_masks(:,:,6);
                binaryReg{6} = binaryReg{6}(round(app.fullImSizePix(1)/2):end,1:round(app.fullImSizePix(1)/2));
                binaryReg{7} = app.BinaryImage.*sector_masks(:,:,7);
                binaryReg{7} = binaryReg{7}(round(app.fullImSizePix(1)/2):end,round(app.fullImSizePix(1)/2):end);
                binaryReg{8} = app.BinaryImage.*sector_masks(:,:,8);
                binaryReg{8} = binaryReg{8}(round(app.fullImSizePix(1)/2):end,round(app.fullImSizePix(1)/2):end);
                binaryReg{9} = app.BinaryImage.*(sector_masks(:,:,1)+sector_masks(:,:,8));
                binaryReg{9} = binaryReg{9}(:,round(app.fullImSizePix(1)/2):end);
                binaryReg{10} = app.BinaryImage.*(sector_masks(:,:,4)+sector_masks(:,:,5));
                binaryReg{10} = binaryReg{10}(:,1:round(app.fullImSizePix(1)/2));

                imgReg{1} = app.inputImage.*sector_masks(:,:,1);
                imgReg{1} = imgReg{1}(1:round(app.fullImSizePix(1)/2),round(app.fullImSizePix(1)/2):end);
                imgReg{2} = app.inputImage.*sector_masks(:,:,2);
                imgReg{2} = imgReg{2}(1:round(app.fullImSizePix(1)/2),round(app.fullImSizePix(1)/2):end);
                imgReg{3} = app.inputImage.*sector_masks(:,:,3);
                imgReg{3} = imgReg{3}(1:round(app.fullImSizePix(1)/2),1:round(app.fullImSizePix(1)/2));
                imgReg{4} = app.inputImage.*sector_masks(:,:,4);
                imgReg{4} = imgReg{4}(1:round(app.fullImSizePix(1)/2),1:round(app.fullImSizePix(1)/2));
                imgReg{5} = app.inputImage.*sector_masks(:,:,5);
                imgReg{5} = imgReg{5}(round(app.fullImSizePix(1)/2):end,1:round(app.fullImSizePix(1)/2));
                imgReg{6} = app.inputImage.*sector_masks(:,:,6);
                imgReg{6} = imgReg{6}(round(app.fullImSizePix(1)/2):end,1:round(app.fullImSizePix(1)/2));
                imgReg{7} = app.inputImage.*sector_masks(:,:,7);
                imgReg{7} = imgReg{7}(round(app.fullImSizePix(1)/2):end,round(app.fullImSizePix(1)/2):end);
                imgReg{8} = app.inputImage.*sector_masks(:,:,8);
                imgReg{8} = imgReg{8}(round(app.fullImSizePix(1)/2):end,round(app.fullImSizePix(1)/2):end);
                imgReg{9} = app.inputImage.*(sector_masks(:,:,1)+sector_masks(:,:,8));
                imgReg{9} = imgReg{9}(:,round(app.fullImSizePix(1)/2):end);
                imgReg{10} = app.inputImage.*(sector_masks(:,:,4)+sector_masks(:,:,5));
                imgReg{10} = imgReg{10}(:,1:round(app.fullImSizePix(1)/2));

                if strcmp(app.RL.Value,'Right Eye')
                    app.RAlabels = ["Super nasal" "Nasal superior" "Temporal superior" "Super temporal" "Inferio temporal" "Temporal inferior" "Nasal inferior" "Inferio nasal" "Nasal wedge" "Temporal wedge"];
                else
                    app.RAlabels = ["Super temporal" "Temporal superior" "Nasal superior" "Super nasal" "Inferio nasal" "Nasal inferior" "Temporal inferior" "Inferio temporal" "Temporal wedge" "Nasal wedge"];
                end

                imgArea_pix_vec = [sum(sector_masks(:,:,1),'all') sum(sector_masks(:,:,2),'all') sum(sector_masks(:,:,3),'all') sum(sector_masks(:,:,4),'all') sum(sector_masks(:,:,5),'all')...
                    sum(sector_masks(:,:,6),'all') sum(sector_masks(:,:,7),'all') sum(sector_masks(:,:,8),'all') sum(sector_masks(:,:,1)+sector_masks(:,:,8),'all') sum(sector_masks(:,:,4)+sector_masks(:,:,5),'all')];
                
                grid_type = 'Extended';

            elseif strcmp(grid_type,'Optic nerve head [BETA]')  
                %Calculate each ring radius in pixels
                rad_1mm = 1*app.fullImSizePix(1)/app.RealImageSizemm.Value;%Inner excluded ring is 2 mm in diameter
                rad_outer = 2*app.fullImSizePix(1)/app.RealImageSizemm.Value; %The outer ring may need to be 2.5, 3, or 4.25 - The user will need to input this 


                %Setup to save figure so contour can be checked later
                fol = fullfile(app.SaveFolder,'images');
                if ~exist(fol, 'dir')
                    mkdir(fol)
                    imgnum = 0;
                else
                    list = dir(fullfile(fol, '*ONH_Countour*.png'));
                    imgnum = length(list);
                end
                
                savename_ONH = fullfile(fol,[app.FileLabelName '_ONH_Countour_' num2str(imgnum) '.png']);

                
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
                
                roi_1mm = images.roi.Circle(gca,"Center",app.FAZ_ctr,"Radius",rad_1mm,"LineWidth",2,"Color",'y',"FaceAlpha",0);
                roi_outer = images.roi.Circle(gca,"Center",app.FAZ_ctr,"Radius",rad_outer, "LineWidth",2,"Color",'r',"FaceAlpha",0);

                ONH_mask_inner = roi_1mm.createMask;
                PP_mask = roi_outer.createMask-roi_1mm.createMask; %Peripapaillary

                %Save image with rings 
                axis off
                export_fig(fig,savename_ONH)

                %Need to make 8 sectors, similar to EDTRS grid 
                sector_masks = zeros(app.fullImSizePix(1), app.fullImSizePix(2), 6);
                
                for ii = 1:8
                    theta = linspace(0, -45, 1000)-45*(ii-1);
                    x_sector = [app.FAZ_ctr(1) rad_outer*cosd(theta)+app.FAZ_ctr(1) app.FAZ_ctr(1)];
                    y_sector = [app.FAZ_ctr(2) rad_outer*sind(theta)+app.FAZ_ctr(2) app.FAZ_ctr(2)];
                    plot(x_sector,y_sector,'LineWidth',2,"Color",'r')
                    mask = poly2mask(x_sector, y_sector,app.fullImSizePix(1),app.fullImSizePix(2));
                    sector_masks(:,:,ii) = (mask-ONH_mask_inner) > 0;
                end
                drawnow
                close(fig)

                %Define regions - each for 8 45 degree wedges on its own +
                %extra = 14 total + peripaillary defined above 
                %regions 

                binaryReg{1} = app.BinaryImage.*sector_masks(:,:,1); %TS
                binaryReg{1} = binaryReg{1}(1:round(app.fullImSizePix(1)/2),round(app.fullImSizePix(1)/2):end);
                binaryReg{2} = app.BinaryImage.*sector_masks(:,:,2); %ST
                binaryReg{2} = binaryReg{2}(1:round(app.fullImSizePix(1)/2),round(app.fullImSizePix(1)/2):end);
                binaryReg{3} = app.BinaryImage.*sector_masks(:,:,3); %SN
                binaryReg{3} = binaryReg{3}(1:round(app.fullImSizePix(1)/2),1:round(app.fullImSizePix(1)/2));
                binaryReg{4} = app.BinaryImage.*sector_masks(:,:,4); %NS
                binaryReg{4} = binaryReg{4}(1:round(app.fullImSizePix(1)/2),1:round(app.fullImSizePix(1)/2));
                binaryReg{5} = app.BinaryImage.*sector_masks(:,:,5); %NI
                binaryReg{5} = binaryReg{5}(round(app.fullImSizePix(1)/2):end,1:round(app.fullImSizePix(1)/2));
                binaryReg{6} = app.BinaryImage.*sector_masks(:,:,6); %IN
                binaryReg{6} = binaryReg{6}(round(app.fullImSizePix(1)/2):end,1:round(app.fullImSizePix(1)/2));
                binaryReg{7} = app.BinaryImage.*sector_masks(:,:,7); %IT
                binaryReg{7} = binaryReg{7}(round(app.fullImSizePix(1)/2):end,round(app.fullImSizePix(1)/2):end);
                binaryReg{8} = app.BinaryImage.*sector_masks(:,:,8); % TI
                binaryReg{8} = binaryReg{8}(round(app.fullImSizePix(1)/2):end,round(app.fullImSizePix(1)/2):end);
                binaryReg{9} = app.BinaryImage.*(sector_masks(:,:,1)+sector_masks(:,:,2)+sector_masks(:,:,3)+sector_masks(:,:,4)); %S_hemi
                binaryReg{9} = binaryReg{9}(1:round(app.fullImSizePix(1)/2),:);
                binaryReg{10} = app.BinaryImage.*(sector_masks(:,:,5)+sector_masks(:,:,6)+sector_masks(:,:,7)+sector_masks(:,:,8)); %I_Hemi
                binaryReg{10} = binaryReg{10}(round(app.fullImSizePix(1)/2):end,:);
                binaryReg{11} = app.BinaryImage.*(sector_masks(:,:,2)+sector_masks(:,:,3)); %S
                binaryReg{11} = binaryReg{11}(1:round(app.fullImSizePix(1)/2),:);
                binaryReg{12} = app.BinaryImage.*(sector_masks(:,:,6)+sector_masks(:,:,7)); %I
                binaryReg{12} = binaryReg{12}(round(app.fullImSizePix(1)/2):end,:);
                binaryReg{13} = app.BinaryImage.*(sector_masks(:,:,4)+sector_masks(:,:,5)); %N
                binaryReg{13} = binaryReg{13}(:,1:round(app.fullImSizePix(1)/2));
                binaryReg{14} = app.BinaryImage.*(sector_masks(:,:,1)+sector_masks(:,:,8)); %T
                binaryReg{14} = binaryReg{14}(:,round(app.fullImSizePix(1)/2):end);
                binaryReg{15} = app.BinaryImage.*PP_mask; %PP
                

                imgReg{1} = app.inputImage.*sector_masks(:,:,1);
                imgReg{1} = imgReg{1}(1:round(app.fullImSizePix(1)/2),round(app.fullImSizePix(1)/2):end);
                imgReg{2} = app.inputImage.*sector_masks(:,:,2);
                imgReg{2} = imgReg{2}(1:round(app.fullImSizePix(1)/2),round(app.fullImSizePix(1)/2):end);
                imgReg{3} = app.inputImage.*sector_masks(:,:,3);
                imgReg{3} = imgReg{3}(1:round(app.fullImSizePix(1)/2),1:round(app.fullImSizePix(1)/2));
                imgReg{4} = app.inputImage.*sector_masks(:,:,4);
                imgReg{4} = imgReg{4}(1:round(app.fullImSizePix(1)/2),1:round(app.fullImSizePix(1)/2));
                imgReg{5} = app.inputImage.*sector_masks(:,:,5);
                imgReg{5} = imgReg{5}(round(app.fullImSizePix(1)/2):end,1:round(app.fullImSizePix(1)/2));
                imgReg{6} = app.inputImage.*sector_masks(:,:,6);
                imgReg{6} = imgReg{6}(round(app.fullImSizePix(1)/2):end,1:round(app.fullImSizePix(1)/2));
                imgReg{7} = app.inputImage.*sector_masks(:,:,7);
                imgReg{7} = imgReg{7}(round(app.fullImSizePix(1)/2):end,round(app.fullImSizePix(1)/2):end);
                imgReg{8} = app.inputImage.*sector_masks(:,:,8);
                imgReg{8} = imgReg{8}(round(app.fullImSizePix(1)/2):end,round(app.fullImSizePix(1)/2):end);
                imgReg{9} = app.inputImage.*(sector_masks(:,:,1)+sector_masks(:,:,2)+sector_masks(:,:,3)+sector_masks(:,:,4));
                imgReg{9} = imgReg{9}(1:round(app.fullImSizePix(1)/2),:);
                imgReg{10} = app.inputImage.*(sector_masks(:,:,5)+sector_masks(:,:,6)+sector_masks(:,:,7)+sector_masks(:,:,8));
                imgReg{10} = imgReg{10}(round(app.fullImSizePix(1)/2):end,:);
                imgReg{11} = app.inputImage.*(sector_masks(:,:,2)+sector_masks(:,:,3));
                imgReg{11} = imgReg{11}(1:round(app.fullImSizePix(1)/2),:);
                imgReg{12} = app.inputImage.*(sector_masks(:,:,6)+sector_masks(:,:,7));
                imgReg{12} = imgReg{12}(round(app.fullImSizePix(1)/2):end,:);
                imgReg{13} = app.inputImage.*(sector_masks(:,:,4)+sector_masks(:,:,5));
                imgReg{13} = imgReg{13}(:,1:round(app.fullImSizePix(1)/2));
                imgReg{14} = app.inputImage.*(sector_masks(:,:,1)+sector_masks(:,:,8));
                imgReg{14} = imgReg{14}(:,round(app.fullImSizePix(1)/2):end);
                imgReg{15} = app.inputImage.*PP_mask;
                
                

                
                if strcmp(app.RL.Value,'Right Eye')
                    app.RAlabels = ["NS" "SN" "ST" "TS" "TI" "IT" "IN" "NI" "S_hemi" "I_Hemi" "S" "I" "T" "N" "PP"];
                else
                    app.RAlabels = ["TS" "ST" "SN" "NS" "NI" "IN" "IT" "TI" "S_hemi" "I_Hemi" "S" "I" "N" "T" "PP"];
                end

                imgArea_pix_vec = [sum(sector_masks(:,:,1),'all') sum(sector_masks(:,:,2),'all') sum(sector_masks(:,:,3),'all') sum(sector_masks(:,:,4),'all') sum(sector_masks(:,:,5),'all')...
                    sum(sector_masks(:,:,6),'all') sum(sector_masks(:,:,7),'all') sum(sector_masks(:,:,8),'all') sum(sector_masks(:,:,1)+sector_masks(:,:,2)+sector_masks(:,:,3)+sector_masks(:,:,4),'all')...
                    sum(sector_masks(:,:,5)+sector_masks(:,:,6)+sector_masks(:,:,7)+sector_masks(:,:,8),'all') sum(sector_masks(:,:,2)+sector_masks(:,:,3),'all') sum(sector_masks(:,:,6)+sector_masks(:,:,7),'all')...
                    sum(sector_masks(:,:,4)+sector_masks(:,:,5),'all') sum(sector_masks(:,:,1)+sector_masks(:,:,8),'all') sum(PP_mask,'all')];
               
                grid_type = 'ONH'; %This will need to be updated to append the outer ring diameter 



            else %Foveal rings 
                %Calculate each ring radius in pixels
                rad_1mm = .5*app.fullImSizePix(1)/app.RealImageSizemm.Value;
                rad_2mm = 1*app.fullImSizePix(1)/app.RealImageSizemm.Value;
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
                roi_2mm = images.roi.Circle(gca,"Center",app.FAZ_ctr,"Radius",rad_2mm,"LineWidth",2,"Color",'y');
                roi_3mm = images.roi.Circle(gca,"Center",app.FAZ_ctr,"Radius",rad_3mm,"LineWidth",2,"Color",'y');

                foveal_mask = roi_1mm.createMask;
                pf500_mask = roi_2mm.createMask-roi_1mm.createMask;
                pfouter_mask = roi_3mm.createMask-roi_2mm.createMask;

                binaryReg{1} = app.BinaryImage.*foveal_mask; %foveal circle
                binaryReg{1} = binaryReg{1}(round(max(app.FAZ_ctr(1)-rad_3mm,1)):round(min(app.FAZ_ctr(1)+rad_3mm,app.fullImSizePix(1))), round(max(app.FAZ_ctr(2)-rad_3mm,1)):round(min(app.FAZ_ctr(2)+rad_3mm,app.fullImSizePix(2))));
                binaryReg{2} = app.BinaryImage.*pf500_mask; % 0.5 mm ring around FAZ 
                binaryReg{2} = binaryReg{2}(round(max(app.FAZ_ctr(1)-rad_3mm,1)):round(min(app.FAZ_ctr(1)+rad_3mm,app.fullImSizePix(1))), round(max(app.FAZ_ctr(2)-rad_3mm,1)):round(min(app.FAZ_ctr(2)+rad_3mm,app.fullImSizePix(2))));
                binaryReg{3} = app.BinaryImage.*pfouter_mask; %Outer 0.5 mm ring of 3mm circle around FAZ center 

                imgReg{1} = app.inputImage.*foveal_mask; %foveal circle
                imgReg{1} = imgReg{1}(round(max(app.FAZ_ctr(1)-rad_3mm,1)):round(min(app.FAZ_ctr(1)+rad_3mm,app.fullImSizePix(1))), round(max(app.FAZ_ctr(2)-rad_3mm,1)):round(min(app.FAZ_ctr(2)+rad_3mm,app.fullImSizePix(2))));
                imgReg{2} = app.inputImage.*pf500_mask; % 0.5 mm ring around FAZ 
                imgReg{2} = imgReg{2}(round(max(app.FAZ_ctr(1)-rad_3mm,1)):round(min(app.FAZ_ctr(1)+rad_3mm,app.fullImSizePix(1))), round(max(app.FAZ_ctr(2)-rad_3mm,1)):round(min(app.FAZ_ctr(2)+rad_3mm,app.fullImSizePix(2))));
                imgReg{3} = app.inputImage.*pfouter_mask; %Outer 0.5 mm ring of 3mm circle around FAZ center 

                app.RAlabels = ["FAZ circle" "Inner 0.5mm ring around FAZ" "Outer 0.5mm ring"];
                
                imgArea_pix_vec = [sum(foveal_mask,'all') sum(pf500_mask,'all') sum(pfouter_mask ,'all') ];
            
            end
            
            %Run metrics generation for each of the regions seperately
            for i = 1:size(binaryReg,2)
                skeletonize(app, imgReg{i}, binaryReg{i}, fol, 0);
                
                if ~strcmp(grid_type,'Square grid')
                    imgArea_pix = imgArea_pix_vec(i);
                    imgArea_mm = imgArea_pix *pix_to_mm^2;
                end
                regionalmetrics(i).Region = app.RAlabels(i);
                

                
                if ~isempty(app.Glinks) 
                    regionalmetrics(i).nodes = sum(~[app.Gnodes.ep]);
                    regionalmetrics(i).VAD = round(sum(sum(binaryReg{i}))/255/imgArea_pix,4)*100;
                    regionalmetrics(i).totalLength = round(sum([app.Glinks.pixLength]*pix_to_mm),2); %In mm
                    regionalmetrics(i).VLD_pct = round(regionalmetrics(i).totalLength*pix_to_mm/imgArea_mm,4)*100; %in percent %? seem to be a bug
                    regionalmetrics(i).VLD_mminv = round(regionalmetrics(i).totalLength/imgArea_mm,4); %in inverse mm
                    regionalmetrics(i).MeanLength = round(mean([app.Glinks.pixLength]*pix_to_mm*1000)); %in microns
                    regionalmetrics(i).MedianLength = round(median([app.Glinks.pixLength]*pix_to_mm*1000)); %in microns
                    
                    regionalmetrics(i).MeanDiam = round(mean([app.Glinks.diameter]*pix_to_mm*1000)); %In microns
                    regionalmetrics(i).MedianDiam = round(median([app.Glinks.diameter]*pix_to_mm*1000));
                    regionalmetrics(i).BD = round(regionalmetrics(i).nodes./regionalmetrics(i).totalLength,2); %in 1/mm
                    slope = fractalDimension(app);
                    regionalmetrics(i).FD = round(slope,4);
                    tortuosity = [app.Glinks.tortuosity];
                    regionalmetrics(i).mTort = round(mean(tortuosity(~isinf(tortuosity))),4);
                else
                    regionalmetrics(i).nodes = 0;
                    regionalmetrics(i).VAD = round(sum(sum(binaryReg{i}))/255/imgArea_pix,4)*100;
                    regionalmetrics(i).totalLength = 0;
                    regionalmetrics(i).VLD_pct = 0;
                    regionalmetrics(i).VLD_mminv = 0;
                    regionalmetrics(i).MeanLength = 0;
                    regionalmetrics(i).MedianLength = 0;
                    regionalmetrics(i).MeanDiam = 0;
                    regionalmetrics(i).MedianDiam = 0;
                    regionalmetrics(i).BD = 0;
                    slope = fractalDimension(app);
                    regionalmetrics(i).FD = round(slope,4);
                    regionalmetrics(i).mTort = 0;
                end



            end
            
            %Save Excel file with results summary
            datatable = struct2table(regionalmetrics);
            ExcelFilename = fullfile(app.SaveFolder, [app.FileLabelName '_' app.datanum' '.xlsx']);
            writetable(datatable,ExcelFilename, 'Sheet', ['Regional analysis_' grid_type]);
            
        end