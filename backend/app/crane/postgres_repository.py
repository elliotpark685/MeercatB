"""Atomic PostgreSQL writer for TRT60 parser output.

Supabase is PostgreSQL here; no Supabase REST URL or service-role key is used.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.crane.trt60_schema import CanonicalTRT60Data


class PostgresTRT60Repository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, data: CanonicalTRT60Data, *, original_filename: str) -> dict[str, int | str]:
        if data.parser_verification_status.value != "AUTO_VALIDATED":
            raise ValueError("only AUTO_VALIDATED parser output can be persisted")

        # One Session transaction covers every insert. Any exception rolls back all rows.
        with self.db.begin():
            crane_id = self.db.execute(text("""
                insert into public.cranes
                    (manufacturer, brand, model, crane_type, nominal_capacity_t, parser_profile, parser_version)
                values (:manufacturer, :brand, :model, :crane_type, :nominal_capacity_t, :parser_profile, :parser_version)
                on conflict (manufacturer, model) do update set
                    brand = excluded.brand,
                    nominal_capacity_t = excluded.nominal_capacity_t,
                    parser_profile = excluded.parser_profile,
                    parser_version = excluded.parser_version,
                    updated_at = now()
                returning id
            """), data.model_dump(mode="json")).scalar_one()

            source_id = self.db.execute(text("""
                insert into public.source_documents
                    (crane_id, original_filename, manufacturer, model, parser_profile, parser_version,
                     parser_verification_status, validation_errors)
                values (:crane_id, :original_filename, :manufacturer, :model, :parser_profile, :parser_version,
                        :parser_verification_status, cast(:validation_errors as jsonb))
                returning id
            """), {
                "crane_id": crane_id, "original_filename": original_filename,
                "manufacturer": data.manufacturer, "model": data.model,
                "parser_profile": data.parser_profile, "parser_version": data.parser_version,
                "parser_verification_status": data.parser_verification_status.value,
                "validation_errors": __import__("json").dumps(data.validation_errors),
            }).scalar_one()

            chart_count = 0
            cell_count = 0
            for chart in data.load_charts:
                config_id = self.db.execute(text("""
                    insert into public.lifting_configurations
                        (crane_id, source_document_id, counterweight_t, support_mode, working_area, standard, source_page)
                    values (:crane_id, :source_document_id, :counterweight_t, :support_mode, :working_area, :standard, :source_page)
                    returning id
                """), {"crane_id": crane_id, "source_document_id": source_id, **chart.header.model_dump(mode="json", exclude={"source"}), "source_page": chart.header.source.source_page}).scalar_one()
                self.db.execute(text("""
                    insert into public.support_configurations
                        (lifting_configuration_id, support_type, outrigger_percent, outrigger_width_m)
                    values (:configuration_id, :support_type, :outrigger_percent, :outrigger_width_m)
                """), {"configuration_id": config_id, "support_type": chart.header.support_mode, "outrigger_percent": chart.header.outrigger_percent, "outrigger_width_m": chart.header.outrigger_width_m})
                boom_id = self.db.execute(text("""
                    insert into public.boom_configurations
                        (lifting_configuration_id, boom_type, main_boom_length_m, jib_length_m)
                    values (:configuration_id, :boom_type, :main_boom_length_m, :jib_length_m)
                    returning id
                """), {"configuration_id": config_id, "boom_type": chart.header.boom_type, "main_boom_length_m": chart.header.main_boom_length_m, "jib_length_m": chart.header.jib_length_m}).scalar_one()
                chart_id = self.db.execute(text("""
                    insert into public.load_charts
                        (crane_id, source_document_id, lifting_configuration_id, boom_configuration_id,
                         chart_type, unit_system, capacity_basis, source_page, parser_profile, parser_version, verification_status)
                    values (:crane_id, :source_document_id, :configuration_id, :boom_id,
                            :chart_type, :unit_system, :capacity_basis, :source_page, :parser_profile, :parser_version, :verification_status)
                    returning id
                """), {"crane_id": crane_id, "source_document_id": source_id, "configuration_id": config_id, "boom_id": boom_id, "chart_type": chart.chart_type, "unit_system": chart.unit_system, "capacity_basis": chart.capacity_basis, "source_page": chart.source.source_page, "parser_profile": data.parser_profile, "parser_version": data.parser_version, "verification_status": data.parser_verification_status.value}).scalar_one()
                rows = []
                for cell in chart.cells:
                    row = cell.model_dump(mode="json", exclude={"source"})
                    row.update({"load_chart_id": chart_id, "source_page": cell.source.source_page})
                    rows.append(row)
                self.db.execute(text("""
                    insert into public.load_chart_cells
                        (load_chart_id, radius_m, boom_length_m, boom_angle_deg, rated_capacity_t,
                         source_radius_text, parsed_source_radius_value, source_radius_unit,
                         source_capacity_text, parsed_source_capacity_value, source_capacity_unit,
                         cell_status, source_text, source_page, confidence)
                    values (:load_chart_id, :radius_m, :boom_length_m, :boom_angle_deg, :rated_capacity_t,
                            :source_radius_text, :parsed_source_radius_value, :source_radius_unit,
                            :source_capacity_text, :parsed_source_capacity_value, :source_capacity_unit,
                            :cell_status, :source_text, :source_page, :confidence)
                """), rows)
                chart_count += 1
                cell_count += len(rows)
        return {"crane_id": str(crane_id), "source_document_id": str(source_id), "chart_count": chart_count, "cell_count": cell_count}
