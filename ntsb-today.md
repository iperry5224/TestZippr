# NTSB Today — Customer assessment questions (AC & IA)

Interview prompts for system owners, ISSOs, and operations during NIST 800-53–style assessments.

**Control families:** Access Control (AC), Identification and Authentication (IA)

---

## Access Control (AC)

1. **Scope:** What users, roles, and privilege levels exist for this system (end users, admins, DBAs, vendors, break-glass)?

2. **Least privilege:** How do you ensure accounts and service principals only have the minimum permissions needed day-to-day?

3. **Separation of duties:** Which sensitive functions are split across different people or roles (e.g., deploy vs approve vs audit)?

4. **Remote access:** How is access from outside the trusted network provided (VPN, ZTNA, bastion), and who may use it?

5. **Session / connection controls:** What timeouts, lockouts, or idle disconnects apply to administrative sessions?

6. **Privileged access:** How are elevated accounts requested, approved, time-bound, and logged?

7. **Emergency access:** Is there a break-glass or emergency admin process? When was it last tested?

8. **Shared accounts:** Are any shared or generic accounts still in use? If so, how are they justified and controlled?

9. **Non-person entities:** How are application/service accounts provisioned, rotated, and reviewed?

10. **Cross-boundary flows:** Which interfaces expose the system to other networks, cloud tenants, or partners—and how is access enforced there?

11. **Default deny:** At layers you control (app, API, network, cloud IAM), is default posture deny-by-default with explicit allows?

12. **Changes to access:** How are adds/moves/changes to permissions requested, approved, and verified after the fact?

13. **Reviews:** How often are user accounts and access rights reviewed, and what triggers an out-of-cycle review?

14. **Third parties:** How is vendor or contractor access scoped, monitored, and terminated when work ends?

---

## Identification and Authentication (IA)

15. **Identity stores:** Where are identities mastered (IdP, AD, cloud IAM), and how does this system integrate with them?

16. **MFA:** Is MFA required for all human users, especially for privileged and remote access? Any known exceptions?

17. **Federation / SSO:** Is single sign-on used for this application, and are any local-only accounts still allowed?

18. **Password / authenticator policy:** What complexity, history, lockout, and reset rules apply—and how are they enforced technically?

19. **Privileged authentication:** Is MFA, hardware token, or step-up auth required for admin or break-glass use?

20. **Default credentials:** How do you ensure default, vendor, or bootstrap credentials are changed or disabled before production?

21. **Certificates / keys:** How are TLS certs, API keys, and signing keys issued, stored, rotated, and revoked?

22. **Device or context:** Do you use any device posture, conditional access, or IP allowlisting before granting access?

23. **Account lifecycle:** How are joins, moves, leaves (including contractors) reflected in access to this system within your defined SLA (e.g., 24 hours)?

24. **Authentication logging:** What is logged for sign-on and MFA events, and who monitors those logs for anomalies?

25. **Legacy / weak auth:** Are any legacy protocols or weak auth methods still in use for this system (e.g., basic auth over HTTP, unauthenticated internal APIs)? What is the remediation plan?

---

*Optional follow-up: map each question to specific NIST SP 800-53 Rev 5 control IDs (e.g., AC-2, AC-3, IA-2, IA-5) in the formal SAR/assessment package.*
