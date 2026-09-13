import { apiClient } from './client';

export const TRT35_CONFIGURATIONS = [
  { value: 'PAGE_11_UPPER_100_OUTRIGGER', label: '페이지 11 - 아웃트리거 100%' },
  { value: 'PAGE_11_LOWER_50_OUTRIGGER', label: '페이지 11 - 아웃트리거 50%' },
  { value: 'PAGE_12_UPPER_ON_TIRES_360_0_KMH', label: '페이지 12 - On Tires 360° / 0 km/h' },
  { value: 'PAGE_12_LOWER_ON_TIRES_0_MAX_2_KMH', label: '페이지 12 - On Tires 0° / 최대 2 km/h' },
  { value: 'PAGE_15_LEFT_LATTICE_JIB_8M_0_DEG', label: '페이지 15 - 격자 지브 8 m / 0°' },
  { value: 'PAGE_15_RIGHT_LATTICE_JIB_8M_20_DEG', label: '페이지 15 - 격자 지브 8 m / 20°' },
] as const;

export type Trt35Configuration = (typeof TRT35_CONFIGURATIONS)[number]['value'];
export type Trt35CellStatus = 'AVAILABLE' | 'NOT_AVAILABLE' | 'UNRESOLVED';

export interface Trt35CellResult {
  row_index: number;
  column_index: number;
  radius_m: number;
  boom_length_m: number;
  rated_capacity_t: number | null;
  cell_status: Trt35CellStatus;
  source_text: string | null;
  confidence: number | null;
  reason: string | null;
}

export interface Trt35ParseResult {
  source_page: number;
  table_segment: Trt35Configuration;
  grid_status: 'PASS' | 'TABLE_STRUCTURE_UNRESOLVED';
  cells: Trt35CellResult[];
  critical_errors: string[];
}

export interface Trt35ParseResponse {
  parser_result: Trt35ParseResult;
  persisted: false;
  approval: 'NOT_GRANTED';
}

export async function parseTrt35Pdf(file: File, configuration: Trt35Configuration): Promise<Trt35ParseResponse> {
  const form = new FormData();
  form.append('file', file);
  form.append('configuration', configuration);
  const response = await apiClient.post<Trt35ParseResponse>('/api/v1/cranes/trt35/parse', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}
