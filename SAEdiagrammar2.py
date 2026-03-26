import json
import re
from datetime import datetime

class SAENWdiagrammar:
    def __init__(self, diagram_data):
        self.data = diagram_data
        self.issues = []
        self.nodes = diagram_data.get("nodes", [])
        self.edges = diagram_data.get("connections", [])
        self.metadata = diagram_data.get("metadata", {})

    # ==========================================
    # 🆕 NEW EXPORT FUNCTION
    # ==========================================
    def export_to_json(self, filename="saenw_audit_report.json"):
        """
        Exports the original diagram data AND the audit results to a JSON file.
        This creates a permanent artifact of the security review.
        """
        report_payload = {
            "audit_timestamp": datetime.now().isoformat(),
            "audit_summary": {
                "total_issues": len(self.issues),
                "status": "FAIL" if self.issues else "PASS"
            },
            "audit_findings": self.issues,
            "source_diagram": self.data
        }

        try:
            with open(filename, 'w') as f:
                json.dump(report_payload, f, indent=4)
            print(f"💾 Report successfully exported to: {filename}")
        except IOError as e:
            print(f"❌ Error exporting JSON: {e}")

    # ==========================================
    # LOGGING UTILITY
    # ==========================================
    def log_issue(self, severity, check_name, message):
        icon = "❌ FAIL" if severity == "HIGH" else "⚠️ WARN"
        # We store it as a dict now for cleaner JSON export, formatted string for console
        issue_entry = {
            "severity": severity,
            "check": check_name,
            "message": message,
            "formatted": f"{icon} [{check_name}]: {message}"
        }
        self.issues.append(issue_entry)

    # ==========================================
    # SECURITY CHECKS (The "Linter" Logic)
    # ==========================================
    
    # 1. METADATA & HYGIENE
    def check_metadata(self):
        required_fields = ["version", "last_updated", "author", "classification"]
        for field in required_fields:
            if field not in self.metadata:
                self.log_issue("HIGH", "Hygiene", f"Missing metadata field: '{field}'")
        
        if "last_updated" in self.metadata:
            try:
                last_date = datetime.strptime(self.metadata["last_updated"], "%Y-%m-%d")
                days_old = (datetime.now() - last_date).days
                if days_old > 180:
                    self.log_issue("WARN", "Hygiene", f"Diagram is {days_old} days old. Verify accuracy.")
            except ValueError:
                self.log_issue("WARN", "Hygiene", "Date format invalid (use YYYY-MM-DD)")

    # 2. TRUST BOUNDARIES & 4. INGRESS/EGRESS
    def check_boundaries_and_ingress(self):
        has_internet = any(n.get("zone") == "Internet" for n in self.nodes)
        has_dmz = any(n.get("zone") == "DMZ" for n in self.nodes)
        
        if has_internet and not has_dmz:
            self.log_issue("HIGH", "Trust Boundaries", "Internet zone detected but no DMZ defined.")

    # 3. SUBNET LOGIC
    def check_subnets(self):
        cidr_pattern = re.compile(r'^([0-9]{1,3}\.){3}[0-9]{1,3}(\/([0-9]|[1-2][0-9]|3[0-2]))$')
        for node in self.nodes:
            if "subnet" in node:
                if not cidr_pattern.match(node["subnet"]):
                    self.log_issue("HIGH", "Addressing", f"Invalid CIDR format for node {node['id']}: {node['subnet']}")
            else:
                 if node.get("type") in ["server", "database"]:
                     self.log_issue("WARN", "Addressing", f"Node {node['id']} is missing Subnet/CIDR info.")

    # 5. DIRECTIONALITY & 6. PROTOCOLS
    def check_connections(self):
        insecure_ports = [21, 23, 80] # FTP, Telnet, HTTP
        
        for edge in self.edges:
            if "direction" not in edge or edge["direction"] == "unknown":
                self.log_issue("WARN", "Flow", f"Connection {edge['id']} missing flow direction.")
            
            if "port" not in edge:
                self.log_issue("WARN", "Ports", f"Connection {edge['id']} missing destination port.")
            elif edge["port"] in insecure_ports:
                self.log_issue("HIGH", "Protocols", f"Insecure port {edge['port']} ({edge.get('protocol')}) in use on connection {edge['id']}.")

    # 7. CONTROLS (SSL Termination)
    def check_encryption(self):
        public_web = [n for n in self.nodes if n.get("type") == "web_server" and n.get("public_access") == True]
        for node in public_web:
            incoming = [e for e in self.edges if e["to"] == node["id"]]
            for conn in incoming:
                if conn.get("port") == 80:
                    self.log_issue("HIGH", "Controls", f"Public Web Server {node['id']} accepts HTTP (Port 80). Ensure Redirect or WAF is present.")

    # 9. REDUNDANCY
    def check_redundancy(self):
        critical_devices = [n for n in self.nodes if n.get("type") in ["firewall", "load_balancer"]]
        for device in critical_devices:
            if not device.get("ha_enabled", False):
                self.log_issue("WARN", "Resilience", f"Critical device {device['id']} does not have High Availability (HA) flagged.")

    # 10. CLOUD REALITY
    def check_cloud_security(self):
        databases = [n for n in self.nodes if n.get("type") == "database"]
        for db in databases:
            if db.get("public_ip", False) == True:
                self.log_issue("HIGH", "Cloud Reality", f"Database {db['id']} is marked as having a PUBLIC IP.")

    # ==========================================
    # MAIN EXECUTION
    # ==========================================
    def run_all_checks(self):
        print(f"--- 🛡️  Starting SAENWdiagrammar Review ---")
        self.check_metadata()
        self.check_boundaries_and_ingress()
        self.check_subnets()
        self.check_connections()
        self.check_encryption()
        self.check_redundancy()
        self.check_cloud_security()
        
        print("\n--- 📋 Audit Report ---")
        if not self.issues:
            print("✅ No issues found. Diagram passes QC.")
        else:
            for issue in self.issues:
                print(issue['formatted'])
        
        # Trigger the export
        print("-----------------------")
        self.export_to_json() 

# ==========================================
# MOCK DATA (Simulating an exported diagram)
# ==========================================
mock_diagram_json = {
    "metadata": {
        "version": "1.0",
        "author": "DevOps Team",
        # Missing classification/date to trigger hygiene errors
    },
    "nodes": [
        {"id": "fw-01", "type": "firewall", "zone": "DMZ", "ha_enabled": False}, 
        {"id": "web-01", "type": "web_server", "zone": "DMZ", "subnet": "10.0.1.x", "public_access": True}, 
        {"id": "db-01", "type": "database", "zone": "Private", "subnet": "10.0.2.0/24", "public_ip": True} 
    ],
    "connections": [
        {"id": "conn-1", "from": "internet", "to": "web-01", "port": 80, "protocol": "HTTP", "direction": "inbound"}, 
        {"id": "conn-2", "from": "web-01", "to": "db-01", "protocol": "SQL"} 
    ]
}

if __name__ == "__main__":
    tool = SAENWdiagrammar(mock_diagram_json)
    tool.run_all_checks()