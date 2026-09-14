import { useState } from "react";
import { reviewTrt35Pdf, TRT35_CONFIGURATIONS, type Trt35CapacityStatus, type Trt35ReviewResponse } from "../api/cranes";
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
type FormValues = { radius_m: string; boom_length_m: string; required_height_m: string; payload_t: string; rigging_t: string; hook_block_t: string; spreader_t: string; configuration_confirmed: boolean };
const INITIAL_VALUES: FormValues = { radius_m: "", boom_length_m: "", required_height_m: "", payload_t: "", rigging_t: "0", hook_block_t: "0", spreader_t: "0", configuration_confirmed: false };

export default function CraneCapacity() {
  const { addToast } = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [configuration, setConfiguration] = useState("");
  const [values, setValues] = useState<FormValues>(INITIAL_VALUES);
  const [result, setResult] = useState<Trt35ReviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const setValue = (field: keyof FormValues, value: string | boolean) => setValues((current) => ({ ...current, [field]: value }));

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !configuration) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const number = (value: string) => Number(value);
      const response = await reviewTrt35Pdf(file, configuration as (typeof TRT35_CONFIGURATIONS)[number]["value"], {
        radius_m: number(values.radius_m), boom_length_m: number(values.boom_length_m), required_height_m: number(values.required_height_m),
        payload_t: number(values.payload_t), rigging_t: number(values.rigging_t), hook_block_t: number(values.hook_block_t),
        spreader_t: number(values.spreader_t), configuration_confirmed: values.configuration_confirmed,
      });
      setResult(response);
      addToast("양중 용량 검토 결과를 생성했습니다. 작업 승인은 포함하지 않습니다.", "success");
    } catch (requestError) {
      setError(requestError);
      addToast("양중 검토를 완료할 수 없습니다. 원본 PDF, 구성 및 입력값을 확인해 주세요.", "error");
    } finally { setLoading(false); }
  }

  const review = result?.review_result;
  const fields: Array<[Exclude<keyof FormValues, "configuration_confirmed">, string, boolean]> = [
    ["radius_m", "작업 반경 (m)", true], ["boom_length_m", "붐 길이 (m)", true], ["required_height_m", "필요 양중 높이 (m)", true],
    ["payload_t", "중량물 (t)", true], ["rigging_t", "줄걸이 합계 (t)", false], ["hook_block_t", "훅 블록 (t)", false], ["spreader_t", "스프레더 (t)", false],
  ];

  return <div className="mx-auto max-w-6xl space-y-6">
    <section className="rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50 to-white p-6 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wider text-blue-600">TRT35 preliminary lift review</p>
      <h1 className="mt-2 text-2xl font-bold text-slate-900">양중 작업 검토</h1>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">검증된 TRT35 용량표의 정확한 반경·붐 길이 셀로 총 양중중량을 비교합니다. 보간은 하지 않으며, 이 결과는 작업 승인이나 운전 지시가 아닙니다.</p>
    </section>
    <form className="space-y-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={handleSubmit}>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm font-semibold text-slate-700">TRT35 원본 PDF<input className="mt-2 block w-full rounded-lg border border-slate-300 p-2 text-sm" type="file" accept="application/pdf,.pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
        <label className="text-sm font-semibold text-slate-700">용량표 구성<select className="mt-2 block w-full rounded-lg border border-slate-300 p-2 text-sm" value={configuration} onChange={(event) => setConfiguration(event.target.value)}><option value="">구성을 선택하세요</option>{TRT35_CONFIGURATIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {fields.map(([field, label, required]) => <label key={field} className="text-sm font-semibold text-slate-700">{label}<input className="mt-2 block w-full rounded-lg border border-slate-300 p-2 text-sm" type="number" min="0" step="0.01" required={required} value={values[field]} onChange={(event) => setValue(field, event.target.value)} /></label>)}
      </div>
      <label className="flex items-start gap-3 rounded-lg bg-amber-50 p-3 text-sm text-slate-700"><input className="mt-1" type="checkbox" checked={values.configuration_confirmed} onChange={(event) => setValue("configuration_confirmed", event.target.checked)} /><span>선택한 용량표 구성(아웃트리거, 작업영역, 이동/정지 조건, 지브 조건)이 실제 장비 설정과 일치함을 확인했습니다.</span></label>
      <button className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400" type="submit" disabled={!file || !configuration || loading}>{loading ? "검토 중..." : "양중 작업 검토"}</button>
    </form>
    {loading && <Spinner text="검증 용량표와 작업조건을 대조하고 있습니다..." />}
    {error !== null && <ErrorBox error={error} />}
    {review && <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className={`rounded-lg border p-4 ${CAPACITY_STYLE[review.capacity_status]}`}><p className="text-xs font-bold uppercase tracking-wide">용량 검토</p><h2 className="mt-1 text-xl font-bold">{CAPACITY_LABEL[review.capacity_status]}</h2>{review.reason && <p className="mt-2 text-sm">{review.reason}</p>}</div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Metric label="총 양중중량" value={`${review.gross_load_t.toFixed(2)} t`} /><Metric label="정격 용량" value={review.rated_capacity_t == null ? "-" : `${review.rated_capacity_t.toFixed(2)} t`} /><Metric label="용량 여유" value={review.capacity_margin_t == null ? "-" : `${review.capacity_margin_t.toFixed(2)} t`} /><Metric label="사용률" value={review.utilization_percent == null ? "-" : `${review.utilization_percent.toFixed(1)} %`} /></div>
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-900"><p className="font-bold">높이 검토: 미검증으로 차단</p><p className="mt-1 text-sm">입력 높이 {review.required_height_m.toFixed(2)} m — {review.geometry_reason}</p></div>
      <p className="text-xs text-slate-500">근거: 용량표 페이지 {review.source_page ?? "-"}. 승인 상태: {review.approval}.</p>
    </section>}
  </div>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg bg-slate-50 p-4"><p className="text-xs font-semibold text-slate-500">{label}</p><p className="mt-1 text-lg font-bold text-slate-900">{value}</p></div>;
}
