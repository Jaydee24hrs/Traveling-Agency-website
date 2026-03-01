import json

# Load the JSON content from the file
with open('/mnt/data/stuff.json', 'r') as file:
    data = json.load(file)

# Fix the JSON structure by correcting syntax errors and formatting issues
fixed_data = {
    "type": "flight-offer",
    "id": "1",
    "source": "GDS",
    "instantTicketingRequired": False,
    "nonHomogeneous": False,
    "oneWay": False,
    "isUpsellOffer": False,
    "lastTicketingDate": "2024-09-12",
    "lastTicketingDateTime": "2024-09-12",
    "numberOfBookableSeats": 5,
    "itineraries": [
        {
            "duration": "PT9H5M",
            "segments": [
                {
                    "departure": {
                        "iataCode": "LOS",
                        "terminal": "2",
                        "at": "2024-09-12T06:50:00"
                    },
                    "arrival": {
                        "iataCode": "CMN",
                        "terminal": "2",
                        "at": "2024-09-12T11:25:00"
                    },
                    "carrierCode": "AT",
                    "number": "554",
                    "aircraft": {
                        "code": "73H"
                    },
                    "operating": {
                        "carrierCode": "AT"
                    },
                    "duration": "PT4H35M",
                    "id": "11",
                    "numberOfStops": 0,
                    "blacklistedInEU": False
                },
                {
                    "departure": {
                        "iataCode": "CMN",
                        "terminal": "1",
                        "at": "2024-09-12T12:25:00"
                    },
                    "arrival": {
                        "iataCode": "FRA",
                        "terminal": "2",
                        "at": "2024-09-12T16:55:00"
                    },
                    "carrierCode": "AT",
                    "number": "810",
                    "aircraft": {
                        "code": "73H"
                    },
                    "operating": {
                        "carrierCode": "AT"
                    },
                    "duration": "PT3H30M",
                    "id": "12",
                    "numberOfStops": 0,
                    "blacklistedInEU": False
                }
            ]
        },
        {
            "duration": "PT12H40M",
            "segments": [
                {
                    "departure": {
                        "iataCode": "FRA",
                        "terminal": "2",
                        "at": "2024-09-17T17:55:00"
                    },
                    "arrival": {
                        "iataCode": "CMN",
                        "terminal": "2",
                        "at": "2024-09-17T20:35:00"
                    },
                    "carrierCode": "AT",
                    "number": "811",
                    "aircraft": {
                        "code": "73H"
                    },
                    "operating": {
                        "carrierCode": "AT"
                    },
                    "duration": "PT3H40M",
                    "id": "131",
                    "numberOfStops": 0,
                    "blacklistedInEU": False
                },
                {
                    "departure": {
                        "iataCode": "CMN",
                        "terminal": "1",
                        "at": "2024-09-18T01:10:00"
                    },
                    "arrival": {
                        "iataCode": "LOS",
                        "terminal": "2",
                        "at": "2024-09-18T05:35:00"
                    },
                    "carrierCode": "AT",
                    "number": "555",
                    "aircraft": {
                        "code": "788"
                    },
                    "operating": {
                        "carrierCode": "AT"
                    },
                    "duration": "PT4H25M",
                    "id": "132",
                    "numberOfStops": 0,
                    "blacklistedInEU": False
                }
            ]
        }
    ],
    "price": {
        "currency": "NGN",
        "total": 3087497.00,
        "base": 1149570.00,
        "fees": [
            {
                "amount": 0.00,
                "type": "SUPPLIER"
            },
            {
                "amount": 0.00,
                "type": "TICKETING"
            }
        ],
        "grandTotal": 3087497.00
    },
    "pricingOptions": {
        "fareType": ["PUBLISHED"],
        "includedCheckedBagsOnly": False
    },
    "validatingAirlineCodes": ["AT"],
    "travelerPricings": [
        {
            "travelerId": "1",
            "fareOption": "STANDARD",
            "travelerType": "ADULT",
            "price": {
                "currency": "NGN",
                "total": 1571295.00,
                "base": 610560.00
            },
            "fareDetailsBySegment": [
                {
                    "segmentId": "11",
                    "cabin": "ECONOMY",
                    "fareBasis": "QA0RAAFA",
                    "class": "Q",
                    "includedCheckedBags": {
                        "quantity": 2
                    }
                },
                {
                    "segmentId": "12",
                    "cabin": "ECONOMY",
                    "fareBasis": "QA0RAAFA",
                    "class": "Q",
                    "includedCheckedBags": {
                        "quantity": 2
                    }
                },
                {
                    "segmentId": "131",
                    "cabin": "ECONOMY",
                    "fareBasis": "QA0RAAFA",
                    "class": "Q",
                    "includedCheckedBags": {
                        "quantity": 2
                    }
                },
                {
                    "segmentId": "132",
                    "cabin": "ECONOMY",
                    "fareBasis": "QA0RAAFA",
                    "class": "Q",
                    "includedCheckedBags": {
                        "quantity": 2
                    }
                }
            ]
        },
        {
            "travelerId": "2",
            "fareOption": "STANDARD",
            "travelerType": "CHILD",
            "price": {
                "currency": "NGN",
                "total": 1416032.00,
                "base": 462690.00
            },
            "fareDetailsBySegment": [
                {
                    "segmentId": "11",
                    "cabin": "ECONOMY",
                    "fareBasis": "QA0RAAFACH",
                    "class": "Q"
                },
                {
                    "segmentId": "12",
                    "cabin": "ECONOMY",
                    "fareBasis": "QA0RAAFACH",
                    "class": "Q"
                },
                {
                    "segmentId": "131",
                    "cabin": "ECONOMY",
                    "fareBasis": "QA0RAAFACH",
                    "class": "Q"
                },
                {
                    "segmentId": "132",
                    "cabin": "ECONOMY",
                    "fareBasis": "QA0RAAFACH",
                    "class": "Q"
                }
            ]
        },
        {
            "travelerId": "3",
            "fareOption": "STANDARD",
            "travelerType": "HELD_INFANT",
            "associatedAdultId": "1",
            "price": {
                "currency": "NGN",
                "total": 100170.00,
                "base": 76320.00
            },
            "fareDetailsBySegment": [
                {
                    "segmentId": "11",
                    "cabin": "ECONOMY",
                    "fareBasis": "QA0RAAFAINF",
                    "class": "Q"
                },
                {
                    "segmentId": "12",
                    "cabin": "ECONOMY",
                    "fareBasis": "QA0RAAFAINF",
                    "class": "Q"
                },
                {
                    "segmentId": "131",
                    "cabin": "ECONOMY",
                    "fareBasis": "QA0RAAFAINF",
                    "class": "Q"
                },
                {
                    "segmentId": "132",
                    "cabin": "ECONOMY",
                    "fareBasis": "QA0RAAFAINF",
                    "class": "Q"
                }
            ]
        }
    ],
    "fareRules": {
        "rules": [
            {
                "category": "EXCHANGE",
                "maxPenaltyAmount": "103566"
            },
            {
                "category": "REFUND",
                "maxPenaltyAmount": "483307"
            },
            {
                "category": "REVALIDATION",
                "notApplicable": True
            }
        ]
    }
}

# Save the fixed JSON content back to the file
with open('/mnt/data/fixed_stuff.json', 'w') as file:
    json.dump(fixed_data, file, indent=4)

# Return the path to the fixed file
'/mnt/data/fixed_stuff.json'
