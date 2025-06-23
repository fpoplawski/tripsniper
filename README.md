# Trip Sniper

This project provides the skeleton for the `trip_sniper` service managed with [Poetry](https://python-poetry.org/).

## Installation

1. Install Poetry if it is not already installed:
   ```bash
   pip install poetry
   ```
2. Install the project dependencies:
   ```bash
   poetry install
   ```

## Running

To run the service module:

```bash
poetry run python -m trip_sniper.service
```

This command will execute the main service package. Adjust the entry point as your implementation evolves.

## Scoring Configuration

The `steal_score` algorithm combines several feature scores using a weight table.
Default weights are:

```json
{
    "discount_pct": 0.25,
    "absolute_price_score": 0.2,
    "hotel_quality": 0.2,
    "flight_comfort": 0.15,
    "urgency_score": 0.05,
    "novelty_score": 0.05,
    "category_match": 0.1
}
```

Weights can be overridden via the environment. Provide a JSON string in
`STEAL_SCORE_WEIGHTS` or a path to a JSON file in `STEAL_SCORE_WEIGHTS_FILE`.
Missing keys fall back to the defaults.

Example using an environment variable:

```bash
export STEAL_SCORE_WEIGHTS='{"discount_pct": 0.3, "absolute_price_score": 0.15}'
```

Example JSON file (`weights.json`):

```json
{
    "discount_pct": 0.3,
    "absolute_price_score": 0.15
}
```

```bash
export STEAL_SCORE_WEIGHTS_FILE=weights.json
```

## Scheduler

`src/trip_sniper/scheduler.py` starts a Celery beat process that triggers the
data pipeline once per hour by default. To change the schedule, provide a
standard five-field cron expression in the `RUN_PIPELINE_CRON` environment
variable. The value is parsed using `celery.schedules.crontab`.

```bash
export RUN_PIPELINE_CRON="0 */6 * * *"  # run every six hours
```

