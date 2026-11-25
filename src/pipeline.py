import logging
import time
import requests
from src.extract import extract_all_cities
from src.load import load_data
from src.transform import transform_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline(past_days: int = 6) -> dict[str, int]:
    """Execute the full Extract, Transform, and Load workflow."""
    start_time = time.perf_counter()
    logger.info("Starting Weather & Air Quality ETL pipeline (past_days=%d)", past_days)

    try:
        logger.info("Stage 1/3: Extracting raw data from Open-Meteo...")
        raw_batch = extract_all_cities(past_days=past_days)
        logger.info("Extracted raw payloads for %d cities.", len(raw_batch))

        logger.info("Stage 2/3: Transforming and aggregating daily metrics...")
        transformed = transform_all(raw_batch)
        logger.info(
            "Prepared %d cities and %d daily measurement rows.",
            len(transformed["cities"]),
            len(transformed["daily_metrics"]),
        )

        logger.info("Stage 3/3: Loading records into SQLite...")
        summary = load_data(transformed)
        elapsed = time.perf_counter() - start_time
        logger.info(
            "Pipeline succeeded in %.2fs | processed=%d | db_cities=%d | db_measurements=%d",
            elapsed,
            summary["rows_processed"],
            summary["cities_total"],
            summary["measurements_total"],
        )
        return summary

    except requests.RequestException:
        logger.exception(
            "Pipeline failed during API extraction (network or HTTP error)."
        )
        raise
    except Exception:
        logger.exception("Pipeline failed with an unexpected error.")
        raise


if __name__ == "__main__":
    run_pipeline()
