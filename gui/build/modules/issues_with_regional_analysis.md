# Issues with regional analysis

## 1. ETDRS Grid area pixels calculation
In the following Matlab code, `sum(sum(sector_masks(:,:,2)))` is repeated twice at the end when creating the regional pixel vector.
```matlab
imgArea_pix_vec = [sum(sum(foveal_mask)) sum(sum(parafoveal_mask)) sum(sum(sector_masks(:,:,1)+sector_masks(:,:,2)+sector_masks(:,:,3)))...
                    sum(sum(sector_masks(:,:,4)+sector_masks(:,:,5)+sector_masks(:,:,6))) sum(sum(sector_masks(:,:,1)+sector_masks(:,:,6))) sum(sum(sector_masks(:,:,3)+sector_masks(:,:,4)))...
                    sum(sum(sector_masks(:,:,2))) sum(sum(sector_masks(:,:,2)))];
```

Is it supposed to be `sum(sum(sector_masks(:,:,5)))` based on the binary region division?

## 2. Double "pix_to_mm" multiplication when computing VLD_pct
`pix_to_mm` was multiplied when computing VLD_pct, however, it was multiplied when calculating totalLength too. VLD_pct is equivalent to `round(sum([app.Glinks.pixLength]*pix_to_mm)*pix_to_mm/imgArea_mm,4)*100`
```matlab
regionalmetrics(i).totalLength = round(sum([app.Glinks.pixLength]*pix_to_mm),2); %In mm
regionalmetrics(i).VLD_pct = round(regionalmetrics(i).totalLength*pix_to_mm/imgArea_mm,4)*100; %in percent
regionalmetrics(i).VLD_mminv = round(regionalmetrics(i).totalLength/imgArea_mm,4); %in inverse mm
```

What should the formula of calculating VLD_pct be?


## 3. Cropping vs area mismatch
In Matlab ETDRS and Foveal-ring grid types, we crop some regions.


When we crop a region, should we crop the mask used for the area too?

