function [metrics meanMetrics] = tort_metrics_new(links)
    nLinks = length(links);

    metrics = struct('AOC',nan,'TSC',nan,'TSCN',nan,'tortDensity',nan,'DT',nan,'PWAOC',nan, 'ISR',nan, 'SOAM',nan,'tortAngle',nan,'VCI1',nan,'VCI2',nan);

    plotOn = 0;

    pix2mm = 3/1000;
    %I need to figure out how to properly convert to real units! I am not
    %sure that I understand the units on all the curvature-based metrics 

    for i = 1:nLinks
        %% Preparations 
        vesselX = links(i).x.*pix2mm;
        vesselY = links(i).y*pix2mm;
        numPoints = length(vesselX);

        % ax = linspace(0,3,1000);
        % ay = linspace(0,3,1000);

        %Calculate vessel lengths 
        ds = sqrt(diff(vesselX).^2 + diff(vesselY).^2);
        arcLength = sum(ds);
        chordLength = sqrt((vesselX(end) - vesselX(1))^2 + (vesselY(end) - vesselY(1))^2);
        %arcLength_mm =  arcLength*pix2mm;


        %Need to smooth between each differentiation step to avoid
        %artefacts from the fact that we have discrete curves 
        windowSize = 10; 
        smoothedX = smoothdata(vesselX, 'movmean', windowSize);
        smoothedY = smoothdata(vesselY, 'movmean', windowSize);

        %Calculate curvature based on finite differences 
        %first and second derivatives
        dx = gradient(smoothedX);
        dy = gradient(smoothedY);
        dx = smoothdata(dx, 'movmean', windowSize);
        dy = smoothdata(dy, 'movmean', windowSize);

        ddx = gradient(dx);
        ddy = gradient(dy);
        ddx = smoothdata(ddx, 'movmean', windowSize);
        ddy = smoothdata(ddy, 'movmean', windowSize);

        % Compute curvature 
        %? curvature = dx .* ddy - ddx .* dy ./ ((dx.^2 + dy.^2).^(3/2) + eps);
        curvature = (dx .* ddy - ddx .* dy) ./ ((dx.^2 + dy.^2).^(3/2) + eps);  
        curvature = smoothdata(curvature, 'movmean', windowSize);

        %find inflection points 
        signCurv   = sign(curvature);
        inflecIdx  = find(diff(signCurv) ~= 0);
        nSeg       = length(inflecIdx) + 1; %Number of segments 
        

        %find local extrema
        %Find angle between the vessel and a horzontal line 
        x = 1:numPoints;
        v1 = [vesselY(end) - vesselY(1),vesselX(end) - vesselX(1)];
        v2 = [x(end) - x(1), 0];
        angle = acos(dot(v1, v2) / (norm(v1)*norm(v2) + eps));
        vessel = [smoothedY', smoothedX'];
        vesselSlope = sign(v1(2));
        vessel_rot = vessel*[cos(vesselSlope*angle) -sin(vesselSlope*angle); sin(vesselSlope*angle) cos(vesselSlope*angle)];
        vessel_rot = vessel_rot(:,2);
        %Differentiate and smooth 
        gradCurv = gradient(vessel_rot);
        gradCurv = smoothdata(gradCurv, 'movmean', windowSize);
        %Find zeros of the first derivative of the vessel shape
        signGradCurv = sign(gradCurv);
        extremaIdx  = find(diff(signGradCurv) ~= 0); 
        

        %Check minimum extrema extent is >3 pixels 
        testY = diff(vesselY(extremaIdx));
        testX = diff(vesselX(extremaIdx));
        trueExtrema = [];
        if length(extremaIdx)>=1
            trueExtrema = extremaIdx(1);
            thr = 3*pix2mm;
            for kk = 2:length(extremaIdx)
                if (abs(testY(kk-1))>thr && abs(testX(kk-1))>thr) || ((abs(testY(kk-1))>thr || abs(testX(kk-1))>thr)&& (extremaIdx(kk) - extremaIdx(kk-1)>100))
                    %NOTE: there are some hardcoded numbers here that may need
                    %to be checked! 
                    trueExtrema = [trueExtrema extremaIdx(kk)];
                end
                
            end
            nExtrema = length(trueExtrema);
            nExtrema(nExtrema <1) = 1; %Minimum value should be 1 
        else
            nExtrema = 1;
        end


        % If I want to, I can plot the infelction points an extrema 
        if plotOn == 1
            figure(1); 
            hold on 
            plot(vesselY(inflecIdx)/pix2mm,vesselX(inflecIdx)/pix2mm,'.r','MarkerSize',10)
            plot(vesselY(trueExtrema)/pix2mm,vesselX(trueExtrema)/pix2mm,'.r','MarkerSize',10,'Color',[0.7 0 1])
            drawnow
        end
       

        %% 1. Arc over chord length ratio 
        if chordLength == 0
            metrics(i).AOC = NaN;
        else
            metrics(i).AOC = arcLength / chordLength;
        end


        %% 2. Total squared curvature 
        metrics(i).TSC = sum( curvature(2:end-1).^2 .* ds(2:end) ); %why cut off first point? 

        %% 3. Normalized total squared curvature 
        metrics(i).TSCN = sum( curvature(2:end-1).^2 .* ds(2:end)./arcLength); %why cut off first point? 

        %% 4. Tortuosity density 
        segAOCs    = [];
        segArcs  = [];
        segStart   = 1;


        for k = 1:nSeg
            if k <= length(inflecIdx)
                segEnd = inflecIdx(k);
            else
                segEnd = length(vesselX);
            end
        
            % --- Arc length (s(Ci)) ---
            segArc = sum( sqrt( diff(vesselX(segStart:segEnd)).^2 + ...
                                diff(vesselY(segStart:segEnd)).^2 ) );
        
            % --- Chord length (chord(Ci)) ---
            segChord = sqrt( (vesselX(segEnd) - vesselX(segStart))^2 + ...
                             (vesselY(segEnd) - vesselY(segStart))^2 );
        
            % --- Arc-over-chord ratio ---
            if segChord == 0
                segAOC_val = NaN;
            else
                segAOC_val = segArc / segChord;
            end

             % --- Save values ---
            segAOCs   = [segAOCs; segAOC_val];
            segArcs = [segArcs; segArc];

            % Go to next segment
            segStart = segEnd;          
        end

        if nSeg > 1 && arcLength > 0
            metrics(i).tortDensity = ((nSeg - 1)/nSeg) * ( sum(segAOCs - 1) / arcLength );
        else
            metrics(i).tortDensity = segAOCs; %check this 
        end

        %% 5. Distance tortuosity 
        % We already have the AOC for each segment from the previous
        % calculation 
        metrics(i).DT = nansum(segAOCs .* segArcs) / arcLength;
        
        %%! 6. Peak-weighted AOC
        metrics(i).PWAOC = metrics(i).AOC*nExtrema;

        %% 7. Inverse spherical radius 
        metrics(i).ISR = sum(abs(curvature))/numPoints;

        %%! 8. Sum of angles metric 
        % This implementation computes the turning angle (in radians) at each interior point
        % of the vessel and weights the angle by the average length of the two adjoining segments.
        numPoints = length(vesselX);
        if numPoints < 3
            %? SOAM(i) = 0;  % Not enough points to compute an angle.
            metrics(i).SOAM = 0; % Not enough points to compute an angle.
        else
            totalWeightedAngle = 0;
            totalWeight = 0;
            for j = 2:numPoints-1
                % Define vectors for the segments before and after point j
                v1 = [vesselX(j) - vesselX(j-1), vesselY(j) - vesselY(j-1)];
                v2 = [vesselX(j+1) - vesselX(j), vesselY(j+1) - vesselY(j)];
                
                % Compute the cosine of the turning angle, using a small epsilon to avoid division by zero
                cosTheta = dot(v1, v2) / (norm(v1)*norm(v2) + eps);
                % Clamp the value to [-1,1] to avoid numerical issues
                cosTheta = max(min(cosTheta, 1), -1);
                % Calculate the turning angle in radians
                angleRad = acos(cosTheta);
                
                totalWeightedAngle = totalWeightedAngle + angleRad;
            end
            % Compute the weighted average turning angle (radians per unit length)
            metrics(i).SOAM = totalWeightedAngle / arcLength;
        end
        
        %% 9. Modified sum of angles metric 

        segStart   = 1;
        angleRads = [];

         for k = 1:nSeg
            if k <= length(inflecIdx)
                segEnd = inflecIdx(k);
            else
                segEnd = length(vesselX);
            end

            %Define vectors around midpoint of the vessel segment
            midpointIndex = round((segEnd-segStart)/2)+segStart;
            v1 = [vesselX(midpointIndex) - vesselX(segStart), vesselY(midpointIndex) - vesselY(segStart)];
            v2 = [vesselX(segEnd) - vesselX(midpointIndex), vesselY(segEnd) - vesselY(midpointIndex)];


            % Compute the cosine of the turning angle, using a small epsilon to avoid division by zero
            cosTheta = dot(v1, v2) / (norm(v1)*norm(v2) + eps);
            % Clamp the value to [-1,1] to avoid numerical issues
            cosTheta = max(min(cosTheta, 1), -1);
            % Calculate the turning angle in radians
            angleRads(k) = acos(cosTheta);
         end

         metrics(i).tortAngle = sum(angleRads'.*segArcs)/nSeg;

         %% 10. Vessel curvature index - M&M method 

         windowSize = 4; 
            
            smoothedX = smoothdata(vesselX, 'movmean', windowSize);
            smoothedY = smoothdata(vesselY, 'movmean', windowSize);
    
            dx = diff(smoothedX);
            dy = diff(smoothedY);

            ds = sqrt(dx.^2 + dy.^2);  % local arc-length increments
            if length(ds) > 1
                arcLength = sum(ds);
    
                % Compute tangent angles for each segment (midpoints)
                theta = atan2(dy, dx);
                
                % Using central difference to estimate local derivative of theta
                dtheta = zeros(size(theta));
    
                for j = 2:length(theta)-1
                    dtheta(j) = (theta(j+1) - theta(j-1)) / (ds(j) + ds(j-1));
                end
    
                % For endpoints, you can use forward/backward differences
    
                dtheta(1) = (theta(2) - theta(1)) / ds(1);
                dtheta(end) = (theta(end) - theta(end-1)) / ds(end-1);
                
                % Local curvature magnitude (kappa) is given by |dtheta/ds|
    
                kappa = abs(dtheta);
                window = 4;  % for example, use 5 points around the current point
                nPoints = length(smoothedX);
                L_local = zeros(1, nPoints);
    
                for j = 1:nPoints
                    % Determine indices for a local window; use boundaries appropriately.
                    idxStart = max(1, j - floor(window/2));
                    idxEnd = min(nPoints, j + floor(window/2));
                    localCentroidX = mean(smoothedX(idxStart:idxEnd));
                    localCentroidY = mean(smoothedY(idxStart:idxEnd));
                    r_local = sqrt((smoothedX(j) - localCentroidX)^2 + (smoothedY(j) - localCentroidY)^2);
                    L_local(j) = r_local^2;
                end
    
                dL_local = abs(diff(L_local));
    
                % Use robust finite differences; you might also compute a moving average of dL_local.
    
                total_dL = sum(dL_local);
    
                VCI_value = total_dL / arcLength;
                robust_dL = trimmean(dL_local, 10);  % remove the top 10% outliers
                VCI_value_robust = robust_dL / (arcLength / length(dL_local));  
                % This divides by average ds rather than total arc length if preferred.
    
    
                metrics(i).VCI1 = VCI_value_robust;

            else 
                 metrics(i).VCI1 = NaN;

            end

            %% VCI my method 
            t = gradient(1./curvature); 
            t(t==inf) = nan;
            t(t==-inf) = nan;
            metrics(i).VCI2 = nansum(t)/numPoints; % average rate of change of curvature radius

            %% Save mean and STD of all metrics 
            % Package all metrics into a structure for output.
            meanMetrics.AOCmean = nanmean([metrics.AOC]);
            meanMetrics.AOCstd = nanstd([metrics.AOC]);

            meanMetrics.TSCmean = nanmean([metrics.TSC]);
            meanMetrics.TSCstd = nanstd([metrics.TSC]);

            meanMetrics.TSCNmean = nanmean([metrics.TSCN]);
            meanMetrics.TSCNstd = nanstd([metrics.TSCN]);

            meanMetrics.tortDensitymean = nanmean([metrics.tortDensity]);
            meanMetrics.tortDensitystd = nanstd([metrics.tortDensity]);

            meanMetrics.DTmean = nanmean([metrics.DT]);
            meanMetrics.DTstd = nanstd([metrics.DT]);

            meanMetrics.PWAOCmean = nanmean([metrics.PWAOC]);
            meanMetrics.PWAOCstd = nanstd([metrics.PWAOC]);

            meanMetrics.ISRmean = nanmean([metrics.ISR]);
            meanMetrics.ISRstd = nanstd([metrics.ISR]);

            meanMetrics.SOAMmean = nanmean([metrics.SOAM]);
            meanMetrics.SOAMstd = nanstd([metrics.SOAM]);

            meanMetrics.tortAnglemean = nanmean([metrics.tortAngle]);
            meanMetrics.tortAnglestd = nanstd([metrics.tortAngle]);

            meanMetrics.VCI1mean = nanmean([metrics.VCI1]);
            meanMetrics.VCI1std = nanstd([metrics.VCI1]);

            meanMetrics.VCI2mean = nanmean([metrics.VCI2]);
            meanMetrics.VCI2std = nanstd([metrics.VCI2]);
            
            


    end 