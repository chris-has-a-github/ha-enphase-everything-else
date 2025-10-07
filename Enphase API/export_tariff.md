Example payload:

```json
{
    "type": "tariff-rates",
    "timestamp": "2025-10-04T18:10:22.921060539Z",
    "data": {
        "tariff-version-id": "11dd22cc333333b44a555555",
        "tariff-type": "static",
        "currency": "$",
        "timezone": "US/Pacific",
        "siteDetails": {
            "currency": "$",
            "timezone": "US/Pacific",
            "importPlanType": "NEM3",
            "exportPlanType": "NEM3",
            "exportApplicabilityYear": 2024,
            "interconnectionApplicationDate": "2024-09-12T00:00:00Z",
            "installDate": "2024-09-13",
            "lastExportDate": "2033-09-11T07:00:00Z"
        },
        "buyback": [
            {
                "start": 0,
                "end": 59,
                "rate": 0.0675
            },
            {
                "start": 60,
                "end": 119,
                "rate": 0.0669
            },
            {
                "start": 120,
                "end": 179,
                "rate": 0.0651
            },
            {
                "start": 180,
                "end": 239,
                "rate": 0.0652
            },
            {
                "start": 240,
                "end": 299,
                "rate": 0.0649
            },
            {
                "start": 300,
                "end": 359,
                "rate": 0.0643
            },
            {
                "start": 360,
                "end": 419,
                "rate": 0.0647
            },
            {
                "start": 420,
                "end": 479,
                "rate": 0.0611
            },
            {
                "start": 480,
                "end": 539,
                "rate": 0.0564
            },
            {
                "start": 540,
                "end": 599,
                "rate": 0.0569
            },
            {
                "start": 600,
                "end": 659,
                "rate": 0.0584
            },
            {
                "start": 660,
                "end": 719,
                "rate": 0.0604
            },
            {
                "start": 720,
                "end": 779,
                "rate": 0.0624
            },
            {
                "start": 780,
                "end": 839,
                "rate": 0.0632
            },
            {
                "start": 840,
                "end": 899,
                "rate": 0.0683
            },
            {
                "start": 900,
                "end": 959,
                "rate": 0.0792
            },
            {
                "start": 960,
                "end": 1019,
                "rate": 0.0939
            },
            {
                "start": 1020,
                "end": 1079,
                "rate": 0.1472
            },
            {
                "start": 1080,
                "end": 1139,
                "rate": 0.2367
            },
            {
                "start": 1140,
                "end": 1199,
                "rate": 0.1163
            },
            {
                "start": 1200,
                "end": 1259,
                "rate": 0.1077
            },
            {
                "start": 1260,
                "end": 1319,
                "rate": 0.0987
            },
            {
                "start": 1320,
                "end": 1379,
                "rate": 0.0851
            },
            {
                "start": 1380,
                "end": 1439,
                "rate": 0.0738
            }
        ]
    }
}
```