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

export type Trt35CapacityStatus =
  | 'PASS'
  | 'FAIL'
  | 'CONFIGURATION_NOT_CONFIRMED'
  | 'CELL_NOT_FOUND'
  | 'CELL_NOT_AVAILABLE';

export interface Trt35ReviewInput {
  radius_m: number;
  boom_length_m: number;
  required_height_m: number;
  payload_t: number;
  rigging_t?: number;
  sling_leg_count?: number;
  sling_weight_per_leg_t?: number;
  hook_block_t: number;
  spreader_t: number;
  configuration_confirmed: boolean;
}

export interface Trt35ReviewResult {
  gross_load_t: number;
  rigging_total_t: number;
  required_height_m: number;
  capacity_status: Trt35CapacityStatus;
  geometry_status: 'REFERENCE_DATASET_REQUIRED';
  rated_capacity_t: number | null;
  capacity_margin_t: number | null;
  utilization_percent: number | null;
  source_page: number | null;
  reason: string | null;
  geometry_reason: string;
  approval: 'NOT_GRANTED';
}

export interface Trt35ReviewResponse {
  review_result: Trt35ReviewResult;
  persisted: false;
  approval: 'NOT_GRANTED';
}

export async function parseTrt35Pdf(file: File, configuration: Trt35Configuration): Promise<Trt35ParseResponse> {
  const form = new FormData();
  form.append('file', file);
  form.append('configuration', configuration);
  // Leave Content-Type unset: the browser must add the multipart boundary.
  const response = await apiClient.post<Trt35ParseResponse>('/api/v1/cranes/trt35/parse', form);
  return response.data;
}

export async function reviewTrt35Pdf(file: File, configuration: Trt35Configuration, review: Trt35ReviewInput): Promise<Trt35ReviewResponse> {
  const form = new FormData();
  form.append('file', file);
  form.append('configuration', configuration);
  form.append('review', JSON.stringify(review));
  const response = await apiClient.post<Trt35ReviewResponse>('/api/v1/cranes/trt35/review', form);
  return response.data;
}
