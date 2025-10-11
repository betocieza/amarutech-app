-- Script para actualizar sliders existentes con sort_order
-- Este script se ejecuta después de la migración 2dbea6e6d8f4

-- Actualizar sliders existentes que no tienen sort_order (serán NULL después de la migración)
UPDATE sliders 
SET sort_order = 0 
WHERE sort_order IS NULL;

-- Opcional: Asignar sort_order incremental basado en la fecha de creación
-- UPDATE sliders 
-- SET sort_order = (
--     SELECT ROW_NUMBER() OVER (ORDER BY created_at ASC)
--     FROM (SELECT slider_id, created_at FROM sliders) AS ranked
--     WHERE ranked.slider_id = sliders.slider_id
-- );

-- Verificar los resultados
-- SELECT slider_id, title, sort_order, created_at 
-- FROM sliders 
-- ORDER BY sort_order ASC, created_at DESC;