# Data Dictionary

| Field | Description |
|---|---|
| data_source | API or provider name |
| timestamp | Pipeline collection timestamp in UTC |
| symbol | Stock ticker or FRED series id |
| metric_name | Human-readable metric label |
| metric_value | Numeric metric value |
| units | Unit of measurement |
| frequency | Daily, monthly, quarterly, or other frequency |
| provider_timestamp | Provider observation date or latest trading day |
| status | success, api_failure, rate_limited, or raw |
| message | Provider or validation message |
