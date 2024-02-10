sites = [
    {
        "Address": {
            "label": "Deutschland",
            "countryName": "Deutschland"
        }
    },
    {
        "Address": {
            "label": "Belgium",
            "countryName": "Belgium"
        }
    }
]

sites2 = [
    {
        "Address": {
            "label": "Spain",
            "countryName": "Spain"
        }
    },
    {
        "Address": {
            "label": "Portugal",
            "countryName": "Portugal"
        }
    }
]

listings = [
    {
        "productDescription": "listing1",
        "sites": sites
    },
    {
        "productDescription": "listing2",
        "sites": sites2
    }
]

result = [item["productDescription"] for item in listings] + [site["Address"]["countryName"] for item in listings for site in item["sites"]]

if __name__ == "__main__":
    print(result)