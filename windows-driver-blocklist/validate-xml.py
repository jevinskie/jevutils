#!/usr/bin/env python3

import xmlschema

# Load and validate the XML files against the XSD schema
xsd_schema = xmlschema.XMLSchema("CIPolicy.xsd")

# Validate XML file
is_valid = xsd_schema.is_valid("VulnerableDriverBlockList/SiPolicy_Enforced.xml")
print(f"Is the XML file valid? {is_valid}")
