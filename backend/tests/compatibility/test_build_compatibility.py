
def test_build_compatibility_endpoint(client, admin, make_product):
    products = [
        {
            "name": "Ryzen Test 5",
            "category": "cpu",
            "specs": {
                "socket": "AM5",
                "cores": 6,
                "threads": 12,
                "base_clock_ghz": 3.5,
                "boost_clock_ghz": 4.5,
                "tdp_w": 120,
                "supported_memory_types": ["DDR5"],
                "max_memory_gb": 128,
            },
        },
        {
            "name": "B650 Test",
            "category": "placa_madre",
            "specs": {
                "socket": "AM5",
                "chipset": "B650",
                "memory_type": "DDR5",
                "max_memory_gb": 128,
                "memory_slots": 4,
                "form_factor": "ATX",
                "sata_ports": 4,
                "supported_cpu_models": [
                    {"model": "Ryzen Test 5"}
                ],
                "m2_slots_details": [
                    {
                        "interface": "PCIe",
                        "supported_form_factors": ["M.2 2280"],
                        "quantity": 1,
                    }
                ],
                "pcie_slots_details": [
                    {
                        "generation": "4.0",
                        "physical_size": "x16",
                        "electrical_lanes": 16,
                        "quantity": 1,
                    }
                ],
            },
        },
        {
            "name": "DDR5 Test",
            "category": "ram",
            "specs": {
                "memory_type": "DDR5",
                "capacity_per_module_gb": 16,
                "total_capacity_gb": 32,
                "module_count": 2,
                "frequency_mhz": 5600,
                "cas_latency_cl": 36,
                "form_factor": "DIMM",
                "memory_profile": ["EXPO"],
            },
        },
        {
            "name": "RTX Test",
            "category": "gpu",
            "specs": {
                "interface": {
                    "generation": "4.0",
                    "physical_size": "x16",
                    "electrical_lanes": 16,
                },
                "vram_gb": 12,
                "length_mm": 250,
                "board_power_w": 200,
                "recommended_psu_w": 650,
                "power_connectors_required": [
                    {"type": "8-pin", "quantity": 1}
                ],
            },
        },
        {
            "name": "750W Test",
            "category": "fuente",
            "specs": {
                "wattage_w": 750,
                "certification": "80 Plus Gold",
                "power_connectors": [
                    {
                        "type": "8-pin",
                        "quantity": 1,
                        "native": True,
                    }
                ],
            },
        },
        {
            "name": "Cooler Test",
            "category": "refrigeracion",
            "specs": {
                "cooling_type": "Aire",
                "supported_sockets": ["AM5"],
                "tdp_rating_w": 180,
            },
        },
        {
            "name": "NVMe Test",
            "category": "almacenamiento",
            "specs": {
                "storage_type": "SSD",
                "capacity_gb": 1000,
                "interface": {
                    "protocol": "NVMe",
                    "connection": "PCIe",
                    "generation": "4.0",
                },
                "form_factor": "M.2 2280",
            },
        },
    ]

    created_products = [
        make_product(
            name=product["name"],
            category=product["category"],
            specs=product["specs"],
        )
        for product in products
    ]

    response = client.post(
        "/api/builds/compatibility",
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                }
                for product in created_products
            ]
        },
        headers=admin,
    )

    assert response.status_code == 200, response.text

    result = response.json()

    assert result["status"] in {
        "compatible",
        "warning",
        "incompatible",
        "review_required",
    }
    assert result["total_rules"] > 0
    assert "results" in result
    assert "indeterminate_count" not in result


def test_build_compatibility_rejects_ineligible_product(
    client,
    admin,
    make_product,
):
    product = make_product(
        category="gpu",
        specs={},
    )

    response = client.post(
        "/api/builds/compatibility",
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                }
            ]
        },
        headers=admin,
    )

    assert response.status_code == 400
