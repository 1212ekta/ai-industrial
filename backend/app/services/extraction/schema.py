"""Fixed entity/relation taxonomy used by the extraction prompt and downstream graph writes."""

ENTITY_TYPES = [
    "Equipment",       # generic equipment ID / tag, e.g. "P101"
    "Pump",
    "Valve",
    "Motor",
    "Boiler",
    "Compressor",
    "Temperature",
    "Pressure",
    "MaintenanceDate",
    "Engineer",
    "Vendor",
    "OEM",
    "SerialNumber",
    "FailureType",
    "SafetyProcedure",
    "InspectionReport",
    "RiskLevel",
    "MaintenanceFrequency",
    "ComplianceStandard",
]

RELATION_TYPES = [
    "CONNECTED_TO",
    "INSPECTED_BY",
    "MENTIONED_IN",
    "HAS_FAILURE",
    "FOLLOWS",
    "MAINTAINED_BY",
    "SUPPLIED_BY",
]

EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ENTITY_TYPES},
                    "value": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["type", "value", "confidence"],
            },
        },
        "relations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "relation": {"type": "string", "enum": RELATION_TYPES},
                    "target": {"type": "string"},
                },
                "required": ["source", "relation", "target"],
            },
        },
    },
    "required": ["entities", "relations"],
}
