"""
BeeKeeper — Test data for simulations.
Xray-style alerts, vulnerabilities, and packages for demo runs.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Alert:
    severity: str  # Critical, Major, Minor
    message: str
    timestamp: str
    issue_count: int


@dataclass
class Vulnerability:
    cve_id: str
    description: str
    severity: str


@dataclass
class Package:
    name: str
    status: str  # Normal, Vulnerable, etc.


def get_recent_alerts() -> list[Alert]:
    """My Recent Alerts — simulation data."""
    base = datetime.now()
    return [
        Alert("Minor", "Issue in openssl package — certificate validation bypass in OpenSSL 3.0.x allows man-in-the-middle when renegotiating", (base - timedelta(hours=2)).strftime("%b %d, %Y %I:%M %p"), 1),
        Alert("Major", "Artifact nginx:1.21-alpine was added to repository docker-hub with vulnerability CVE-2022-41741", (base - timedelta(days=1)).strftime("%b %d, %Y %I:%M %p"), 3),
        Alert("Critical", "Artifact jackson-databind-2.13.4.jar was added to Repository maven-central with remote code execution vulnerability", (base - timedelta(days=2)).strftime("%b %d, %Y %I:%M %p"), 1),
        Alert("Major", "Artifact log4j-core-2.17.1.jar was added to Repository joe-repo with JNDI injection risk", (base - timedelta(days=3)).strftime("%b %d, %Y %I:%M %p"), 2),
        Alert("Minor", "Artifact python-requests-2.28.0 identified with potential SSRF in redirect handling", (base - timedelta(days=4)).strftime("%b %d, %Y %I:%M %p"), 1),
    ]


def get_recent_vulnerabilities() -> list[Vulnerability]:
    """Recent Vulnerabilities — CVE list."""
    return [
        Vulnerability(
            "CVE-2024-21626",
            "runc path traversal allows container escape — process.cwd and leaked fds enable an attacker to escape the container and overwrite host binary.",
            "Critical"
        ),
        Vulnerability(
            "CVE-2023-44487",
            "HTTP/2 Rapid Reset — denial of service attack enabling inexpensive DDoS with minimal bandwidth.",
            "High"
        ),
        Vulnerability(
            "CVE-2022-41741",
            "net/http, net/textproto: HTTP and MIME header parsing may accept excessively large header values, causing a denial of service.",
            "High"
        ),
        Vulnerability(
            "CVE-2010-2253",
            "lwp-download in libwww-perl before 5.835 does not reject downloads to filenames that begin with a . (dot) character, which allows remote servers to overwrite arbitrary files.",
            "Minor"
        ),
        Vulnerability(
            "CVE-2016-1664",
            "The HistoryController:UpdateForCommit function in Chromium allows remote attackers to cause a denial of service via crafted data.",
            "Minor"
        ),
    ]


def get_recent_packages() -> list[Package]:
    """Recent Packages — indexed component list."""
    return [
        Package("antlr:antlr", "Normal"),
        Package("apache-beanutils:commons-beanutils", "Normal"),
        Package("apache-lang:commons-lang", "Normal"),
        Package("backbone.databinding", "Normal"),
        Package("backbone.datastore", "Vulnerable"),
        Package("classworlds:classworlds", "Normal"),
        Package("com.fasterxml.jackson.core:jackson-annotations", "Normal"),
        Package("com.fasterxml.jackson.core:jackson-databind", "Vulnerable"),
        Package("nginx:1.21-alpine", "Vulnerable"),
        Package("alpine:3.18", "Normal"),
        Package("python:3.11-slim", "Vulnerable"),
        Package("node:18-alpine", "Normal"),
        Package("log4j:log4j-core", "Vulnerable"),
        Package("requests", "Normal"),
        Package("openssl", "Vulnerable"),
    ]


def get_metrics(scanned_images: int = 12, indexed_packages: int = 194, total_alerts: int = 37) -> tuple[int, int, int]:
    """Returns (scanned_images, indexed_packages, total_alerts)."""
    return scanned_images, indexed_packages, total_alerts


def get_sync_status(percent: int = 94, current: int = 735, total: int = 761) -> dict:
    """Database/Sync progress for simulation."""
    return {"percent": percent, "current": current, "total": total}


SUPPORTED_TECHNOLOGIES = [
    ("npm", "Node.js packages"),
    ("Maven", "Java artifacts"),
    ("Debian", "apt packages"),
    ("Python", "pip/PyPI"),
    ("Docker", "Container images"),
    ("RPM", "Red Hat packages"),
    ("Go", "Go modules"),
    ("NuGet", ".NET packages"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# ENTERPRISE SIMULATION — 857,284 vulnerabilities across unpatched estate
# ═══════════════════════════════════════════════════════════════════════════════

TOTAL_ENTERPRISE_VULNS = 857_284


@dataclass
class InventoryCluster:
    id: str
    name: str
    platform: str  # EKS, AKS, GKE, on-prem
    nodes: int
    vuln_count: int
    last_scanned: str
    status: str  # unpatched, unmonitored


@dataclass
class InventoryImage:
    id: str
    name: str
    registry: str
    tag: str
    vuln_count: int
    critical: int
    high: int
    status: str


@dataclass
class InventoryRepo:
    id: str
    name: str
    type: str  # Maven, npm, PyPI, etc.
    artifact_count: int
    vuln_count: int
    status: str


@dataclass
class InventoryYamlFunc:
    id: str
    name: str
    source: str  # k8s manifests, Helm, Serverless, ArgoCD
    file_count: int
    vuln_count: int
    status: str


@dataclass
class VulnSummary:
    cve_id: str
    description: str
    severity: str
    affected_count: int
    exploitability: str


def get_enterprise_clusters() -> list[InventoryCluster]:
    """Unpatched, unmonitored Kubernetes/container clusters."""
    base = datetime.now()
    return [
        InventoryCluster("clus-prod-us-east-1", "prod-us-east-1", "EKS", 48, 124_530, (base - timedelta(days=90)).strftime("%Y-%m-%d"), "unpatched"),
        InventoryCluster("clus-staging-eu-west", "staging-eu-west", "EKS", 12, 38_200, (base - timedelta(days=120)).strftime("%Y-%m-%d"), "unmonitored"),
        InventoryCluster("clus-dev-aps1", "dev-ap-south-1", "EKS", 8, 22_100, (base - timedelta(days=60)).strftime("%Y-%m-%d"), "unpatched"),
        InventoryCluster("clus-legacy-dc1", "legacy-datacenter-1", "on-prem", 24, 89_400, (base - timedelta(days=365)).strftime("%Y-%m-%d"), "unmonitored"),
        InventoryCluster("clus-aks-prod", "prod-aks-west", "AKS", 32, 67_800, (base - timedelta(days=45)).strftime("%Y-%m-%d"), "unpatched"),
        InventoryCluster("clus-gke-analytics", "analytics-gke", "GKE", 16, 41_300, (base - timedelta(days=200)).strftime("%Y-%m-%d"), "unmonitored"),
    ]


def get_enterprise_images() -> list[InventoryImage]:
    """Docker images across registries — unpatched."""
    return [
        InventoryImage("img-1", "nginx", "docker.io", "1.21-alpine", 4_200, 120, 890, "unpatched"),
        InventoryImage("img-2", "node", "docker.io", "18-alpine", 8_100, 45, 1_200, "unpatched"),
        InventoryImage("img-3", "python", "docker.io", "3.9-slim", 12_400, 89, 2_100, "unpatched"),
        InventoryImage("img-4", "postgres", "docker.io", "13-alpine", 3_800, 22, 650, "unpatched"),
        InventoryImage("img-5", "redis", "docker.io", "6-alpine", 2_100, 11, 420, "unpatched"),
        InventoryImage("img-6", "api-gateway", "acr.azure.io", "v2.1.4", 15_600, 210, 4_200, "unpatched"),
        InventoryImage("img-7", "auth-service", "ecr.aws.io", "sha256:a1b2c3", 9_800, 78, 1_800, "unpatched"),
        InventoryImage("img-8", "alpine", "docker.io", "3.15", 18_200, 340, 5_600, "unpatched"),
        InventoryImage("img-9", "java/openjdk", "docker.io", "11-jre-slim", 22_100, 156, 6_700, "unpatched"),
        InventoryImage("img-10", "ubuntu", "docker.io", "20.04", 31_400, 520, 12_300, "unpatched"),
    ]


def get_enterprise_repos() -> list[InventoryRepo]:
    """Artifact repositories — Maven, npm, PyPI."""
    return [
        InventoryRepo("repo-maven-core", "maven-central-proxy", "Maven", 2_400, 156_200, "unpatched"),
        InventoryRepo("repo-npm-frontend", "npm-internal", "npm", 1_800, 94_500, "unmonitored"),
        InventoryRepo("repo-pypi-ml", "pypi-ml-mirror", "PyPI", 420, 38_600, "unpatched"),
        InventoryRepo("repo-docker-hub", "docker-hub-cache", "Docker", 890, 198_400, "unpatched"),
        InventoryRepo("repo-nuget-legacy", "nuget-legacy", "NuGet", 320, 22_100, "unmonitored"),
    ]


def get_enterprise_yaml_funcs() -> list[InventoryYamlFunc]:
    """K8s manifests, Helm charts, serverless functions."""
    return [
        InventoryYamlFunc("yaml-1", "k8s-prod-manifests", "Kubernetes", 180, 45_200, "unpatched"),
        InventoryYamlFunc("yaml-2", "helm-charts-platform", "Helm", 24, 32_100, "unmonitored"),
        InventoryYamlFunc("yaml-3", "serverless-api", "Serverless/Lambda", 12, 8_400, "unpatched"),
        InventoryYamlFunc("yaml-4", "argocd-apps", "ArgoCD", 56, 18_600, "unmonitored"),
        InventoryYamlFunc("yaml-5", "terraform-k8s", "Terraform+K8s", 8, 12_300, "unpatched"),
    ]


def get_enterprise_vuln_breakdown() -> dict:
    """Severity breakdown for 857,284 vulnerabilities."""
    return {
        "critical": 12_840,
        "high": 98_500,
        "medium": 412_200,
        "low": 298_744,
        "info": 35_000,
    }


def get_enterprise_kpis() -> dict:
    """KPI cards: % risks, total risks, risk analysis progress, response progress."""
    return {
        "pct_risks": 38.4,
        "total_risks": TOTAL_ENTERPRISE_VULNS,
        "risk_analysis_progress": 86.7,
        "response_progress": 55.7,
    }


def get_enterprise_risk_heatmap() -> dict:
    """Severity × Likelihood heat map. Rows: Severe→Insignificant; Cols: Rare→Almost Certain."""
    # Rows (Severity): Severe, Major, Moderate, Minor, Insignificant
    # Cols (Likelihood): Rare, Unlikely, Moderate, Likely, Almost Certain
    return {
        "rows": ["Severe", "Major", "Moderate", "Minor", "Insignificant"],
        "cols": ["Rare", "Unlikely", "Moderate", "Likely", "Almost Certain"],
        "matrix": [
            [12, 8, 45, 120, 89],   # Severe
            [34, 56, 180, 220, 95],  # Major
            [180, 240, 520, 380, 120],  # Moderate
            [420, 380, 450, 280, 90],   # Minor
            [150, 120, 85, 45, 12],   # Insignificant
        ],
    }


def get_enterprise_action_breakdown() -> dict:
    """Action plan status: Deferred, TBD, Implemented, In Progress."""
    return {
        "Deferred": 53,
        "TBD": 23,
        "Implemented": 4,
        "In Progress": 20,
    }


def get_enterprise_top_vulns() -> list[VulnSummary]:
    """Top CVEs by affected asset count."""
    return [
        VulnSummary("CVE-2024-21626", "runc container escape — path traversal", "Critical", 48_200, "High"),
        VulnSummary("CVE-2023-44487", "HTTP/2 Rapid Reset — DDoS", "High", 156_000, "High"),
        VulnSummary("CVE-2022-41741", "Go net/http header DoS", "High", 89_400, "Medium"),
        VulnSummary("CVE-2021-44228", "Log4j JNDI injection", "Critical", 23_100, "Critical"),
        VulnSummary("CVE-2023-22515", "Atlassian Confluence RCE", "Critical", 8_200, "High"),
        VulnSummary("CVE-2023-46604", "Apache ActiveMQ RCE", "Critical", 12_600, "High"),
        VulnSummary("CVE-2022-36934", "containerd-shim escape", "High", 67_300, "Medium"),
        VulnSummary("CVE-2023-38545", "curl SOCKS5 heap buffer overflow", "High", 42_100, "Medium"),
        VulnSummary("CVE-2022-42916", "glibc buffer overflow", "High", 124_500, "Medium"),
        VulnSummary("CVE-2023-44487", "HTTP/2 Rapid Reset", "High", 156_000, "High"),
    ]


def get_all_inventory_components() -> list[dict]:
    """~1,500 mixed components: clusters, images, repos, yaml. Each has type, id, name, summary, details."""
    import random
    base = datetime.now()
    random.seed(42)
    components = []

    # Clusters ~180
    platforms = ["EKS", "AKS", "GKE", "on-prem", "OpenShift"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1", "eu-central-1", "ap-northeast-1"]
    envs = ["prod", "staging", "dev", "qa", "sandbox"]
    for i in range(180):
        plat = platforms[i % len(platforms)]
        reg = regions[i % len(regions)]
        env = envs[i % len(envs)]
        name = f"{env}-{reg}" if i < 90 else f"{env}-cluster-{i}"
        nodes = random.randint(4, 64)
        vuln = random.randint(2_000, 150_000)
        status = "unpatched" if i % 3 != 1 else "unmonitored"
        last = (base - timedelta(days=random.randint(7, 365))).strftime("%Y-%m-%d")
        components.append({
            "type": "cluster", "id": f"clus-{i}", "name": name,
            "summary": f"{plat} • {nodes} nodes • {vuln:,} vulns",
            "status": status, "vuln_count": vuln,
            "details": f"Platform: {plat} | Nodes: {nodes} | Region: {reg} | Environment: {env} | Last scanned: {last} | Status: {status}",
        })

    # Docker images ~800
    bases = ["nginx", "node", "python", "alpine", "ubuntu", "postgres", "redis", "java/openjdk", "golang", "rust"]
    registries = ["docker.io", "ecr.aws.io", "acr.azure.io", "gcr.io", "ghcr.io"]
    tags = ["alpine", "slim", "latest", "18", "20", "22", "3.9", "3.11", "1.21", "1.25", "13", "15"]
    for i in range(800):
        base_img = bases[i % len(bases)]
        reg = registries[i % len(registries)]
        tag = f"{tags[i % len(tags)]}" if i % 5 == 0 else f"{tags[i % len(tags)]}-{i % 10}"
        vuln = random.randint(500, 35_000)
        c = random.randint(1, min(500, vuln // 10))
        h = random.randint(10, min(5000, vuln - c))
        components.append({
            "type": "image", "id": f"img-{i}", "name": f"{base_img}:{tag}",
            "summary": f"{vuln:,} vulns (C:{c} H:{h})",
            "status": "unpatched", "vuln_count": vuln,
            "details": f"Registry: {reg} | Tag: {tag} | Vulnerabilities: {vuln:,} | Critical: {c} | High: {h} | Status: unpatched",
        })

    # Repos ~320
    repo_types = ["Maven", "npm", "PyPI", "Docker", "NuGet", "Go"]
    prefixes = ["platform", "frontend", "api", "data", "ml", "core", "legacy", "shared"]
    for i in range(320):
        rtype = repo_types[i % len(repo_types)]
        prefix = prefixes[i % len(prefixes)]
        name = f"{prefix}-{rtype.lower()}-{'proxy' if i % 4 == 0 else 'internal'}" + (f"-{i}" if i > 40 else "")
        arts = random.randint(100, 5000)
        vuln = random.randint(5_000, 200_000)
        status = "unpatched" if i % 3 != 2 else "unmonitored"
        components.append({
            "type": "repo", "id": f"repo-{i}", "name": name,
            "summary": f"{rtype} • {arts:,} artifacts • {vuln:,} vulns",
            "status": status, "vuln_count": vuln,
            "details": f"Type: {rtype} | Artifacts: {arts:,} | Vulnerabilities: {vuln:,} | Status: {status}",
        })

    # YAML / configs ~200
    sources = ["Kubernetes", "Helm", "Serverless/Lambda", "ArgoCD", "Terraform+K8s", "Tekton", "Kustomize"]
    for i in range(200):
        src = sources[i % len(sources)]
        name = f"{src.lower().replace('/', '-')}-{['manifests', 'charts', 'apps', 'workflows'][i % 4]}" + (f"-{i}" if i > 30 else "")
        files = random.randint(5, 250)
        vuln = random.randint(1_000, 50_000)
        status = "unpatched" if i % 3 != 0 else "unmonitored"
        components.append({
            "type": "yaml", "id": f"yaml-{i}", "name": name,
            "summary": f"{src} • {files} files • {vuln:,} vulns",
            "status": status, "vuln_count": vuln,
            "details": f"Source: {src} | Files: {files} | Vulnerabilities: {vuln:,} | Status: {status}",
        })

    random.shuffle(components)
    return components


def get_enterprise_remediation_options() -> list[dict]:
    """Marketplace-style remediation: patch, upgrade, or decommission."""
    return [
        {"id": "patch-cluster-prod", "type": "cluster", "name": "Patch prod-us-east-1 (EKS)", "vulns_removed": 124_530, "action": "patch", "effort": "Medium"},
        {"id": "upgrade-nginx", "type": "image", "name": "Upgrade nginx:1.21 → 1.25", "vulns_removed": 4_200, "action": "upgrade", "effort": "Low"},
        {"id": "decommission-legacy", "type": "cluster", "name": "Decommission legacy-datacenter-1", "vulns_removed": 89_400, "action": "decommission", "effort": "High"},
        {"id": "patch-maven-repo", "type": "repo", "name": "Patch maven-central-proxy artifacts", "vulns_removed": 156_200, "action": "patch", "effort": "High"},
        {"id": "upgrade-alpine", "type": "image", "name": "Upgrade alpine:3.15 → 3.19", "vulns_removed": 18_200, "action": "upgrade", "effort": "Low"},
        {"id": "patch-staging", "type": "cluster", "name": "Patch staging-eu-west (EKS)", "vulns_removed": 38_200, "action": "patch", "effort": "Medium"},
        {"id": "upgrade-node", "type": "image", "name": "Upgrade node:18 → node:20 LTS", "vulns_removed": 8_100, "action": "upgrade", "effort": "Low"},
        {"id": "patch-k8s-manifests", "type": "yaml", "name": "Patch k8s-prod-manifests base images", "vulns_removed": 45_200, "action": "patch", "effort": "Medium"},
        {"id": "decommission-dev-old", "type": "cluster", "name": "Decommission dev-ap-south-1 (legacy)", "vulns_removed": 22_100, "action": "decommission", "effort": "Low"},
        {"id": "upgrade-ubuntu", "type": "image", "name": "Upgrade ubuntu:20.04 → 22.04", "vulns_removed": 31_400, "action": "upgrade", "effort": "Medium"},
    ]


def _unused_get_all_inventory_components() -> list[dict]:
    """~1,500 mixed components (clusters, images, repos, yaml) — single-line entries with details."""
    import random
    base = datetime.now()
    random.seed(42)
    items: list[dict] = []

    # Clusters: ~180 (regions × envs × platforms)
    platforms = ["EKS", "AKS", "GKE", "on-prem"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-south-1", "ap-northeast-1"]
    envs = ["prod", "staging", "dev", "sandbox"]
    for i, (plat, reg, env) in enumerate(
        (p, r, e) for p in platforms for r in regions for e in envs
    )[:180]:
        nodes = random.randint(4, 64)
        vuln = random.randint(2_000, 120_000)
        status = "unpatched" if random.random() < 0.6 else "unmonitored"
        days = random.randint(7, 365)
        items.append({
            "type": "cluster", "id": f"clus-{i}", "name": f"{env}-{reg}",
            "summary": f"{plat} • {nodes} nodes • {vuln:,} vulns",
            "status": status,
            "vuln_count": vuln,
            "details": {"platform": plat, "nodes": nodes, "region": reg, "env": env,
                        "last_scanned": (base - timedelta(days=days)).strftime("%Y-%m-%d")},
        })

    # Docker images: ~800 (base × tags + app images)
    bases = ["nginx", "node", "python", "alpine", "ubuntu", "postgres", "redis", "java/openjdk", "golang", "ruby"]
    tags = ["alpine", "slim", "latest", "20.04", "18", "3.9", "1.21", "13", "6", "11-jre"]
    regs = ["docker.io", "ecr.aws.io", "gcr.io", "acr.azure.io"]
    for i in range(800):
        base_name = random.choice(bases)
        tag = random.choice(tags)
        reg = random.choice(regs)
        vuln = random.randint(50, 25_000)
        c = random.randint(1, min(500, vuln // 10))
        h = random.randint(10, min(3000, vuln // 3))
        items.append({
            "type": "image", "id": f"img-{i}", "name": f"{base_name}:{tag}",
            "summary": f"{reg} • {vuln:,} vulns (C:{c} H:{h})",
            "status": "unpatched",
            "vuln_count": vuln,
            "details": {"registry": reg, "critical": c, "high": h},
        })

    # Repos: ~320 (type × name patterns)
    repo_types = ["Maven", "npm", "PyPI", "Docker", "NuGet", "Go"]
    prefixes = ["platform-", "app-", "lib-", "core-", "api-", "data-"]
    for i in range(320):
        rtype = random.choice(repo_types)
        name = f"{random.choice(prefixes)}{random.choice(['core','frontend','backend','ml','gateway'])}-{i % 50}"
        artifacts = random.randint(50, 5000)
        vuln = random.randint(500, 200_000)
        status = "unpatched" if random.random() < 0.65 else "unmonitored"
        items.append({
            "type": "repo", "id": f"repo-{i}", "name": name,
            "summary": f"{rtype} • {artifacts:,} artifacts • {vuln:,} vulns",
            "status": status,
            "vuln_count": vuln,
            "details": {"repo_type": rtype, "artifact_count": artifacts},
        })

    # YAML / configs: ~200
    yaml_sources = ["Kubernetes", "Helm", "Serverless/Lambda", "ArgoCD", "Terraform+K8s", "Tekton"]
    for i in range(200):
        src = random.choice(yaml_sources)
        name = f"{src.lower().replace('/','-')}-{random.choice(['prod','dev','pipeline'])}-{i % 30}"
        files = random.randint(5, 300)
        vuln = random.randint(100, 50_000)
        status = "unpatched" if random.random() < 0.6 else "unmonitored"
        items.append({
            "type": "yaml", "id": f"yaml-{i}", "name": name,
            "summary": f"{src} • {files} files • {vuln:,} vulns",
            "status": status,
            "vuln_count": vuln,
            "details": {"source": src, "file_count": files},
        })

    random.shuffle(items)
    return items


def get_enterprise_remediation_options() -> list[dict]:
    """Marketplace-style remediation: patch, upgrade, or decommission."""
    return [
        {"id": "patch-cluster-prod", "type": "cluster", "name": "Patch prod-us-east-1 (EKS)", "vulns_removed": 124_530, "action": "patch", "effort": "Medium"},
        {"id": "upgrade-nginx", "type": "image", "name": "Upgrade nginx:1.21 → 1.25", "vulns_removed": 4_200, "action": "upgrade", "effort": "Low"},
        {"id": "decommission-legacy", "type": "cluster", "name": "Decommission legacy-datacenter-1", "vulns_removed": 89_400, "action": "decommission", "effort": "High"},
        {"id": "patch-maven-repo", "type": "repo", "name": "Patch maven-central-proxy artifacts", "vulns_removed": 156_200, "action": "patch", "effort": "High"},
        {"id": "upgrade-alpine", "type": "image", "name": "Upgrade alpine:3.15 → 3.19", "vulns_removed": 18_200, "action": "upgrade", "effort": "Low"},
        {"id": "patch-staging", "type": "cluster", "name": "Patch staging-eu-west (EKS)", "vulns_removed": 38_200, "action": "patch", "effort": "Medium"},
        {"id": "upgrade-node", "type": "image", "name": "Upgrade node:18 → node:20 LTS", "vulns_removed": 8_100, "action": "upgrade", "effort": "Low"},
        {"id": "patch-k8s-manifests", "type": "yaml", "name": "Patch k8s-prod-manifests base images", "vulns_removed": 45_200, "action": "patch", "effort": "Medium"},
        {"id": "decommission-dev-old", "type": "cluster", "name": "Decommission dev-ap-south-1 (legacy)", "vulns_removed": 22_100, "action": "decommission", "effort": "Low"},
        {"id": "upgrade-ubuntu", "type": "image", "name": "Upgrade ubuntu:20.04 → 22.04", "vulns_removed": 31_400, "action": "upgrade", "effort": "Medium"},
    ]


def get_all_inventory_components() -> list[dict]:
    """~1,500 mixed components: clusters, images, repos, yaml — single-line entries, hyperlinkable to details."""
    base = datetime.now()
    out = []
    platforms = ["EKS", "AKS", "GKE", "on-prem", "OpenShift", "k3s"]
    regions = ["us-east-1", "eu-west-1", "ap-south-1", "us-west-2", "eu-central-1", "ap-northeast-1"]
    envs = ["prod", "staging", "dev", "qa", "sandbox"]
    statuses = ["unpatched", "unpatched", "unmonitored"]  # bias unpatched
    # Clusters ~180
    for i in range(180):
        p, r, e = platforms[i % 6], regions[i % 6], envs[i % 5]
        n = 4 + (i % 48)
        v = 5_000 + (i * 1_200) % 120_000
        d = (base - timedelta(days=30 + (i % 330))).strftime("%Y-%m-%d")
        s = statuses[i % 3]
        out.append({
            "type": "cluster", "id": f"clus-{i}", "name": f"{e}-{r.replace('-','')}",
            "summary": f"{e}-{r} • {p} • {n} nodes • {v:,} vulns",
            "details": {"platform": p, "nodes": n, "vuln_count": v, "last_scanned": d, "status": s},
        })
    # Docker images ~800
    bases = ["nginx", "node", "python", "alpine", "ubuntu", "postgres", "redis", "java/openjdk", "golang", "ruby", "php", "dotnet"]
    regs = ["docker.io", "ecr.aws.io", "acr.azure.io", "gcr.io", "ghcr.io"]
    for i in range(800):
        b, r = bases[i % 12], regs[i % 5]
        tag = f"{(i % 20) + 1}.{(i % 10)}" + (["-alpine", "-slim", ""][i % 3])
        v, c, h = 200 + (i * 80) % 30_000, (i % 50) + 5, (i % 200) + 50
        out.append({
            "type": "image", "id": f"img-{i}", "name": f"{b}:{tag}",
            "summary": f"{b}:{tag} • {v:,} vulns (C:{c} H:{h})",
            "details": {"registry": r, "vuln_count": v, "critical": c, "high": h, "status": "unpatched"},
        })
    # Repos ~320
    repotypes = ["Maven", "npm", "PyPI", "NuGet", "Go", "Docker"]
    for i in range(320):
        t = repotypes[i % 6]
        arts = 100 + (i * 50) % 5_000
        v = 1_000 + (i * 600) % 200_000
        s = statuses[i % 3]
        out.append({
            "type": "repo", "id": f"repo-{i}", "name": f"{t.lower()}-{['core','internal','mirror','cache','legacy'][i%5]}-{i}",
            "summary": f"{t} • {arts:,} artifacts • {v:,} vulns",
            "details": {"type": t, "artifact_count": arts, "vuln_count": v, "status": s},
        })
    # YAML ~200
    yaml_sources = ["Kubernetes", "Helm", "Serverless/Lambda", "ArgoCD", "Terraform", "Tekton"]
    for i in range(200):
        src = yaml_sources[i % 6]
        fc = 4 + (i % 200)
        v = 500 + (i * 300) % 50_000
        s = statuses[i % 3]
        out.append({
            "type": "yaml", "id": f"yaml-{i}", "name": f"{src.lower().replace('/','-')}-config-{i}",
            "summary": f"{src} • {fc} files • {v:,} vulns",
            "details": {"source": src, "file_count": fc, "vuln_count": v, "status": s},
        })
    return out


def get_all_inventory_components() -> list[dict]:
    """~1,500 mixed components: clusters, images, repos, YAML. Single-line entries with expandable details."""
    base = datetime.now()
    components: list[dict] = []
    platforms = ["EKS", "AKS", "GKE", "on-prem", "OpenShift"]
    regions = ["us-east-1", "eu-west-1", "ap-south-1", "us-west-2", "eu-central-1", "prod", "staging", "dev"]
    statuses = ["unpatched", "unpatched", "unmonitored"]

    # Clusters (~180)
    for i in range(180):
        r, plat = regions[i % len(regions)], platforms[i % len(platforms)]
        nodes = 8 + (i % 48)
        vuln = 5_000 + (i * 700) % 120_000
        status = statuses[i % 3]
        last = (base - timedelta(days=30 + i % 365)).strftime("%Y-%m-%d")
        name = f"{r}-cluster-{i:03d}" if "us-" in r or "eu-" in r or "ap-" in r else f"{plat}-{r}-{i:03d}"
        components.append({
            "type": "cluster", "id": f"clus-{i}",
            "name": name, "summary": f"{plat} • {nodes} nodes • {vuln:,} vulns",
            "details": {"platform": plat, "nodes": nodes, "vuln_count": vuln, "status": status, "last_scanned": last},
        })

    # Docker images (~800)
    bases = ["nginx", "node", "python", "alpine", "ubuntu", "postgres", "redis", "java/openjdk", "golang", "ruby"]
    registries = ["docker.io", "ecr.aws.io", "acr.azure.io", "gcr.io", "ghcr.io"]
    tags = ["alpine", "slim", "latest", "bullseye", "20.04", "18", "3.9", "1.21", "13", "6.2"]
    for i in range(800):
        b, reg, tag = bases[i % len(bases)], registries[i % len(registries)], tags[i % len(tags)]
        name = f"{b}:{tag}" if b in ["nginx", "node", "python"] else f"{b}:{tag}-alpine" if "alpine" in tag else f"{b}:{tag}"
        vuln = 400 + (i * 50) % 35_000
        c, h = max(1, vuln // 40), max(1, vuln // 8)
        components.append({
            "type": "image", "id": f"img-{i}",
            "name": name, "summary": f"{vuln:,} vulns (C:{c} H:{h})",
            "details": {"registry": reg, "vuln_count": vuln, "critical": c, "high": h, "status": "unpatched"},
        })

    # Repos (~320)
    repo_types = ["Maven", "npm", "PyPI", "Docker", "NuGet", "Go"]
    prefixes = ["platform-", "frontend-", "backend-", "data-", "ml-", "api-"]
    for i in range(320):
        rt, px = repo_types[i % len(repo_types)], prefixes[i % len(prefixes)]
        art = 50 + (i * 20) % 5_000
        vuln = 1_000 + (i * 500) % 200_000
        status = statuses[i % 3]
        name = f"{px}{rt.lower()}-repo-{i:03d}"
        components.append({
            "type": "repo", "id": f"repo-{i}",
            "name": name, "summary": f"{rt} • {art:,} artifacts • {vuln:,} vulns",
            "details": {"type": rt, "artifact_count": art, "vuln_count": vuln, "status": status},
        })

    # YAML / configs (~200)
    yaml_sources = ["Kubernetes", "Helm", "Serverless", "ArgoCD", "Terraform", "Tekton"]
    for i in range(200):
        src = yaml_sources[i % len(yaml_sources)]
        files = 5 + (i % 200)
        vuln = 200 + (i * 100) % 50_000
        status = statuses[i % 3]
        name = f"{src.lower()}-config-{i:03d}"
        components.append({
            "type": "yaml", "id": f"yaml-{i}",
            "name": name, "summary": f"{src} • {files} files • {vuln:,} vulns",
            "details": {"source": src, "file_count": files, "vuln_count": vuln, "status": status},
        })

    return components


def get_all_inventory_components(
    n_clusters: int = 180,
    n_images: int = 820,
    n_repos: int = 320,
    n_yaml: int = 180,
) -> list[dict]:
    """~1,500 mixed components — single-line expandable entries with device details."""
    import random
    random.seed(42)
    base = datetime.now()
    out = []

    platforms = ["EKS", "AKS", "GKE", "on-prem", "OpenShift", "kind", "k3s"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-south-1", "ap-northeast-1"]
    envs = ["prod", "staging", "dev", "qa", "sandbox"]
    statuses = ["unpatched", "unmonitored"]

    for i in range(n_clusters):
        plat = platforms[i % len(platforms)]
        reg = regions[i % len(regions)]
        env = envs[i % len(envs)]
        name = f"{env}-{reg}" if plat != "on-prem" else f"legacy-dc-{i % 12 + 1}"
        nodes = random.randint(4, 64)
        vuln = random.randint(2_000, 85_000)
        last = (base - timedelta(days=random.randint(7, 365))).strftime("%Y-%m-%d")
        st = statuses[i % 2]
        out.append({
            "type": "cluster",
            "id": f"clus-{i}",
            "name": name,
            "summary": f"{name} • {plat} • {nodes} nodes • {vuln:,} vulns",
            "details": {"platform": plat, "nodes": nodes, "vuln_count": vuln, "last_scanned": last, "status": st},
        })

    images = [("nginx", "1.21-alpine"), ("node", "18-alpine"), ("python", "3.9-slim"), ("postgres", "13-alpine"),
              ("redis", "6-alpine"), ("alpine", "3.15"), ("ubuntu", "20.04"), ("java/openjdk", "11-jre-slim"),
              ("golang", "1.19-alpine"), ("elasticsearch", "8.5.0"), ("kafka", "3.4"), ("zookeeper", "3.8"),
              ("mongodb", "5.0"), ("mysql", "8.0"), ("rabbitmq", "3.11"), ("memcached", "1.6"),
              ("grafana", "9.4"), ("prometheus", "v2.42"), ("fluentd", "v1.16"), ("vault", "1.12")]
    registries = ["docker.io", "ecr.aws.io", "gcr.io", "acr.azure.io", "ghcr.io", "quay.io"]
    for i in range(n_images):
        img_name, tag = images[i % len(images)]
        reg = registries[i % len(registries)]
        vuln = random.randint(100, 25_000)
        c, h = random.randint(0, min(200, vuln // 10)), random.randint(0, min(2000, vuln // 5))
        out.append({
            "type": "image",
            "id": f"img-{i}",
            "name": f"{img_name}:{tag}",
            "summary": f"{img_name}:{tag} • {reg} • {vuln:,} vulns (C:{c} H:{h})",
            "details": {"registry": reg, "vuln_count": vuln, "critical": c, "high": h, "status": "unpatched"},
        })

    repo_types = ["Maven", "npm", "PyPI", "Docker", "NuGet", "Go", "RPM", "Debian"]
    repo_prefixes = ["platform", "frontend", "backend", "data", "ml", "api", "legacy", "shared"]
    for i in range(n_repos):
        rt = repo_types[i % len(repo_types)]
        pre = repo_prefixes[i % len(repo_prefixes)]
        name = f"{pre}-{rt.lower()}-repo-{i % 50}"
        arts = random.randint(50, 5000)
        vuln = random.randint(1_000, 120_000)
        st = statuses[i % 2]
        out.append({
            "type": "repo",
            "id": f"repo-{i}",
            "name": name,
            "summary": f"{name} • {rt} • {arts:,} artifacts • {vuln:,} vulns",
            "details": {"type": rt, "artifact_count": arts, "vuln_count": vuln, "status": st},
        })

    yaml_sources = ["Kubernetes", "Helm", "Serverless/Lambda", "ArgoCD", "Tekton", "Terraform+K8s", "Flux"]
    for i in range(n_yaml):
        src = yaml_sources[i % len(yaml_sources)]
        name = f"{src.lower().replace('/', '-')}-config-{i % 30}"
        files = random.randint(5, 200)
        vuln = random.randint(200, 35_000)
        st = statuses[i % 2]
        out.append({
            "type": "yaml",
            "id": f"yaml-{i}",
            "name": name,
            "summary": f"{name} • {src} • {files} files • {vuln:,} vulns",
            "details": {"source": src, "file_count": files, "vuln_count": vuln, "status": st},
        })

    random.shuffle(out)
    return out


def get_all_inventory_components(
    target_count: int = 1_500,
) -> list[dict]:
    """~1,500 mixed components: clusters, images, repos, yaml. Each has type, id, name, summary, details."""
    import random
    random.seed(42)
    base = datetime.now()
    out: list[dict] = []

    platforms = ["EKS", "AKS", "GKE", "on-prem", "OpenShift", "Rancher"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1", "prod", "staging", "dev"]
    base_images = [
        "nginx", "node", "python", "postgres", "redis", "alpine", "ubuntu", "java/openjdk",
        "golang", "php", "ruby", "mongo", "mysql", "elasticsearch", "kafka", "zookeeper",
        "api-gateway", "auth-service", "payment-worker", "analytics", "ml-inference",
    ]
    registries = ["docker.io", "ecr.aws.io", "acr.azure.io", "gcr.io", "quay.io", "harbor.internal"]
    repo_types = ["Maven", "npm", "PyPI", "Docker", "NuGet", "Go", "RPM"]
    yaml_sources = ["Kubernetes", "Helm", "Serverless/Lambda", "ArgoCD", "Terraform+K8s", "Tekton"]

    # Clusters ~180
    for i in range(180):
        plat = platforms[i % len(platforms)]
        reg = regions[i % len(regions)]
        name = f"{reg}-{plat.lower()}-{i // 10}"
        nodes = random.randint(4, 64)
        vulns = random.randint(8_000, 120_000)
        status = "unpatched" if i % 3 != 0 else "unmonitored"
        last = (base - timedelta(days=random.randint(7, 400))).strftime("%Y-%m-%d")
        out.append({
            "type": "cluster",
            "id": f"clus-{i}",
            "name": name,
            "summary": f"{name} • {plat} • {nodes} nodes • {vulns:,} vulns",
            "details": {"platform": plat, "nodes": nodes, "vuln_count": vulns, "last_scanned": last, "status": status},
        })

    # Docker images ~800
    for i in range(800):
        img = base_images[i % len(base_images)]
        tag = f"{random.randint(1,22)}.{random.choice(['alpine','slim','bullseye'])}" if "nginx" in img or img == "node" else f"{random.randint(10,20)}-{random.choice(['alpine','slim'])}"
        reg = registries[i % len(registries)]
        vulns = random.randint(200, 35_000)
        c, h = random.randint(1, 400), random.randint(50, 5_000)
        out.append({
            "type": "image",
            "id": f"img-{i}",
            "name": f"{img}:{tag}",
            "summary": f"{img}:{tag} • {reg} • {vulns:,} vulns (C:{c} H:{h})",
            "details": {"registry": reg, "vuln_count": vulns, "critical": c, "high": h, "status": "unpatched"},
        })

    # Repos ~320
    for i in range(320):
        rt = repo_types[i % len(repo_types)]
        name = f"{rt.lower()}-repo-{regions[i % len(regions)]}-{i}"
        arts = random.randint(50, 4_000)
        vulns = random.randint(2_000, 200_000)
        status = "unpatched" if i % 4 != 0 else "unmonitored"
        out.append({
            "type": "repo",
            "id": f"repo-{i}",
            "name": name,
            "summary": f"{name} • {rt} • {arts:,} artifacts • {vulns:,} vulns",
            "details": {"type": rt, "artifact_count": arts, "vuln_count": vulns, "status": status},
        })

    # YAML functions ~200
    for i in range(200):
        src = yaml_sources[i % len(yaml_sources)]
        name = f"{src.lower().replace('+','-')}-config-{i}"
        files = random.randint(5, 250)
        vulns = random.randint(1_000, 50_000)
        status = "unpatched" if i % 3 != 0 else "unmonitored"
        out.append({
            "type": "yaml",
            "id": f"yaml-{i}",
            "name": name,
            "summary": f"{name} • {src} • {files} files • {vulns:,} vulns",
            "details": {"source": src, "file_count": files, "vuln_count": vulns, "status": status},
        })

    random.shuffle(out)
    return out[:target_count]


def get_all_inventory_components() -> list[dict]:
    """~1,500 mixed components: clusters, images, repos, yaml. Each has type, id, name, summary, details."""
    import random
    random.seed(42)
    base = datetime.now()
    out = []

    platforms = ["EKS", "AKS", "GKE", "on-prem", "OpenShift"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-south-1", "ap-northeast-1"]
    envs = ["prod", "staging", "dev", "qa", "sandbox"]

    # ~180 clusters
    for i in range(180):
        plat = platforms[i % len(platforms)]
        reg = regions[i % len(regions)]
        env = envs[i % len(envs)]
        name = f"{env}-{reg}"
        nodes = random.randint(4, 64)
        vulns = random.randint(2_000, 95_000)
        status = "unpatched" if i % 3 else "unmonitored"
        last = (base - timedelta(days=random.randint(7, 365))).strftime("%Y-%m-%d")
        out.append({
            "type": "cluster",
            "id": f"clus-{i}",
            "name": name,
            "summary": f"{plat} • {nodes} nodes • {vulns:,} vulns",
            "details": {"platform": plat, "nodes": nodes, "vuln_count": vulns, "last_scanned": last, "status": status, "region": reg},
        })

    # ~800 docker images
    bases = ["nginx", "node", "python", "alpine", "ubuntu", "postgres", "redis", "java/openjdk", "golang", "ruby", "php", "api-gateway", "auth-service", "worker", "cron"]
    tags = ["1.21-alpine", "18-alpine", "3.9-slim", "3.15", "20.04", "13-alpine", "6-alpine", "11-jre", "1.19", "3.10", "8.1", "v2.1", "sha256:a1b2", "latest", "dev"]
    regs = ["docker.io", "ecr.aws.io", "gcr.io", "acr.azure.io"]
    for i in range(800):
        base_n = bases[i % len(bases)]
        tag = tags[(i // len(bases)) % len(tags)]
        reg = regs[i % len(regs)]
        vulns = random.randint(200, 25_000)
        crit = random.randint(0, min(500, vulns // 10))
        high = random.randint(0, min(2000, vulns // 4))
        out.append({
            "type": "image",
            "id": f"img-{i}",
            "name": f"{base_n}:{tag}",
            "summary": f"{vulns:,} vulns (C:{crit} H:{high})",
            "details": {"registry": reg, "vuln_count": vulns, "critical": crit, "high": high, "status": "unpatched"},
        })

    # ~320 repos
    repo_types = ["Maven", "npm", "PyPI", "Docker", "NuGet", "Go"]
    prefixes = ["platform", "frontend", "api", "data", "ml", "legacy", "shared", "core"]
    for i in range(320):
        rtype = repo_types[i % len(repo_types)]
        pref = prefixes[i % len(prefixes)]
        name = f"{pref}-{rtype.lower()}-{i % 50}"
        arts = random.randint(50, 5_000)
        vulns = random.randint(1_000, 120_000)
        status = "unpatched" if i % 4 else "unmonitored"
        out.append({
            "type": "repo",
            "id": f"repo-{i}",
            "name": name,
            "summary": f"{rtype} • {arts:,} artifacts • {vulns:,} vulns",
            "details": {"type": rtype, "artifact_count": arts, "vuln_count": vulns, "status": status},
        })

    # ~200 yaml functions
    sources = ["Kubernetes", "Helm", "Serverless/Lambda", "ArgoCD", "Terraform+K8s", "Tekton"]
    names = ["prod-manifests", "platform-charts", "api-functions", "deploy-apps", "infra-k8s", "build-pipeline"]
    for i in range(200):
        src = sources[i % len(sources)]
        n = names[i % len(names)]
        name = f"{n}-{i % 30}"
        files = random.randint(5, 300)
        vulns = random.randint(500, 35_000)
        status = "unpatched" if i % 3 else "unmonitored"
        out.append({
            "type": "yaml",
            "id": f"yaml-{i}",
            "name": name,
            "summary": f"{src} • {files} files • {vulns:,} vulns",
            "details": {"source": src, "file_count": files, "vuln_count": vulns, "status": status},
        })

    random.shuffle(out)
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# ~1,500 INVENTORY COMPONENTS (mixed clusters, images, repos, yaml) — single-line, expandable
# ═══════════════════════════════════════════════════════════════════════════════

import random
_INV_RANDOM_SEED = 42


def _gen_inventory_components() -> list[dict]:
    """Generate ~1,500 mixed inventory components. Each has type, id, name, summary, details."""
    random.seed(_INV_RANDOM_SEED)
    base = datetime.now()
    out: list[dict] = []

    platforms = ["EKS", "AKS", "GKE", "on-prem", "OpenShift", "Rancher"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-south-1", "ap-northeast-1"]
    envs = ["prod", "staging", "dev", "qa", "sandbox"]
    statuses = ["unpatched", "unpatched", "unpatched", "unmonitored", "unmonitored"]  # bias unpatched

    for i in range(185):  # clusters
        env = envs[i % len(envs)]
        reg = regions[i % len(regions)]
        plat = platforms[i % len(platforms)]
        nodes = random.choice([4, 8, 12, 16, 24, 32, 48, 64])
        vulns = random.randint(5_000, 95_000)
        days = random.randint(7, 400)
        status = random.choice(statuses)
        name = f"{env}-{reg}".replace("us-", "us").replace("eu-", "eu").replace("ap-", "ap")
        out.append({
            "type": "cluster",
            "id": f"clus-{i:04d}",
            "name": name,
            "summary": f"{plat} • {nodes} nodes • {vulns:,} vulns",
            "status": status,
            "details": {
                "platform": plat,
                "nodes": nodes,
                "vuln_count": vulns,
                "last_scanned": (base - timedelta(days=days)).strftime("%Y-%m-%d"),
                "region": reg,
                "environment": env,
            },
        })

    images_base = [
        ("nginx", "docker.io", ["1.19", "1.21-alpine", "1.23", "1.24-alpine", "1.25"]),
        ("node", "docker.io", ["16-alpine", "18-alpine", "18-bullseye", "20-alpine", "20-slim"]),
        ("python", "docker.io", ["3.8-slim", "3.9-slim", "3.10-slim", "3.11-slim", "3.12"]),
        ("alpine", "docker.io", ["3.14", "3.15", "3.16", "3.17", "3.18", "3.19"]),
        ("ubuntu", "docker.io", ["18.04", "20.04", "22.04"]),
        ("postgres", "docker.io", ["12-alpine", "13-alpine", "14", "15-alpine"]),
        ("redis", "docker.io", ["6-alpine", "6.2", "7-alpine"]),
        ("java/openjdk", "docker.io", ["11-jre-slim", "17-jre-slim", "21-jre"]),
        ("grafana/grafana", "docker.io", ["8.5", "9.2", "10.0"]),
        ("prom/prometheus", "docker.io", ["v2.40", "v2.45", "v2.47"]),
    ]
    registries = ["docker.io", "ecr.aws.io", "acr.azure.io", "gcr.io", "ghcr.io"]
    for i in range(820):  # docker images
        base_img = images_base[i % len(images_base)]
        name, reg, tags = base_img[0], base_img[1], base_img[2]
        tag = tags[i % len(tags)] if tags else "latest"
        registry = registries[i % len(registries)]
        vulns = random.randint(200, 25_000)
        crit = random.randint(0, min(200, vulns // 20))
        high = random.randint(0, min(1500, vulns // 5))
        status = random.choice(statuses)
        full_name = f"{name}:{tag}"
        out.append({
            "type": "image",
            "id": f"img-{i:04d}",
            "name": full_name,
            "summary": f"{vulns:,} vulns (C:{crit} H:{high})",
            "status": status,
            "details": {
                "registry": registry,
                "tag": tag,
                "vuln_count": vulns,
                "critical": crit,
                "high": high,
                "digest": f"sha256:{random.randint(10**14, 10**15):x}"[:64],
            },
        })

    repo_types = ["Maven", "npm", "PyPI", "Docker", "NuGet", "Go"]
    for i in range(320):  # repos
        rtype = repo_types[i % len(repo_types)]
        name = f"{rtype.lower()}-repo-{envs[i % 5]}-{(i // 5) % 20:02d}"
        artifacts = random.randint(50, 3500)
        vulns = random.randint(2_000, 120_000)
        status = random.choice(statuses)
        out.append({
            "type": "repo",
            "id": f"repo-{i:04d}",
            "name": name,
            "summary": f"{rtype} • {artifacts:,} artifacts • {vulns:,} vulns",
            "status": status,
            "details": {
                "type": rtype,
                "artifact_count": artifacts,
                "vuln_count": vulns,
            },
        })

    yaml_sources = ["Kubernetes", "Helm", "Serverless/Lambda", "ArgoCD", "Terraform+K8s", "Tekton", "Flux"]
    for i in range(195):  # yaml
        src = yaml_sources[i % len(yaml_sources)]
        name = f"{src.lower().replace('/', '-')}-{envs[i % 5]}-{(i % 15):02d}"
        files = random.randint(3, 220)
        vulns = random.randint(500, 48_000)
        status = random.choice(statuses)
        out.append({
            "type": "yaml",
            "id": f"yaml-{i:04d}",
            "name": name,
            "summary": f"{src} • {files} files • {vulns:,} vulns",
            "status": status,
            "details": {
                "source": src,
                "file_count": files,
                "vuln_count": vulns,
            },
        })

    random.shuffle(out)
    return out


_INVENTORY_CACHE: list[dict] | None = None


def get_all_inventory_components() -> list[dict]:
    """~1,500 mixed components. Each: type, id, name, summary, status, details (for expand)."""
    global _INVENTORY_CACHE
    if _INVENTORY_CACHE is None:
        _INVENTORY_CACHE = _gen_inventory_components()
    return _INVENTORY_CACHE


def get_all_inventory_components() -> list[dict]:
    """~1,500 mixed components: clusters, images, repos, YAML. Each has single-line summary + details for expand."""
    base = datetime.now()
    out: list[dict] = []

    # Clusters: ~180 (regions × envs × platforms)
    platforms = ["EKS", "AKS", "GKE", "OpenShift", "on-prem", "Rancher"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-south-1", "ap-northeast-1"]
    envs = ["prod", "staging", "dev", "sandbox"]
    for i, (plat, reg, env) in enumerate(
        (p, r, e) for p in platforms for r in regions for e in envs
    )[:180]:
        vulns = 5_000 + (i * 700) % 120_000
        nodes = 4 + (i % 48)
        status = "unpatched" if i % 3 else "unmonitored"
        last = (base - timedelta(days=30 + i % 365)).strftime("%Y-%m-%d")
        name = f"{env}-{reg}"
        out.append({
            "type": "cluster",
            "id": f"clus-{i}",
            "name": name,
            "summary": f"{name} · {plat} · {nodes} nodes · {vulns:,} vulns · {status}",
            "details": {
                "platform": plat,
                "nodes": nodes,
                "vuln_count": vulns,
                "last_scanned": last,
                "status": status,
                "region": reg,
                "environment": env,
            },
        })

    # Docker images: ~800 (base images × tags, app images)
    bases = ["nginx", "node", "python", "alpine", "ubuntu", "postgres", "redis", "java/openjdk",
             "elasticsearch", "kafka", "rabbitmq", "mongo", "mysql", "grafana", "prometheus"]
    tags = ["latest", "alpine", "slim", "bullseye", "1.21", "18", "3.9", "20.04", "13", "6.2"]
    registries = ["docker.io", "ecr.aws.io", "gcr.io", "acr.azure.io", "ghcr.io"]
    for i in range(800):
        b, t, r = bases[i % len(bases)], tags[i % len(tags)], registries[i % len(registries)]
        vulns = 500 + (i * 123) % 35_000
        crit, high = max(1, vulns // 50), max(10, vulns // 5)
        name = f"{b}:{t}" if ":" in t or t in ("latest", "alpine", "slim", "bullseye") else f"{b}:{t}"
        out.append({
            "type": "image",
            "id": f"img-{i}",
            "name": name,
            "summary": f"{name} · {r} · {vulns:,} vulns (C:{crit} H:{high}) · unpatched",
            "details": {
                "registry": r,
                "vuln_count": vulns,
                "critical": crit,
                "high": high,
                "digest": f"sha256:abc{i % 10000:04d}...",
                "size_mb": 50 + (i % 500),
            },
        })

    # Repos: ~320 (Maven, npm, PyPI, Docker, NuGet, Go)
    repo_types = ["Maven", "npm", "PyPI", "Docker", "NuGet", "Go"]
    prefixes = ["core", "frontend", "api", "data", "ml", "legacy", "internal", "shared"]
    for i in range(320):
        rt = repo_types[i % len(repo_types)]
        prefix = prefixes[i % len(prefixes)]
        arts = 50 + (i * 17) % 5_000
        vulns = 2_000 + (i * 300) % 200_000
        status = "unpatched" if i % 4 else "unmonitored"
        name = f"{prefix}-{rt.lower()}-{i % 100}"
        out.append({
            "type": "repo",
            "id": f"repo-{i}",
            "name": name,
            "summary": f"{name} · {rt} · {arts:,} artifacts · {vulns:,} vulns · {status}",
            "details": {
                "type": rt,
                "artifact_count": arts,
                "vuln_count": vulns,
                "status": status,
                "last_indexed": (base - timedelta(days=i % 30)).strftime("%Y-%m-%d"),
            },
        })

    # YAML / configs: ~200 (K8s, Helm, Serverless, ArgoCD, Terraform)
    sources = ["Kubernetes", "Helm", "Serverless/Lambda", "ArgoCD", "Terraform+K8s", "Tekton", "Flux"]
    for i in range(200):
        src = sources[i % len(sources)]
        files = 5 + (i * 3) % 200
        vulns = 100 + (i * 150) % 50_000
        status = "unpatched" if i % 3 else "unmonitored"
        name = f"{src.lower().replace('/', '-')}-config-{i % 50}"
        out.append({
            "type": "yaml",
            "id": f"yaml-{i}",
            "name": name,
            "summary": f"{name} · {src} · {files} files · {vulns:,} vulns · {status}",
            "details": {
                "source": src,
                "file_count": files,
                "vuln_count": vulns,
                "status": status,
                "path": f"/infra/{name}",
            },
        })

    return out


def get_all_inventory_components() -> list[dict]:
    """~1,500 mixed components (clusters, images, repos, yaml) as single-line entries with detail payloads."""
    base = datetime.now()
    components: list[dict] = []
    platforms = ["EKS", "AKS", "GKE", "on-prem", "OpenShift", "Rancher"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1", "ap-northeast-1"]
    envs = ["prod", "staging", "dev", "qa", "sandbox"]

    # Clusters ~180
    for i in range(180):
        platform = platforms[i % len(platforms)]
        region = regions[i % len(regions)]
        env = envs[i % len(envs)]
        name = f"{env}-{region}-{i // 5}"
        vulns = 5_000 + (i * 617) % 120_000
        nodes = 4 + (i % 52)
        last = (base - timedelta(days=7 + (i % 365))).strftime("%Y-%m-%d")
        status = "unpatched" if i % 3 != 0 else "unmonitored"
        components.append({
            "type": "cluster", "id": f"clus-{i}",
            "name": name, "status": status,
            "summary": f"{name} | {platform} | {nodes} nodes | {vulns:,} vulns | {last}",
            "details": {"platform": platform, "nodes": nodes, "vuln_count": vulns, "last_scanned": last, "region": region, "environment": env},
        })

    # Docker images ~800
    bases = ["nginx", "node", "python", "alpine", "ubuntu", "postgres", "redis", "java/openjdk", "golang", "ruby"]
    regs = ["docker.io", "ecr.aws.io", "gcr.io", "acr.azure.io", "ghcr.io", "quay.io"]
    tags = ["alpine", "slim", "latest", "bullseye", "18", "20", "3.9", "1.21", "13", "6.2"]
    for i in range(800):
        base_img = bases[i % len(bases)]
        tag = f"{tags[i % len(tags)]}" if i % 3 == 0 else f"{1 + (i % 25)}.{i % 10}-{tags[i % len(tags)]}"
        reg = regs[i % len(regs)]
        vulns = 500 + (i * 83) % 35_000
        crit = (i % 50) + 1
        high = (i % 200) + 100
        status = "unpatched" if i % 4 != 0 else "unmonitored"
        name = f"{base_img}:{tag}"
        full_ref = f"{reg}/{name}" if reg != "docker.io" else name
        components.append({
            "type": "image", "id": f"img-{i}",
            "name": full_ref, "status": status,
            "summary": f"{full_ref} | {vulns:,} vulns (C:{crit} H:{high})",
            "details": {"registry": reg, "tag": tag, "vuln_count": vulns, "critical": crit, "high": high},
        })

    # Repos ~320
    repo_types = ["Maven", "npm", "PyPI", "Docker", "NuGet", "Go", "RPM", "Debian"]
    prefixes = ["platform", "frontend", "backend", "data", "infra", "ml", "api", "legacy"]
    for i in range(320):
        rt = repo_types[i % len(repo_types)]
        prefix = prefixes[i % len(prefixes)]
        name = f"{prefix}-{rt.lower()}-{i // 8}"
        artifacts = 50 + (i * 17) % 3_000
        vulns = 1_000 + (i * 293) % 200_000
        status = "unpatched" if i % 3 != 0 else "unmonitored"
        components.append({
            "type": "repo", "id": f"repo-{i}",
            "name": name, "status": status,
            "summary": f"{name} | {rt} | {artifacts:,} artifacts | {vulns:,} vulns",
            "details": {"repo_type": rt, "artifact_count": artifacts, "vuln_count": vulns},
        })

    # YAML / configs ~200
    yaml_sources = ["Kubernetes", "Helm", "Serverless", "ArgoCD", "Terraform", "Tekton", "Flux"]
    for i in range(200):
        src = yaml_sources[i % len(yaml_sources)]
        name = f"{src.lower()}-{['prod', 'staging', 'dev'][i % 3]}-config-{i}"
        files = 5 + (i % 120)
        vulns = 200 + (i * 47) % 50_000
        status = "unpatched" if i % 3 != 0 else "unmonitored"
        components.append({
            "type": "yaml", "id": f"yaml-{i}",
            "name": name, "status": status,
            "summary": f"{name} | {src} | {files} files | {vulns:,} vulns",
            "details": {"source": src, "file_count": files, "vuln_count": vulns},
        })

    return components


# ═══════════════════════════════════════════════════════════════════════════════
# ~1,500 INVENTORY COMPONENTS — Mixed variety, single-line, hyperlinkable
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_inventory_components() -> list[dict]:
    """Generate ~1,500 mixed components: clusters, images, repos, yaml. Cached."""
    import random
    random.seed(42)
    base = datetime.now()
    components = []

    # Cluster name parts
    regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "ap-northeast-1", "sa-east-1"]
    envs = ["prod", "staging", "dev", "qa", "uat", "sandbox"]
    platforms = ["EKS", "AKS", "GKE", "on-prem", "OpenShift", "RKE"]

    for i in range(180):
        region = regions[i % len(regions)]
        env = envs[i % len(envs)]
        plat = platforms[i % len(platforms)]
        nodes = random.randint(4, 64)
        vulns = random.randint(5_000, 95_000)
        status = "unpatched" if i % 3 else "unmonitored"
        last = (base - timedelta(days=random.randint(7, 365))).strftime("%Y-%m-%d")
        components.append({
            "type": "cluster",
            "id": f"clus-{i:04d}",
            "name": f"{env}-{region}-{i % 10}",
            "line": f"{plat} • {nodes} nodes • {vulns:,} vulns",
            "status": status,
            "vuln_count": vulns,
            "details": {
                "platform": plat, "nodes": nodes, "last_scanned": last,
                "region": region, "environment": env,
                "top_cves": ["CVE-2024-21626", "CVE-2023-44487", "CVE-2022-41741"][: random.randint(2, 3)],
            },
        })

    # Docker images
    bases = ["nginx", "node", "python", "alpine", "ubuntu", "postgres", "redis", "java/openjdk", "golang", "ruby", "php", "mongo", "mysql", "elasticsearch", "kafka"]
    registries = ["docker.io", "ecr.aws.io", "gcr.io", "acr.azure.io", "quay.io"]
    tags = ["latest", "alpine", "slim", "1.21", "18", "20.04", "3.9", "3.15", "11-jre", "6-alpine", "13-alpine", "v2.1", "sha256:a1b2c3"]

    for i in range(820):
        base_img = bases[i % len(bases)]
        reg = registries[i % len(registries)]
        tag = tags[i % len(tags)]
        vulns = random.randint(200, 25_000)
        c = random.randint(1, min(500, vulns // 10))
        h = random.randint(10, min(2000, vulns))
        status = "unpatched" if i % 4 else "unmonitored"
        components.append({
            "type": "image",
            "id": f"img-{i:04d}",
            "name": f"{base_img}:{tag}",
            "line": f"{vulns:,} vulns (C:{c} H:{h})",
            "status": status,
            "vuln_count": vulns,
            "details": {
                "registry": reg, "critical": c, "high": h,
                "layers": random.randint(3, 15), "size_mb": random.randint(50, 800),
                "base_image": base_img, "tag": tag,
            },
        })

    # Repos
    repo_types = ["Maven", "npm", "PyPI", "Docker", "NuGet", "Go", "RPM"]
    prefixes = ["core", "frontend", "backend", "ml", "data", "api", "platform", "legacy"]

    for i in range(320):
        rtype = repo_types[i % len(repo_types)]
        pre = prefixes[i % len(prefixes)]
        arts = random.randint(50, 3500)
        vulns = random.randint(2_000, 120_000)
        status = "unpatched" if i % 3 else "unmonitored"
        components.append({
            "type": "repo",
            "id": f"repo-{i:04d}",
            "name": f"{pre}-{rtype.lower()}-{i % 20}",
            "line": f"{rtype} • {arts:,} artifacts • {vulns:,} vulns",
            "status": status,
            "vuln_count": vulns,
            "details": {
                "type": rtype, "artifact_count": arts,
                "last_indexed": (base - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d"),
                "url": f"https://artifacts.internal/{pre}-{rtype.lower()}-{i}",
            },
        })

    # YAML / functions
    yaml_sources = ["Kubernetes", "Helm", "Serverless", "ArgoCD", "Terraform+K8s", "Tekton", "Kustomize"]
    yaml_names = ["manifests", "charts", "lambda", "workflows", "pipelines", "deployments", "ingress"]

    for i in range(200):
        src = yaml_sources[i % len(yaml_sources)]
        nm = yaml_names[i % len(yaml_names)]
        files = random.randint(5, 250)
        vulns = random.randint(500, 55_000)
        status = "unpatched" if i % 4 else "unmonitored"
        components.append({
            "type": "yaml",
            "id": f"yaml-{i:04d}",
            "name": f"{nm}-{src.lower().replace('+', '-')}-{i % 15}",
            "line": f"{src} • {files} files • {vulns:,} vulns",
            "status": status,
            "vuln_count": vulns,
            "details": {
                "source": src, "file_count": files,
                "path": f"/gitops/{nm}-{i}", "last_scan": (base - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d"),
            },
        })

    return components


_CACHED_COMPONENTS: list[dict] | None = None


def get_all_inventory_components() -> list[dict]:
    """~1,500 mixed inventory components. Each has type, id, name, line, status, vuln_count, details."""
    global _CACHED_COMPONENTS
    if _CACHED_COMPONENTS is None:
        _CACHED_COMPONENTS = _gen_inventory_components()
    return _CACHED_COMPONENTS


def get_all_inventory_components() -> list[dict]:
    """~1,500 mixed components: clusters, images, repos, yaml. Each has type, id, name, summary, details."""
    import random
    random.seed(42)
    base = datetime.now()
    out = []

    platforms = ["EKS", "AKS", "GKE", "on-prem", "OpenShift"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-south-1", "ap-northeast-1"]
    envs = ["prod", "staging", "dev", "qa", "sandbox"]

    # ~180 clusters
    for i in range(180):
        plat = platforms[i % len(platforms)]
        reg = regions[i % len(regions)]
        env = envs[i % len(envs)]
        name = f"{env}-{reg}"
        nodes = random.randint(4, 64)
        vulns = random.randint(2_000, 80_000)
        status = "unpatched" if i % 3 else "unmonitored"
        last = (base - timedelta(days=random.randint(7, 365))).strftime("%Y-%m-%d")
        out.append({
            "type": "cluster",
            "id": f"clus-{i}",
            "name": name,
            "summary": f"{plat} • {nodes} nodes • {vulns:,} vulns",
            "details": f"Platform: {plat} | Region: {reg} | Nodes: {nodes} | Last scanned: {last} | Status: {status}",
            "vuln_count": vulns,
            "status": status,
        })

    # ~800 Docker images
    bases = ["nginx", "node", "python", "alpine", "ubuntu", "postgres", "redis", "java/openjdk", "golang", "ruby", "php", "kafka", "elasticsearch", "mongo", "mysql"]
    registries = ["docker.io", "ecr.aws.io", "gcr.io", "acr.azure.io", "ghcr.io"]
    tags = ["latest", "alpine", "slim", "bullseye", "3.15", "3.18", "18", "20", "21", "1.21", "13", "11-jre"]
    for i in range(800):
        base_name = bases[i % len(bases)]
        reg = registries[i % len(registries)]
        tag = tags[i % len(tags)] if i % 3 else f"v{(i % 20) + 1}.0"
        vulns = random.randint(200, 25_000)
        crit = random.randint(0, min(500, vulns // 50))
        high = random.randint(10, min(2000, vulns // 5))
        out.append({
            "type": "image",
            "id": f"img-{i}",
            "name": f"{base_name}:{tag}",
            "summary": f"{reg} • {vulns:,} vulns (C:{crit} H:{high})",
            "details": f"Registry: {reg} | Tag: {tag} | Critical: {crit} | High: {high} | Status: unpatched",
            "vuln_count": vulns,
            "status": "unpatched",
        })

    # ~320 repos
    repo_types = ["Maven", "npm", "PyPI", "Docker", "NuGet", "Go", "RPM", "Debian"]
    prefixes = ["platform-", "frontend-", "backend-", "ml-", "data-", "api-", "core-"]
    for i in range(320):
        rtype = repo_types[i % len(repo_types)]
        name = f"{prefixes[i % len(prefixes)]}{'maven' if rtype=='Maven' else 'npm' if rtype=='npm' else 'pypi'}-{i % 50}"
        arts = random.randint(50, 5_000)
        vulns = random.randint(1_000, 120_000)
        status = "unpatched" if i % 4 else "unmonitored"
        out.append({
            "type": "repo",
            "id": f"repo-{i}",
            "name": name,
            "summary": f"{rtype} • {arts:,} artifacts • {vulns:,} vulns",
            "details": f"Type: {rtype} | Artifacts: {arts:,} | Last indexed: {(base - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d')} | Status: {status}",
            "vuln_count": vulns,
            "status": status,
        })

    # ~200 YAML functions
    yaml_sources = ["Kubernetes", "Helm", "Serverless/Lambda", "ArgoCD", "Terraform+K8s", "Tekton", "Flux"]
    yaml_names = ["prod-manifests", "helm-platform", "api-lambda", "argocd-apps", "tf-k8s", "ci-pipeline", "deploy-workflow"]
    for i in range(200):
        src = yaml_sources[i % len(yaml_sources)]
        name = f"{yaml_names[i % len(yaml_names)]}-{i % 30}"
        files = random.randint(5, 200)
        vulns = random.randint(500, 45_000)
        status = "unpatched" if i % 3 else "unmonitored"
        out.append({
            "type": "yaml",
            "id": f"yaml-{i}",
            "name": name,
            "summary": f"{src} • {files} files • {vulns:,} vulns",
            "details": f"Source: {src} | Files: {files} | Base images: {random.randint(3, 25)} | Status: {status}",
            "vuln_count": vulns,
            "status": status,
        })

    random.shuffle(out)
    return out

