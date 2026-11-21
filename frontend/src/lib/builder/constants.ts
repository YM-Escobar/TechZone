import type { BuilderCategoryConfig } from './types';

export const BUILDER_CATEGORIES: BuilderCategoryConfig[] = [
  {
    value: 'cpu',
    label: 'Procesador',
    shortLabel: 'PROCESADOR',
    code: 'CPU',
    description: 'Define el rendimiento general y la capacidad de cálculo del equipo.',
  },
  {
    value: 'gpu',
    label: 'Tarjeta gráfica',
    shortLabel: 'TARJETA GRÁFICA',
    code: 'GPU',
    description: 'Determina el rendimiento gráfico para juegos, creación y tareas visuales.',
  },
  {
    value: 'placa_madre',
    label: 'Placa madre',
    shortLabel: 'PLACA MADRE',
    code: 'MB',
    description: 'Conecta los componentes y define qué procesadores y memoria admite el ensamble.',
  },
  {
    value: 'ram',
    label: 'Memoria RAM',
    shortLabel: 'MEMORIA RAM',
    code: 'RAM',
    description: 'Influye en la multitarea y debe coincidir con la plataforma seleccionada.',
  },
  {
    value: 'almacenamiento',
    label: 'Almacenamiento',
    shortLabel: 'ALMACENAMIENTO',
    code: 'SSD',
    description: 'Elige capacidad y velocidad para el sistema, las aplicaciones y tus archivos.',
  },
  {
    value: 'refrigeracion',
    label: 'Refrigeración',
    shortLabel: 'REFRIGERACIÓN',
    code: 'COOL',
    description: 'Ayuda a mantener temperaturas adecuadas según el procesador y el uso.',
  },
  {
    value: 'fuente',
    label: 'Fuente de poder',
    shortLabel: 'FUENTE DE PODER',
    code: 'PSU',
    description: 'Proporciona energía al equipo; considera la potencia y los conectores necesarios.',
  },
];

export const SINGLE_UNIT_CATEGORIES = new Set([
  'cpu',
  'placa_madre',
  'refrigeracion',
  'fuente',
]);

export const DEFAULT_BUILD_NAME = 'MI ENSAMBLE';
export const PRODUCT_PAGE_SIZE = 40;
