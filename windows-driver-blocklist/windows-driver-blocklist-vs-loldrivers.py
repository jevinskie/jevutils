#!/usr/bin/env python3
# Install dependencies using: pip install attrs requests pyyaml rich

import argparse
import io
import zipfile
from xml.etree import ElementTree as ET

import attr
import requests
import yaml
from rich.console import Console
from rich.table import Table

# Initialize rich console for pretty printing
console = Console()


@attr.s(auto_attribs=True, kw_only=True)
class VulnerableDriverYAML:
    Id: str | None = None
    Tags: list | None = attr.ib(factory=list)
    Author: str | None = None
    Created: str | None = None
    MitreID: str | None = None
    Category: str | None = None
    Commands: dict | None = attr.ib(factory=dict)
    Detection: list | None = attr.ib(factory=list)
    KnownVulnerableSamples: list | None = attr.ib(factory=list)
    Description: str | None = None
    Usecase: str | None = None


@attr.s(auto_attribs=True, kw_only=True)
class MicrosoftBlocklistEntry:
    VersionEx: str | None = None
    PlatformID: str | None = None
    RuleOption: str | None = None
    FileRuleID: str | None = None
    FriendlyName: str | None = None


def normalize_hash(hash_string):
    return hash_string.replace("-", "").lower()


def download_and_extract_zip(url):
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        extracted_files = {name: z.read(name) for name in z.namelist() if not name.endswith("/")}
    return extracted_files


def extract_zip_to_memory(zip_path):
    extracted_files = {}
    with zipfile.ZipFile(zip_path, "r") as z:
        for file_info in z.infolist():
            if file_info.is_dir():
                continue
            with z.open(file_info) as file:
                extracted_files[file_info.filename] = file.read()
    return extracted_files


def parse_lol_drivers_yaml(file_content):
    yaml_entries = []
    for doc in yaml.safe_load_all(file_content):
        if isinstance(doc, dict):
            filtered_doc = {
                k: v for k, v in doc.items() if k in attr.fields_dict(VulnerableDriverYAML)
            }
            yaml_entries.append(VulnerableDriverYAML(**filtered_doc))
    return yaml_entries


def parse_ms_blocklist_xml(file_content):
    blocklist_entries = []
    ns = {"ns0": "urn:schemas-microsoft-com:sipolicy"}

    tree = ET.ElementTree(ET.fromstring(file_content))
    root = tree.getroot()

    version_ex = root.findtext("ns0:VersionEx", namespaces=ns)
    platform_id = root.findtext("ns0:PlatformID", namespaces=ns)

    for rule in root.findall("ns0:Rules/ns0:Rule", namespaces=ns):
        rule_option = rule.findtext("ns0:Option", namespaces=ns)
        blocklist_entries.append(
            MicrosoftBlocklistEntry(
                VersionEx=version_ex, PlatformID=platform_id, RuleOption=rule_option
            )
        )

    for file_rule in root.findall("ns0:FileRules/ns0:Allow", namespaces=ns):
        file_rule_id = file_rule.get("ID")
        friendly_name = file_rule.get("FriendlyName")
        blocklist_entries.append(
            MicrosoftBlocklistEntry(
                VersionEx=version_ex,
                PlatformID=platform_id,
                FileRuleID=file_rule_id,
                FriendlyName=friendly_name,
            )
        )

    return blocklist_entries


def find_discrepancies_with_summary(lol_drivers, ms_blocklist, verbose=False):
    ms_hashes = set()
    discrepancies = []
    critical_discrepancies = []

    for entry in ms_blocklist:
        if entry.FileRuleID:
            ms_hashes.add(entry.FileRuleID.lower())
        if entry.FriendlyName:
            ms_hashes.add(entry.FriendlyName.lower())
        if entry.RuleOption:
            ms_hashes.add(entry.RuleOption.lower())

    table = Table(title="Discrepancy Report", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="green")

    for driver in lol_drivers:
        is_critical = False
        for sample in driver.KnownVulnerableSamples:
            driver_hashes = {
                normalize_hash(sample.get(h)) for h in ["SHA1", "SHA256"] if sample.get(h)
            }
            if not driver_hashes.intersection(ms_hashes):
                if verbose:
                    table.add_row(
                        driver.Id or "N/A", driver.Category or "N/A", driver.Description or "N/A"
                    )
                else:
                    discrepancies.append(driver)

                if driver.Category and driver.Category.lower() == "vulnerable driver":
                    is_critical = True

        if is_critical:
            critical_discrepancies.append(driver)

    console.print("[bold]Summary:[/bold]")
    console.print(f"Total discrepancies found: {len(discrepancies)}")
    console.print(
        f"Total critical discrepancies (vulnerable drivers): {len(critical_discrepancies)}"
    )

    if critical_discrepancies:
        console.print("[bold red]List of critical discrepancies:[/bold red]")
        for critical_driver in critical_discrepancies:
            console.print(f"- {critical_driver.Id}: {critical_driver.Category}")

    if verbose:
        console.print(table)

    if not verbose:
        return discrepancies


def main():
    parser = argparse.ArgumentParser(
        description="Compare LOLDrivers YAML and Microsoft Blocklist XML."
    )
    parser.add_argument(
        "--lol-drivers",
        default="https://github.com/magicsword-io/LOLDrivers/archive/refs/heads/latestdumps.zip",
        help="Path to LOLDrivers zip file or URL",
    )
    parser.add_argument(
        "--ms-blocklist",
        default="https://aka.ms/VulnerableDriverBlockList",
        help="Path to Microsoft blocklist zip file or URL",
    )
    parser.add_argument(
        "--hash", help="Hash to search for (will normalize and search across both lists)"
    )
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    args = parser.parse_args()

    if args.lol_drivers.startswith("http"):
        lol_drivers_files = download_and_extract_zip(args.lol_drivers)
    else:
        lol_drivers_files = extract_zip_to_memory(args.lol_drivers)

    if args.ms_blocklist.startswith("http"):
        ms_blocklist_files = download_and_extract_zip(args.ms_blocklist)
    else:
        ms_blocklist_files = extract_zip_to_memory(args.ms_blocklist)

    lol_drivers_entries = []
    for file_name, content in lol_drivers_files.items():
        if file_name.endswith(".yaml"):
            lol_drivers_entries.extend(parse_lol_drivers_yaml(content))

    ms_blocklist_entries = []
    for file_name, content in ms_blocklist_files.items():
        if file_name.endswith(".xml"):
            ms_blocklist_entries.extend(parse_ms_blocklist_xml(content))

    if args.hash:
        normalized_hash = normalize_hash(args.hash)
        console.print(f"Searching for hash: {normalized_hash}")
        for driver in lol_drivers_entries:
            for sample in driver.KnownVulnerableSamples:
                driver_hashes = {
                    normalize_hash(sample.get(h)) for h in ["SHA1", "SHA256"] if sample.get(h)
                }
                if normalized_hash in driver_hashes:
                    console.print(f"Match found in LOLDrivers YAML: {attr.asdict(driver)}")

        for block_entry in ms_blocklist_entries:
            if normalized_hash in {
                block_entry.FileRuleID,
                block_entry.FriendlyName,
                block_entry.RuleOption,
            }:
                console.print(f"Match found in Microsoft Blocklist XML: {attr.asdict(block_entry)}")
    else:
        discrepancies = find_discrepancies_with_summary(
            lol_drivers_entries, ms_blocklist_entries, verbose=args.verbose
        )
        if not args.verbose:
            for discrepancy in discrepancies:
                console.print(f"Discrepancy found: {attr.asdict(discrepancy)}")


if __name__ == "__main__":
    main()
