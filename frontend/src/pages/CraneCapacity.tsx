import { useState } from "react";
import {
  getTrt35ReviewInputOptions,
  reviewTrt35Pdf,
  TRT35_CONFIGURATIONS,
  type Trt35CapacityStatus,
  type Trt35Configuration,
  type Trt35OverallStatus,
  type Trt35ReviewInputOptions,
  type Trt35ReviewResponse,
} from "../api/cranes";
import ErrorBox from "../components/ErrorBox";
import Spinner from "../components/Spinner";
import { useToast } from "../contexts/ToastContext";

const CAPACITY_LABEL: Record<Trt35CapacityStatus, string> = {
  PASS: "용량 범위 내", FAIL: "허용용량 초과", CONFIGURATION_NOT_CONFIRMED: "장비 조건 확인 필요",
  CELL_NOT_FOUND: "정확한 용량표 셀 없음", CELL_NOT_AVAILABLE: "선택 셀 사용 불가",
};
const CAPACITY_STYLE: Record<Trt35CapacityStatus, string> = {
  PASS: "border-emerald-200 bg-emerald-50 text-emerald-800", FAIL: "border-red-200 bg-red-50 text-red-800",
  CONFIGURATION_NOT_CONFIRMED: "border-amber-200 bg-amber-50 text-amber-800",
  CELL_NOT_FOUND: "border-amber-200 bg-amber-50 text-amber-800", CELL_NOT_AVAILABLE: "border-amber-200 bg-amber-50 text-amber-800",
};
const GEOMETRY_LABEL = { PASS: "높이 범위 내", FAIL: "필요 높이 초과", POINT_NOT_FOUND: "정확한 높이 기준점 없음", REFERENCE_DATASET_REQUIRED: "높이 근거 데이터 필요" } as const;
const GEOMETRY_STYLE = {
  PASS: "border-emerald-200 bg-emerald-50 text-emerald-800", FAIL: "border-red-200 bg-red-50 text-red-800",
  POINT_NOT_FOUND: "border-amber-200 bg-amber-50 text-amber-800", REFERENCE_DATASET_REQUIRED: "border-amber-200 bg-amber-50 text-amber-800",
} as const;
const OVERALL_LABEL: Record<Trt35OverallStatus, string> = {
  REVIEW_PASS: "검토 기준 통과", CONFIGURATION_NOT_CONFIRMED: "장비 구성 확인 필요", CAPACITY_FAIL: "용량 초과로 차단",
  CAPACITY_CELL_NOT_FOUND: "용량표 기준점 없음", CAPACITY_CELL_NOT_AVAILABLE: "용량표 셀 사용 불가",
  GEOMETRY_FAIL: "필요 높이 초과로 차단", GEOMETRY_POINT_NOT_FOUND: "높이 기준점 없음",
  GEOMETRY_REFERENCE_DATASET_REQUIRED: "높이 근거 데이터 필요",
};
const OVERALL_STYLE: Record<Trt35OverallStatus, string> = {
  REVIEW_PASS: "border-emerald-300 bg-emerald-50 text-emerald-900", CONFIGURATION_NOT_CONFIRMED: "border-amber-300 bg-amber-50 text-amber-900",
  CAPACITY_FAIL: "border-red-300 bg-red-50 text-red-900", CAPACITY_CELL_NOT_FOUND: "border-amber-300 bg-amber-50 text-amber-900",
  CAPACITY_CELL_NOT_AVAILABLE: "border-amber-300 bg-amber-50 text-amber-900", GEOMETRY_FAIL: "border-red-300 bg-red-50 text-red-900",
  GEOMETRY_POINT_NOT_FOUND: "border-amber-300 bg-amber-50 text-amber-900", GEOMETRY_REFERENCE_DATASET_REQUIRED: "border-amber-300 bg-amber-50 text-amber-900",
};
const INPUT_CLASS = "mt-2 block w-full rounded-lg border border-slate-300 bg-white p-2 text-sm text-slate-800 disabled:cursor-not-allowed disabled:bg-slate-100";

type RiggingMode = "TOTAL" | "PER_LEG";
type FormValues = {
  boomLength: string; radius: string; requiredHeight: string; payload: string; riggingMode: RiggingMode;
  riggingTotal: string; slingLegCount: string; slingWeightPerLeg: string; hookBlock: string; spreader: string; configurationConfirmed: boolean;
};
const INITIAL_VALUES: FormValues = { boomLength: "", radius: "", requiredHeight: "", payload: "", riggingMode: "TOTAL", riggingTotal: "0", slingLegCount: "2", slingWeightPerLeg: "0", hookBlock: "0", spreader: "0", configurationConfirmed: false };

export default function CraneCapacity() {
  const { addToast } = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [configuration, setConfiguration] = useState<Trt35Configuration | "">("");
  const [inputOptions, setInputOptions] = useState<Trt35ReviewInputOptions | null>(null);
  const [optionsLoading, setOptionsLoading] = useState(false);
  const [values, setValues] = useState<FormValues>(INITIAL_VALUES);
  const [result, setResult] = useState<Trt35ReviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const setValue = <K extends keyof FormValues>(field: K, value: FormValues[K]) => setValues((current) => ({ ...current, [field]: value }));

  async function selectConfiguration(value: string) {
    setConfiguration(value as Trt35Configuration | ""); setInputOptions(null); setResult(null); setError(null);
    setValues((current) => ({ ...current, boomLength: "", radius: "" }));
    if (!value) return;
    setOptionsLoading(true);
    try { setInputOptions(await getTrt35ReviewInputOptions(value as Trt35Configuration)); }
    catch (requestError) { setError(requestError); addToast("검증된 용량표 선택값을 불러올 수 없습니다.", "error"); }
    finally { setOptionsLoading(false); }
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !configuration || !inputOptions) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const number = (value: string) => Number(value);
      const rigging = values.riggingMode === "TOTAL"
        ? { rigging_t: number(values.riggingTotal) }
        : { sling_leg_count: number(values.slingLegCount), sling_weight_per_leg_t: number(values.slingWeightPerLeg) };
      const response = await reviewTrt35Pdf(file, configuration, {
        radius_m: number(values.radius), boom_length_m: number(values.boomLength), required_height_m: number(values.requiredHeight),
        payload_t: number(values.payload), hook_block_t: number(values.hookBlock), spreader_t: number(values.spreader),
        configuration_confirmed: values.configurationConfirmed, ...rigging,
      });
      setResult(response); addToast("양중 검토 결과를 생성했습니다. 운영 승인은 포함하지 않습니다.", "success");
    } catch (requestError) { setError(requestError); addToast("양중 검토를 완료할 수 없습니다. 입력값과 원본 PDF를 확인해 주세요.", "error"); }
    finally { setLoading(false); }
  }

  const radii = values.boomLength ? (inputOptions?.available_radii_by_boom_m[Number(values.boomLength).toFixed(1)] ?? []) : [];
  const review = result?.review_result;
  const submitDisabled = !file || !configuration || !inputOptions || !values.boomLength || !values.radius || loading || optionsLoading;

  return <div className="mx-auto max-w-6xl space-y-6">
    <section className="rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50 to-white p-6 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wider text-blue-600">TRT35 preliminary lift review</p>
      <h1 className="mt-2 text-2xl font-bold text-slate-900">양중 작업 검토</h1>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">모든 길이는 m, 모든 중량은 metric tonne(t)입니다. 반경과 붐 길이는 검증된 용량표 셀에서만 선택할 수 있으며 보간하지 않습니다.</p>
    </section>
    <form className="space-y-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={handleSubmit}>
      <div className="grid gap-4 md:grid-cols-2">
        <Field label="TRT35 원본 PDF"><input className={INPUT_CLASS} type="file" accept="application/pdf,.pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></Field>
        <Field label="용량표 구성"><select className={INPUT_CLASS} value={configuration} onChange={(event) => void selectConfiguration(event.target.value)}><option value="">구성을 선택하세요</option>{TRT35_CONFIGURATIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></Field>
      </div>
      {optionsLoading && <p className="text-sm text-slate-500">검증된 선택값을 불러오는 중...</p>}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Field label="붐 길이 (m)"><select className={INPUT_CLASS} required disabled={!inputOptions} value={values.boomLength} onChange={(event) => { setValue("boomLength", event.target.value); setValue("radius", ""); }}><option value="">선택</option>{inputOptions?.boom_lengths_m.map((value) => <option key={value} value={value}>{value.toFixed(1)} m</option>)}</select></Field>
        <Field label="작업 반경 (m)"><select className={INPUT_CLASS} required disabled={!values.boomLength} value={values.radius} onChange={(event) => setValue("radius", event.target.value)}><option value="">선택</option>{radii.map((value) => <option key={value} value={value}>{value.toFixed(1)} m</option>)}</select></Field>
        <NumberField label="필요 양중 높이 (m)" value={values.requiredHeight} onChange={(value) => setValue("requiredHeight", value)} required />
        <NumberField label="중량물 (t)" value={values.payload} onChange={(value) => setValue("payload", value)} required />
        <NumberField label="훅 블록 (t)" value={values.hookBlock} onChange={(value) => setValue("hookBlock", value)} />
        <NumberField label="스프레더 (t)" value={values.spreader} onChange={(value) => setValue("spreader", value)} />
      </div>
      <fieldset className="rounded-lg border border-slate-200 p-4"><legend className="px-1 text-sm font-bold text-slate-700">줄걸이 중량 (t)</legend><div className="mb-3 flex gap-4 text-sm"><label><input type="radio" checked={values.riggingMode === "TOTAL"} onChange={() => setValue("riggingMode", "TOTAL")} /> 합계 입력</label><label><input type="radio" checked={values.riggingMode === "PER_LEG"} onChange={() => setValue("riggingMode", "PER_LEG")} /> 다리별 입력</label></div>{values.riggingMode === "TOTAL" ? <NumberField label="줄걸이 합계 (t)" value={values.riggingTotal} onChange={(value) => setValue("riggingTotal", value)} /> : <div className="grid gap-4 sm:grid-cols-2"><Field label="슬링 다리 수"><select className={INPUT_CLASS} value={values.slingLegCount} onChange={(event) => setValue("slingLegCount", event.target.value)}>{[1, 2, 3, 4].map((value) => <option key={value} value={value}>{value}</option>)}</select></Field><NumberField label="다리당 중량 (t)" value={values.slingWeightPerLeg} onChange={(value) => setValue("slingWeightPerLeg", value)} /></div>}</fieldset>
      <label className="flex items-start gap-3 rounded-lg bg-amber-50 p-3 text-sm text-slate-700"><input className="mt-1" type="checkbox" checked={values.configurationConfirmed} onChange={(event) => setValue("configurationConfirmed", event.target.checked)} /><span>선택한 용량표 구성(아웃트리거, 작업영역, 이동/정지 조건, 지브 조건)이 실제 장비 설정과 일치함을 확인했습니다.</span></label>
      <button className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400" type="submit" disabled={submitDisabled}>{loading ? "검토 중..." : "양중 작업 검토"}</button>
    </form>
    {loading && <Spinner text="검증 용량표와 작업조건을 대조하고 있습니다..." />}{error !== null && <ErrorBox error={error} />}
    {review && <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className={`rounded-lg border-2 p-4 ${OVERALL_STYLE[review.overall_status]}`}><p className="text-xs font-bold uppercase tracking-wide">종합 양중 검토</p><h2 className="mt-1 text-xl font-bold">{OVERALL_LABEL[review.overall_status]}</h2><p className="mt-2 text-sm">{review.overall_reason}</p><p className="mt-1 text-xs">운영 승인 상태: {review.approval}</p></div>
      <div className={`rounded-lg border p-4 ${CAPACITY_STYLE[review.capacity_status]}`}><p className="text-xs font-bold uppercase tracking-wide">용량 검토</p><h2 className="mt-1 text-xl font-bold">{CAPACITY_LABEL[review.capacity_status]}</h2>{review.reason && <p className="mt-2 text-sm">{review.reason}</p>}</div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Metric label="총 양중중량" value={`${review.gross_load_t.toFixed(2)} t`} /><Metric label="정격 용량" value={review.rated_capacity_t == null ? "-" : `${review.rated_capacity_t.toFixed(2)} t`} /><Metric label="용량 여유" value={review.capacity_margin_t == null ? "-" : `${review.capacity_margin_t.toFixed(2)} t`} /><Metric label="사용률" value={review.utilization_percent == null ? "-" : `${review.utilization_percent.toFixed(1)} %`} /></div>
      <div className={`rounded-lg border p-4 ${GEOMETRY_STYLE[review.geometry_status]}`}><p className="font-bold">높이 검토: {GEOMETRY_LABEL[review.geometry_status]}</p><p className="mt-1 text-sm">입력 높이 {review.required_height_m.toFixed(2)} m — {review.geometry_reason}</p>{review.maximum_hook_height_m != null && <p className="mt-1 text-sm">검증 최대 훅 높이 {review.maximum_hook_height_m.toFixed(2)} m / 여유 {review.height_margin_m?.toFixed(2) ?? "-"} m / 기준 {review.height_reference ?? "-"}</p>}</div>
    </section>}
  </div>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) { return <label className="block text-sm font-semibold text-slate-700">{label}{children}</label>; }
function NumberField({ label, value, onChange, required = false }: { label: string; value: string; onChange: (value: string) => void; required?: boolean }) { return <Field label={label}><input className={INPUT_CLASS} type="number" min="0" step="0.01" required={required} value={value} onChange={(event) => onChange(event.target.value)} /></Field>; }
function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-lg bg-slate-50 p-4"><p className="text-xs font-semibold text-slate-500">{label}</p><p className="mt-1 text-lg font-bold text-slate-900">{value}</p></div>; }
