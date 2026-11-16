-- One row per month, MODIS and VIIRS side by side
CREATE OR REPLACE VIEW v_monthly_wide AS
SELECT `month`,
       MAX(CASE WHEN sensor = 'MODIS' THEN hotspots END) AS modis,
       MAX(CASE WHEN sensor = 'VIIRS' THEN hotspots END) AS viirs
FROM monthly_counts
GROUP BY `month`;

-- Months where both sensors observed, with the VIIRS-to-MODIS ratio
CREATE OR REPLACE VIEW v_overlap AS
SELECT `month`, modis, viirs, viirs / modis AS viirs_per_modis
FROM v_monthly_wide
WHERE modis IS NOT NULL AND viirs IS NOT NULL;

-- Two conversion ratios fitted on the overlap up to the end of 2023
CREATE OR REPLACE VIEW v_ratios AS
SELECT
  SUM(CASE WHEN viirs >= 1000 THEN modis END) / SUM(CASE WHEN viirs >= 1000 THEN viirs END) AS r_high,
  SUM(CASE WHEN viirs <  1000 THEN modis END) / SUM(CASE WHEN viirs <  1000 THEN viirs END) AS r_low
FROM v_overlap
WHERE `month` <= '2023-12-31';

-- Harmonized series: observed MODIS where it exists, converted VIIRS otherwise
CREATE OR REPLACE VIEW v_harmonized AS
SELECT w.`month`, w.modis, w.viirs,
       w.viirs * CASE WHEN w.viirs >= 1000 THEN r.r_high ELSE r.r_low END AS viirs_converted,
       COALESCE(w.modis, w.viirs * CASE WHEN w.viirs >= 1000 THEN r.r_high ELSE r.r_low END) AS harmonized,
       CASE WHEN w.modis IS NOT NULL THEN 'MODIS observed' ELSE 'VIIRS converted' END AS source
FROM v_monthly_wide w
CROSS JOIN v_ratios r;
