"""Supabase boundary mapping; this does not create or own database schema."""

from app.crane.trt60_schema import CanonicalTRT60Data


class TRT60SupabaseMapper:
    """Produce table-shaped records for a user-owned Supabase schema."""

    @staticmethod
    def to_rows(data: CanonicalTRT60Data) -> dict[str, list[dict]]:
        crane_id = "parser-generated"
        source_id = "parser-generated"
        crane = {"manufacturer": data.manufacturer, "brand": data.brand, "model": data.model, "crane_type": data.crane_type, "nominal_capacity_t": data.nominal_capacity_t, "parser_profile": data.parser_profile, "parser_version": data.parser_version}
        source = {
            "crane_external_id": crane_id,
            "original_filename": data.source_document.source_text,
            "manufacturer": data.manufacturer,
            "model": data.model,
            "file_hash_sha256": None,
            "storage_path": None,
            "parser_profile": data.parser_profile,
            "parser_version": data.parser_version,
            "parser_verification_status": data.parser_verification_status.value,
            "validation_errors": data.validation_errors,
        }
        configurations = []
        charts = []
        cells = []
        for chart_index, chart in enumerate(data.load_charts):
            config_id = f"config-{chart_index}"
            configurations.append({"external_id": config_id, "crane_external_id": crane_id, **chart.header.model_dump(mode="json", exclude={"source"}), "source_page": chart.header.source.source_page})
            chart_id = f"chart-{chart_index}"
            charts.append({"external_id": chart_id, "crane_external_id": crane_id, "source_external_id": source_id, "chart_type": chart.chart_type, "unit_system": chart.unit_system, "capacity_basis": chart.capacity_basis, "configuration_external_id": config_id, "source_page": chart.source.source_page})
            for cell in chart.cells:
                cells.append({"load_chart_external_id": chart_id, **cell.model_dump(mode="json", exclude={"source", "source_text"}), "source_text": cell.source_text, "source_page": cell.source.source_page})
        return {"cranes": [crane], "source_documents": [source], "lifting_configurations": configurations, "load_charts": charts, "load_chart_cells": cells}
