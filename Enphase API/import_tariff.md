Example payload:

```json
{
    "site_id": 1234321,
    "country": "US",
    "currency": "$",
    "zipcode": "98765",
    "hasAcb": false,
    "chargeFromGrid": false,
    "chargeBeginTime": 0,
    "chargeEndTime": 0,
    "showBatteryConfig": true,
    "hideChargeFromGrid": true,
    "supports_mqtt": true,
    "calibrationProgress": false,
    "purchase": {
        "typeKind": "seasonal",
        "typeId": "tou",
        "hasNetMetering": false,
        "source": "autofill",
        "seasons": [
            {
                "id": "summer",
                "startMonth": "6",
                "endMonth": "9",
                "days": [
                    {
                        "id": "week",
                        "days": [
                            1,
                            2,
                            3,
                            4,
                            5,
                            6,
                            7
                        ],
                        "periods": [
                            {
                                "id": "off-peak",
                                "startTime": "",
                                "endTime": "",
                                "rate": "0.38604",
                                "type": "off-peak",
                                "rateComponents": [
                                    {
                                        "Generation Charge - Summer Off-Peak": 0.14911
                                    },
                                    {
                                        "Distribution Charge - Summer Off-Peak": 0.15665
                                    },
                                    {
                                        "Transmission Charge": 0.05122
                                    },
                                    {
                                        "Transmission Rate Adjustments": -0.01213
                                    },
                                    {
                                        "Reliability Services": 0.00032
                                    },
                                    {
                                        "Public Purpose Programs": 0.02644
                                    },
                                    {
                                        "Nuclear Decommissioning": -0.00024
                                    },
                                    {
                                        "Competition Transition Charges": -0.00072
                                    },
                                    {
                                        "Energy Cost Recovery Amount": 0.00001
                                    },
                                    {
                                        "Wildfire Fund Charge": 0.00595
                                    },
                                    {
                                        "New System Generation Charge": 0.00574
                                    },
                                    {
                                        "Wildfire Hardening Charge": 0.00339
                                    },
                                    {
                                        "Recovery Bond Charge": 0.00778
                                    },
                                    {
                                        "Recovery Bond Credit": -0.00778
                                    },
                                    {
                                        "Energy Surcharge": 0.0003
                                    }
                                ]
                            },
                            {
                                "id": "period-0",
                                "startTime": "1260",
                                "endTime": "1439",
                                "rate": "0.44272",
                                "type": "mid-peak",
                                "rateComponents": [
                                    {
                                        "Generation Charge - Summer Part-Peak": 0.19421
                                    },
                                    {
                                        "Distribution Charge - Summer Part-Peak": 0.16823
                                    },
                                    {
                                        "Transmission Charge": 0.05122
                                    },
                                    {
                                        "Transmission Rate Adjustments": -0.01213
                                    },
                                    {
                                        "Reliability Services": 0.00032
                                    },
                                    {
                                        "Public Purpose Programs": 0.02644
                                    },
                                    {
                                        "Nuclear Decommissioning": -0.00024
                                    },
                                    {
                                        "Competition Transition Charges": -0.00072
                                    },
                                    {
                                        "Energy Cost Recovery Amount": 0.00001
                                    },
                                    {
                                        "Wildfire Fund Charge": 0.00595
                                    },
                                    {
                                        "New System Generation Charge": 0.00574
                                    },
                                    {
                                        "Wildfire Hardening Charge": 0.00339
                                    },
                                    {
                                        "Recovery Bond Charge": 0.00778
                                    },
                                    {
                                        "Recovery Bond Credit": -0.00778
                                    },
                                    {
                                        "Energy Surcharge": 0.0003
                                    }
                                ]
                            },
                            {
                                "id": "period-1",
                                "startTime": "900",
                                "endTime": "959",
                                "rate": "0.44272",
                                "type": "mid-peak",
                                "rateComponents": [
                                    {
                                        "Generation Charge - Summer Part-Peak": 0.19421
                                    },
                                    {
                                        "Distribution Charge - Summer Part-Peak": 0.16823
                                    },
                                    {
                                        "Transmission Charge": 0.05122
                                    },
                                    {
                                        "Transmission Rate Adjustments": -0.01213
                                    },
                                    {
                                        "Reliability Services": 0.00032
                                    },
                                    {
                                        "Public Purpose Programs": 0.02644
                                    },
                                    {
                                        "Nuclear Decommissioning": -0.00024
                                    },
                                    {
                                        "Competition Transition Charges": -0.00072
                                    },
                                    {
                                        "Energy Cost Recovery Amount": 0.00001
                                    },
                                    {
                                        "Wildfire Fund Charge": 0.00595
                                    },
                                    {
                                        "New System Generation Charge": 0.00574
                                    },
                                    {
                                        "Wildfire Hardening Charge": 0.00339
                                    },
                                    {
                                        "Recovery Bond Charge": 0.00778
                                    },
                                    {
                                        "Recovery Bond Credit": -0.00778
                                    },
                                    {
                                        "Energy Surcharge": 0.0003
                                    }
                                ]
                            },
                            {
                                "id": "period-2",
                                "startTime": "960",
                                "endTime": "1259",
                                "rate": "0.6046",
                                "type": "peak",
                                "rateComponents": [
                                    {
                                        "Generation Charge - Summer Peak": 0.29332
                                    },
                                    {
                                        "Distribution Charge - Summer Peak": 0.231
                                    },
                                    {
                                        "Transmission Charge": 0.05122
                                    },
                                    {
                                        "Transmission Rate Adjustments": -0.01213
                                    },
                                    {
                                        "Reliability Services": 0.00032
                                    },
                                    {
                                        "Public Purpose Programs": 0.02644
                                    },
                                    {
                                        "Nuclear Decommissioning": -0.00024
                                    },
                                    {
                                        "Competition Transition Charges": -0.00072
                                    },
                                    {
                                        "Energy Cost Recovery Amount": 0.00001
                                    },
                                    {
                                        "Wildfire Fund Charge": 0.00595
                                    },
                                    {
                                        "New System Generation Charge": 0.00574
                                    },
                                    {
                                        "Wildfire Hardening Charge": 0.00339
                                    },
                                    {
                                        "Recovery Bond Charge": 0.00778
                                    },
                                    {
                                        "Recovery Bond Credit": -0.00778
                                    },
                                    {
                                        "Energy Surcharge": 0.0003
                                    }
                                ]
                            }
                        ],
                        "updatedValue": ""
                    }
                ]
            },
            {
                "id": "winter",
                "startMonth": "10",
                "endMonth": "5",
                "days": [
                    {
                        "id": "week",
                        "days": [
                            1,
                            2,
                            3,
                            4,
                            5,
                            6,
                            7
                        ],
                        "periods": [
                            {
                                "id": "off-peak",
                                "startTime": "",
                                "endTime": "",
                                "rate": "0.33714",
                                "type": "off-peak",
                                "rateComponents": [
                                    {
                                        "Generation Charge - Winter Off-Peak": 0.09787
                                    },
                                    {
                                        "Distribution Charge - Winter Off-Peak": 0.15899
                                    },
                                    {
                                        "Transmission Charge": 0.05122
                                    },
                                    {
                                        "Transmission Rate Adjustments": -0.01213
                                    },
                                    {
                                        "Reliability Services": 0.00032
                                    },
                                    {
                                        "Public Purpose Programs": 0.02644
                                    },
                                    {
                                        "Nuclear Decommissioning": -0.00024
                                    },
                                    {
                                        "Competition Transition Charges": -0.00072
                                    },
                                    {
                                        "Energy Cost Recovery Amount": 0.00001
                                    },
                                    {
                                        "Wildfire Fund Charge": 0.00595
                                    },
                                    {
                                        "New System Generation Charge": 0.00574
                                    },
                                    {
                                        "Wildfire Hardening Charge": 0.00339
                                    },
                                    {
                                        "Recovery Bond Charge": 0.00778
                                    },
                                    {
                                        "Recovery Bond Credit": -0.00778
                                    },
                                    {
                                        "Energy Surcharge": 0.0003
                                    }
                                ]
                            },
                            {
                                "id": "period-0",
                                "startTime": "1260",
                                "endTime": "1439",
                                "rate": "0.351",
                                "type": "mid-peak",
                                "rateComponents": [
                                    {
                                        "Generation Charge - Winter Part-Peak": 0.11122
                                    },
                                    {
                                        "Distribution Charge - Winter Part-Peak": 0.1595
                                    },
                                    {
                                        "Transmission Charge": 0.05122
                                    },
                                    {
                                        "Transmission Rate Adjustments": -0.01213
                                    },
                                    {
                                        "Reliability Services": 0.00032
                                    },
                                    {
                                        "Public Purpose Programs": 0.02644
                                    },
                                    {
                                        "Nuclear Decommissioning": -0.00024
                                    },
                                    {
                                        "Competition Transition Charges": -0.00072
                                    },
                                    {
                                        "Energy Cost Recovery Amount": 0.00001
                                    },
                                    {
                                        "Wildfire Fund Charge": 0.00595
                                    },
                                    {
                                        "New System Generation Charge": 0.00574
                                    },
                                    {
                                        "Wildfire Hardening Charge": 0.00339
                                    },
                                    {
                                        "Recovery Bond Charge": 0.00778
                                    },
                                    {
                                        "Recovery Bond Credit": -0.00778
                                    },
                                    {
                                        "Energy Surcharge": 0.0003
                                    }
                                ]
                            },
                            {
                                "id": "period-1",
                                "startTime": "900",
                                "endTime": "959",
                                "rate": "0.351",
                                "type": "mid-peak",
                                "rateComponents": [
                                    {
                                        "Generation Charge - Winter Part-Peak": 0.11122
                                    },
                                    {
                                        "Distribution Charge - Winter Part-Peak": 0.1595
                                    },
                                    {
                                        "Transmission Charge": 0.05122
                                    },
                                    {
                                        "Transmission Rate Adjustments": -0.01213
                                    },
                                    {
                                        "Reliability Services": 0.00032
                                    },
                                    {
                                        "Public Purpose Programs": 0.02644
                                    },
                                    {
                                        "Nuclear Decommissioning": -0.00024
                                    },
                                    {
                                        "Competition Transition Charges": -0.00072
                                    },
                                    {
                                        "Energy Cost Recovery Amount": 0.00001
                                    },
                                    {
                                        "Wildfire Fund Charge": 0.00595
                                    },
                                    {
                                        "New System Generation Charge": 0.00574
                                    },
                                    {
                                        "Wildfire Hardening Charge": 0.00339
                                    },
                                    {
                                        "Recovery Bond Charge": 0.00778
                                    },
                                    {
                                        "Recovery Bond Credit": -0.00778
                                    },
                                    {
                                        "Energy Surcharge": 0.0003
                                    }
                                ]
                            },
                            {
                                "id": "period-2",
                                "startTime": "960",
                                "endTime": "1259",
                                "rate": "0.37309",
                                "type": "peak",
                                "rateComponents": [
                                    {
                                        "Generation Charge - Winter Peak": 0.13119
                                    },
                                    {
                                        "Distribution Charge - Winter Peak": 0.16162
                                    },
                                    {
                                        "Transmission Charge": 0.05122
                                    },
                                    {
                                        "Transmission Rate Adjustments": -0.01213
                                    },
                                    {
                                        "Reliability Services": 0.00032
                                    },
                                    {
                                        "Public Purpose Programs": 0.02644
                                    },
                                    {
                                        "Nuclear Decommissioning": -0.00024
                                    },
                                    {
                                        "Competition Transition Charges": -0.00072
                                    },
                                    {
                                        "Energy Cost Recovery Amount": 0.00001
                                    },
                                    {
                                        "Wildfire Fund Charge": 0.00595
                                    },
                                    {
                                        "New System Generation Charge": 0.00574
                                    },
                                    {
                                        "Wildfire Hardening Charge": 0.00339
                                    },
                                    {
                                        "Recovery Bond Charge": 0.00778
                                    },
                                    {
                                        "Recovery Bond Credit": -0.00778
                                    },
                                    {
                                        "Energy Surcharge": 0.0003
                                    }
                                ]
                            }
                        ],
                        "updatedValue": ""
                    }
                ]
            }
        ],
        "utilityDetails": {
            "utilityId": 734,
            "tariffCodeId": 3518724,
            "utilityName": "Pacific Gas & Electric Co",
            "tariffName": "E-ELEC-NEM3 Residential Time-Of-Use - Electric Home, 4PM - 9PM (NEM 3.0)",
            "masterTariffCodeId": 3424821,
            "isAccAdderApplicable": true,
            "accPlusAdder": {
                "0": 0,
                "1": 0.0132,
                "2": 0
            },
            "accApplicableYears": 9
        }
    },
    "buyback": {
        "typeKind": "single",
        "typeId": "tou",
        "source": "autofill",
        "metaTariffId": 230,
        "lastExportDate": "2033-09-11T07:00:00Z",
        "seasons": [],
        "utilityDetails": {
            "utilityId": 734,
            "tariffCodeId": 3518724,
            "utilityName": "Pacific Gas & Electric Co",
            "tariffName": "E-ELEC-NEM3 Residential Time-Of-Use - Electric Home, 4PM - 9PM (NEM 3.0)",
            "masterTariffCodeId": 3424821,
            "isAccAdderApplicable": true,
            "accPlusAdder": {
                "0": 0,
                "1": 0.0132,
                "2": 0
            },
            "accApplicableYears": 9,
            "accCustomerType": 1,
            "accPlusAdderValue": 0.0132
        },
        "exportPlan": "nem"
    },
    "nemVersion": "NEM3",
    "installDate": "2024-09-13",
    "showDTQuestion": false,
    "dtCustomChargeEnabled": true
}
```
