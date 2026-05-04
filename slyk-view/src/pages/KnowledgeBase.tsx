import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  BookOpen,
  ExternalLink,
  Shield,
  FileText,
  Server,
  Lock,
  AlertTriangle,
  CheckCircle,
  Search,
  Star,
  Bookmark,
  FolderOpen,
  ClipboardList,
  Zap,
  Database,
  Brain,
  Code,
  Layers,
  Users,
  Network,
  Terminal,
  HelpCircle,
  ChevronDown,
  ChevronRight
} from 'lucide-react'

interface Resource {
  id: string
  title: string
  description: string
  url: string
  category: string
  tags: string[]
  starred?: boolean
}

interface Phase {
  id: number
  title: string
  objective: string
  slykMapping: {
    feature: string
    description: string
    status: 'complete' | 'in-progress' | 'planned'
    evidence: string[]
  }
}

const phases: Phase[] = [
  {
    id: 1,
    title: 'Enable AWS Security Hub in the CSTA environment',
    objective: 'Establish foundational security monitoring and findings aggregation',
    slykMapping: {
      feature: 'Security Hub Integration',
      description: 'SLyK integrates directly with AWS Security Hub to pull real-time security findings, compliance status, and control assessments.',
      status: 'complete',
      evidence: [
        'Security Hub tab displays live findings from the CSTA account',
        'Dashboard shows compliance scores pulled from Security Hub standards',
        'Findings are mapped to NIST 800-53 controls automatically',
        'Real-time alerts feed from Security Hub critical/high findings'
      ]
    }
  },
  {
    id: 2,
    title: 'Establish an internal EC2/S3 hardening runbooks into an Amazon S3 bucket',
    objective: 'Create remediation playbooks for common security misconfigurations',
    slykMapping: {
      feature: 'Remediation Scripts & Runbooks',
      description: 'SLyK provides pre-built remediation scripts for EC2 and S3 security issues, stored and versioned for ISSO use.',
      status: 'complete',
      evidence: [
        'Remediation tab contains AWS CLI scripts for S3 bucket hardening',
        'EC2 security group remediation scripts available',
        'Scripts include: public access blocking, encryption enablement, logging configuration',
        'One-click copy functionality for immediate execution'
      ]
    }
  },
  {
    id: 3,
    title: 'Integrate the Knowledge Base for semantic context retrieval',
    objective: 'Enable AI-powered search and retrieval of security documentation',
    slykMapping: {
      feature: 'Knowledge Base & AI Assistant',
      description: 'SLyK leverages Amazon Bedrock Knowledge Bases to provide semantic search across NIST controls, AWS documentation, and organizational policies.',
      status: 'complete',
      evidence: [
        'Knowledge Base tab provides curated security resources',
        'Ask SLyK chat interface uses Bedrock for contextual responses',
        'NIST 800-53 control descriptions retrieved semantically',
        'AI responses include citations to source documentation'
      ]
    }
  },
  {
    id: 4,
    title: 'Generate OpenAPI schemas mapping the Action Group interfaces',
    objective: 'Define structured API interfaces for agent actions',
    slykMapping: {
      feature: 'Bedrock Agent Action Groups',
      description: 'SLyK\'s Bedrock Agent uses OpenAPI-defined action groups to execute security assessments, retrieve findings, and generate reports.',
      status: 'complete',
      evidence: [
        'Action groups defined for: assess_controls, get_findings, generate_report',
        'OpenAPI schemas specify input/output for each action',
        'Lambda functions implement action group logic',
        'Agent can chain multiple actions for complex queries'
      ]
    }
  },
  {
    id: 5,
    title: 'Develop the serverless architecture to support assessment functions',
    objective: 'Build scalable, cost-effective infrastructure for security automation',
    slykMapping: {
      feature: 'Serverless Assessment Architecture',
      description: 'SLyK runs entirely on serverless AWS services: Lambda for compute, API Gateway for endpoints, S3 for storage, and Bedrock for AI.',
      status: 'complete',
      evidence: [
        'Lambda functions handle all assessment logic (no EC2 required)',
        'API Gateway provides REST endpoints for dashboard',
        'S3 hosts the static React dashboard (CloudFront distributed)',
        'DynamoDB stores assessment history and configurations',
        'Zero infrastructure management required'
      ]
    }
  },
  {
    id: 6,
    title: 'Provide technical demonstration to ISSOs to validate performance functions and results',
    objective: 'Demonstrate working solution to stakeholders',
    slykMapping: {
      feature: 'CSTA Dashboard & Live Demo',
      description: 'The SLyK-View dashboard (CSTA) provides a live, interactive demonstration of all capabilities for ISSO validation.',
      status: 'complete',
      evidence: [
        'Live dashboard accessible at CloudFront URL',
        'Real-time data from account 656443597515',
        'Interactive controls assessment with pass/fail status',
        'AI chat demonstrates natural language security queries',
        'Export capabilities for compliance reporting'
      ]
    }
  }
]

const resources: Resource[] = [
  // NIST Resources
  {
    id: '1',
    title: 'NIST SP 800-53 Rev 5',
    description: 'Security and Privacy Controls for Information Systems and Organizations - the complete control catalog',
    url: 'https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final',
    category: 'NIST Publications',
    tags: ['NIST', '800-53', 'Controls', 'Official'],
    starred: true
  },
  {
    id: '2',
    title: 'NIST SP 800-53A Rev 5',
    description: 'Assessing Security and Privacy Controls - guidance for assessment procedures',
    url: 'https://csrc.nist.gov/publications/detail/sp/800-53a/rev-5/final',
    category: 'NIST Publications',
    tags: ['NIST', 'Assessment', 'Official']
  },
  {
    id: '3',
    title: 'NIST SP 800-37 Rev 2',
    description: 'Risk Management Framework for Information Systems and Organizations',
    url: 'https://csrc.nist.gov/publications/detail/sp/800-37/rev-2/final',
    category: 'NIST Publications',
    tags: ['NIST', 'RMF', 'Risk Management']
  },
  {
    id: '4',
    title: 'NIST Cybersecurity Framework',
    description: 'Framework for Improving Critical Infrastructure Cybersecurity',
    url: 'https://www.nist.gov/cyberframework',
    category: 'NIST Publications',
    tags: ['NIST', 'CSF', 'Framework']
  },
  
  // AWS Security
  {
    id: '5',
    title: 'AWS Security Hub User Guide',
    description: 'Complete documentation for AWS Security Hub service',
    url: 'https://docs.aws.amazon.com/securityhub/latest/userguide/what-is-securityhub.html',
    category: 'AWS Documentation',
    tags: ['AWS', 'Security Hub', 'Documentation'],
    starred: true
  },
  {
    id: '6',
    title: 'AWS Well-Architected Security Pillar',
    description: 'Best practices for securing workloads in AWS',
    url: 'https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html',
    category: 'AWS Documentation',
    tags: ['AWS', 'Well-Architected', 'Best Practices']
  },
  {
    id: '7',
    title: 'AWS Foundational Security Best Practices',
    description: 'Security controls that detect when AWS accounts and resources deviate from best practices',
    url: 'https://docs.aws.amazon.com/securityhub/latest/userguide/fsbp-standard.html',
    category: 'AWS Documentation',
    tags: ['AWS', 'FSBP', 'Best Practices']
  },
  {
    id: '8',
    title: 'AWS Config Rules',
    description: 'Managed and custom rules for evaluating AWS resource configurations',
    url: 'https://docs.aws.amazon.com/config/latest/developerguide/managed-rules-by-aws-config.html',
    category: 'AWS Documentation',
    tags: ['AWS', 'Config', 'Compliance']
  },
  {
    id: '9',
    title: 'Amazon Bedrock Documentation',
    description: 'Build and scale generative AI applications with foundation models',
    url: 'https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html',
    category: 'AWS Documentation',
    tags: ['AWS', 'Bedrock', 'AI']
  },
  
  // CISA Resources
  {
    id: '10',
    title: 'CISA Known Exploited Vulnerabilities',
    description: 'Catalog of vulnerabilities known to be actively exploited',
    url: 'https://www.cisa.gov/known-exploited-vulnerabilities-catalog',
    category: 'CISA Resources',
    tags: ['CISA', 'KEV', 'Vulnerabilities'],
    starred: true
  },
  {
    id: '11',
    title: 'CISA Cybersecurity Alerts',
    description: 'Current cybersecurity alerts and advisories',
    url: 'https://www.cisa.gov/news-events/cybersecurity-advisories',
    category: 'CISA Resources',
    tags: ['CISA', 'Alerts', 'Advisories']
  },
  {
    id: '12',
    title: 'CISA Zero Trust Maturity Model',
    description: 'Guidance for agencies transitioning to zero trust architecture',
    url: 'https://www.cisa.gov/zero-trust-maturity-model',
    category: 'CISA Resources',
    tags: ['CISA', 'Zero Trust', 'Architecture']
  },
  
  // FedRAMP
  {
    id: '13',
    title: 'FedRAMP Marketplace',
    description: 'Search for FedRAMP authorized cloud services',
    url: 'https://marketplace.fedramp.gov/',
    category: 'FedRAMP',
    tags: ['FedRAMP', 'Cloud', 'Authorization']
  },
  {
    id: '14',
    title: 'FedRAMP Documents & Templates',
    description: 'Official FedRAMP templates and documentation',
    url: 'https://www.fedramp.gov/documents-templates/',
    category: 'FedRAMP',
    tags: ['FedRAMP', 'Templates', 'Documentation']
  },
  
  // NOAA Specific
  {
    id: '15',
    title: 'NOAA Cybersecurity Program',
    description: 'NOAA Office of the CIO cybersecurity resources',
    url: 'https://www.noaa.gov/organization/information-technology/cybersecurity',
    category: 'NOAA Resources',
    tags: ['NOAA', 'Policy', 'Internal']
  },
  {
    id: '16',
    title: 'NESDIS Innovation Hub',
    description: 'NESDIS cloud and innovation resources',
    url: 'https://www.nesdis.noaa.gov/',
    category: 'NOAA Resources',
    tags: ['NOAA', 'NESDIS', 'Innovation']
  },
  
  // Tools & Utilities
  {
    id: '17',
    title: 'AWS CLI Command Reference',
    description: 'Complete reference for AWS CLI commands',
    url: 'https://awscli.amazonaws.com/v2/documentation/api/latest/reference/index.html',
    category: 'Tools & Utilities',
    tags: ['AWS', 'CLI', 'Reference']
  },
  {
    id: '18',
    title: 'Prowler - AWS Security Tool',
    description: 'Open source security tool for AWS security assessments',
    url: 'https://github.com/prowler-cloud/prowler',
    category: 'Tools & Utilities',
    tags: ['Open Source', 'Security', 'Assessment']
  },
  {
    id: '19',
    title: 'ScoutSuite - Multi-Cloud Security',
    description: 'Multi-cloud security auditing tool',
    url: 'https://github.com/nccgroup/ScoutSuite',
    category: 'Tools & Utilities',
    tags: ['Open Source', 'Multi-Cloud', 'Audit']
  },
  
  // Training
  {
    id: '20',
    title: 'AWS Security Learning Path',
    description: 'Free AWS security training and certifications',
    url: 'https://aws.amazon.com/training/learn-about/security/',
    category: 'Training',
    tags: ['AWS', 'Training', 'Certification']
  },
  {
    id: '21',
    title: 'SANS Reading Room - Cloud Security',
    description: 'Research papers on cloud security topics',
    url: 'https://www.sans.org/white-papers/?focus-area=cloud-security',
    category: 'Training',
    tags: ['SANS', 'Research', 'Cloud']
  }
]

const categories = [
  { name: 'All', icon: FolderOpen },
  { name: 'NIST Publications', icon: FileText },
  { name: 'AWS Documentation', icon: Server },
  { name: 'CISA Resources', icon: AlertTriangle },
  { name: 'FedRAMP', icon: Shield },
  { name: 'NOAA Resources', icon: BookOpen },
  { name: 'Tools & Utilities', icon: Lock },
  { name: 'Training', icon: CheckCircle }
]

const phaseIcons = [Zap, Database, Brain, Code, Layers, Users]

function RequirementsTab() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-slyk-primary/20 to-slyk-secondary/20 rounded-2xl border border-slyk-primary/30 p-6">
        <h2 className="text-2xl font-bold text-dark-text mb-2">
          SAE Team: Agentic AI-Based Solution
        </h2>
        <p className="text-dark-muted">
          Implementation Phases & SLyK Capability Mapping
        </p>
        <p className="text-sm text-dark-muted mt-2">
          April 22, 2026 • Core Technical Objectives and Milestones
        </p>
      </div>

      {/* Progress Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="glass-card p-4 text-center">
          <p className="text-3xl font-bold text-slyk-success">6</p>
          <p className="text-sm text-dark-muted">Phases Complete</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-3xl font-bold text-slyk-primary">100%</p>
          <p className="text-sm text-dark-muted">Requirements Met</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-3xl font-bold text-slyk-warning">Live</p>
          <p className="text-sm text-dark-muted">Demo Ready</p>
        </div>
      </div>

      {/* Phases */}
      <div className="space-y-4">
        {phases.map((phase, index) => {
          const PhaseIcon = phaseIcons[index]
          return (
            <motion.div
              key={phase.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="glass-card overflow-hidden"
            >
              {/* Phase Header */}
              <div className="bg-dark-border/30 px-6 py-4 flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-slyk-primary/20 flex items-center justify-center flex-shrink-0">
                  <PhaseIcon className="w-6 h-6 text-slyk-primary" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="text-slyk-primary font-bold">Phase {phase.id}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      phase.slykMapping.status === 'complete' 
                        ? 'bg-slyk-success/20 text-slyk-success'
                        : phase.slykMapping.status === 'in-progress'
                        ? 'bg-slyk-warning/20 text-slyk-warning'
                        : 'bg-dark-border text-dark-muted'
                    }`}>
                      {phase.slykMapping.status === 'complete' ? '✓ Complete' : 
                       phase.slykMapping.status === 'in-progress' ? '◐ In Progress' : '○ Planned'}
                    </span>
                  </div>
                  <h3 className="text-dark-text font-medium mt-1">{phase.title}</h3>
                </div>
              </div>

              {/* Phase Content */}
              <div className="p-6 grid md:grid-cols-2 gap-6">
                {/* Objective */}
                <div>
                  <h4 className="text-sm font-medium text-dark-muted mb-2">Objective</h4>
                  <p className="text-dark-text">{phase.objective}</p>
                </div>

                {/* SLyK Mapping */}
                <div>
                  <h4 className="text-sm font-medium text-slyk-primary mb-2">
                    SLyK Implementation: {phase.slykMapping.feature}
                  </h4>
                  <p className="text-dark-text text-sm mb-3">{phase.slykMapping.description}</p>
                  
                  <h5 className="text-xs font-medium text-dark-muted mb-2">Evidence of Completion:</h5>
                  <ul className="space-y-1">
                    {phase.slykMapping.evidence.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-dark-muted">
                        <CheckCircle className="w-4 h-4 text-slyk-success flex-shrink-0 mt-0.5" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Footer Note */}
      <div className="bg-dark-card/50 rounded-xl border border-dark-border/50 p-4">
        <p className="text-sm text-dark-muted italic">
          <strong>Note:</strong> Costs associated with each phase will be determined at a later date. 
          Current implementation uses AWS Free Tier and minimal resource allocation for demonstration purposes.
        </p>
      </div>
    </div>
  )
}

function ArchitectureTab() {
  const [expandedSop, setExpandedSop] = useState<string | null>(null)

  const architectureComponents = [
    {
      name: 'Frontend (React Dashboard)',
      icon: Server,
      color: '#6366F1',
      details: [
        'React + TypeScript + Vite',
        'Hosted on S3: slyk-view-656443597515-us-east-1',
        'Distributed via CloudFront (E3STZQQDVPKXS9)',
        'URL: dymaxfdlmvkiy.cloudfront.net'
      ]
    },
    {
      name: 'API Gateway',
      icon: Network,
      color: '#10B981',
      details: [
        'REST API: zc06lwmk4j.execute-api.us-east-1',
        'Endpoints: /securityhub, /inventory, /assess',
        'CORS enabled for dashboard access',
        'Deployed to prod stage'
      ]
    },
    {
      name: 'Lambda Functions',
      icon: Code,
      color: '#F59E0B',
      details: [
        'slyk-securityhub-findings: Security Hub integration',
        'slyk-inventory: AWS resource inventory',
        'slyk-assess: Control assessment logic',
        'Runtime: Python 3.11, 256MB memory'
      ]
    },
    {
      name: 'Amazon Bedrock',
      icon: Brain,
      color: '#8B5CF6',
      details: [
        'Agent: New_SLyK-53-Security-Assistant',
        'Model: Claude (Anthropic)',
        'Knowledge Base: NIST 800-53 documentation',
        'Action Groups: assess, findings, reports'
      ]
    },
    {
      name: 'Security Hub',
      icon: Shield,
      color: '#EF4444',
      details: [
        'Aggregates findings from AWS services',
        'NIST 800-53 control mapping',
        'Real-time compliance scoring',
        'Integration with Config rules'
      ]
    },
    {
      name: 'Data Sources',
      icon: Database,
      color: '#06B6D4',
      details: [
        'S3: 17 buckets monitored',
        'EC2: Instance compliance tracking',
        'IAM: User/role security analysis',
        'RDS: Database encryption status'
      ]
    }
  ]

  const sops = [
    {
      id: 'sop-001',
      title: 'SOP-001: Daily Security Review',
      frequency: 'Daily (business days)',
      steps: [
        'Access CSTA dashboard and review compliance score',
        'Check alerts feed for CRITICAL/HIGH findings',
        'Review Security Hub tab, filter by severity',
        'For CRITICAL: initiate remediation within 24 hours',
        'For HIGH: create POA&M entry within 72 hours',
        'Document actions in ticketing system'
      ]
    },
    {
      id: 'sop-002',
      title: 'SOP-002: Weekly Compliance Assessment',
      frequency: 'Weekly (Mondays)',
      steps: [
        'Run full assessment via Dashboard refresh',
        'Document compliance score and compare to previous week',
        'Review all control families in Controls tab',
        'Verify resource counts in Inventory tab',
        'Generate weekly compliance report',
        'Update SSP and POA&M as needed'
      ]
    },
    {
      id: 'sop-003',
      title: 'SOP-003: Remediation Execution',
      frequency: 'As needed',
      steps: [
        'Identify finding: note control ID and affected resource',
        'Navigate to Remediation tab, find relevant control',
        'Copy remediation script',
        'Test in non-production environment if possible',
        'Execute script against affected resource',
        'Verify fix in Security Hub (up to 24 hours)',
        'Update POA&M with closure date'
      ]
    },
    {
      id: 'sop-004',
      title: 'SOP-004: AI Assistant Usage',
      frequency: 'As needed',
      steps: [
        'Click "Ask SLyK" in sidebar',
        'Formulate specific query with context',
        'Example: "What are the requirements for AC-2?"',
        'Example: "How do I remediate public S3 access?"',
        'Review AI response and verify against official docs',
        'Use guidance to inform decisions'
      ]
    },
    {
      id: 'sop-005',
      title: 'SOP-005: Incident Response Integration',
      frequency: 'During incidents',
      steps: [
        'Check CSTA dashboard for related findings',
        'Review affected resource in Inventory',
        'Use Ask SLyK for relevant control guidance',
        'Document pre-incident compliance state',
        'Export findings for incident report',
        'Post-incident: update controls based on lessons learned'
      ]
    }
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-slyk-primary/20 to-slyk-secondary/20 rounded-2xl border border-slyk-primary/30 p-6">
        <h2 className="text-2xl font-bold text-dark-text mb-2">
          CSTA Architecture & Standard Operating Procedures
        </h2>
        <p className="text-dark-muted">
          Technical architecture overview and operational procedures for ISSOs
        </p>
        <div className="flex gap-4 mt-4">
          <div className="text-sm">
            <span className="text-dark-muted">Account:</span>{' '}
            <span className="text-slyk-primary font-mono">656443597515</span>
          </div>
          <div className="text-sm">
            <span className="text-dark-muted">Environment:</span>{' '}
            <span className="text-slyk-success">nesdis-ncis-ospocsta-5006</span>
          </div>
        </div>
      </div>

      {/* Architecture Diagram */}
      <div>
        <h3 className="text-xl font-semibold text-dark-text mb-4 flex items-center gap-2">
          <Network className="w-5 h-5 text-slyk-primary" />
          System Architecture
        </h3>
        
        {/* Visual Architecture */}
        <div className="glass-card p-6 mb-4">
          <pre className="text-xs text-dark-muted font-mono overflow-x-auto">
{`┌─────────────────────────────────────────────────────────────────────────────┐
│                              CSTA Architecture                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐   │
│  │   Browser   │────▶│ CloudFront  │────▶│  S3 (Static Dashboard)      │   │
│  │   (ISSO)    │     │   (CDN)     │     │  slyk-view-656443597515-*   │   │
│  └─────────────┘     └─────────────┘     └─────────────────────────────┘   │
│         │                                                                   │
│         │ API Calls                                                         │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        API Gateway (REST)                            │   │
│  │                    zc06lwmk4j.execute-api.us-east-1                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                    │                    │                         │
│         ▼                    ▼                    ▼                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│  │   Lambda    │     │   Lambda    │     │   Lambda    │                   │
│  │ securityhub │     │  inventory  │     │   assess    │                   │
│  └─────────────┘     └─────────────┘     └─────────────┘                   │
│         │                    │                    │                         │
│         ▼                    ▼                    ▼                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│  │  Security   │     │  S3, EC2,   │     │   Config    │                   │
│  │    Hub      │     │  IAM, RDS   │     │   Rules     │                   │
│  └─────────────┘     └─────────────┘     └─────────────┘                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Amazon Bedrock                                │   │
│  │  ┌─────────────────┐     ┌─────────────────────────────────────┐    │   │
│  │  │  Bedrock Agent  │────▶│  Knowledge Base (NIST 800-53 Docs)  │    │   │
│  │  │  SLyK-53        │     │  Security Documentation             │    │   │
│  │  └─────────────────┘     └─────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘`}
          </pre>
        </div>

        {/* Component Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {architectureComponents.map((component, index) => {
            const Icon = component.icon
            return (
              <motion.div
                key={component.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="glass-card p-4"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div 
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${component.color}20` }}
                  >
                    <Icon className="w-5 h-5" style={{ color: component.color }} />
                  </div>
                  <h4 className="font-semibold text-dark-text">{component.name}</h4>
                </div>
                <ul className="space-y-1">
                  {component.details.map((detail, i) => (
                    <li key={i} className="text-sm text-dark-muted flex items-start gap-2">
                      <span className="text-slyk-primary mt-1">•</span>
                      <span className="font-mono text-xs">{detail}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* SOPs */}
      <div>
        <h3 className="text-xl font-semibold text-dark-text mb-4 flex items-center gap-2">
          <Terminal className="w-5 h-5 text-slyk-primary" />
          Standard Operating Procedures
        </h3>
        
        <div className="space-y-3">
          {sops.map((sop) => (
            <div key={sop.id} className="glass-card overflow-hidden">
              <button
                onClick={() => setExpandedSop(expandedSop === sop.id ? null : sop.id)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-dark-border/20 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-slyk-primary/20 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-slyk-primary" />
                  </div>
                  <div className="text-left">
                    <h4 className="font-semibold text-dark-text">{sop.title}</h4>
                    <p className="text-sm text-dark-muted">Frequency: {sop.frequency}</p>
                  </div>
                </div>
                {expandedSop === sop.id ? (
                  <ChevronDown className="w-5 h-5 text-dark-muted" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-dark-muted" />
                )}
              </button>
              
              {expandedSop === sop.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  className="px-6 pb-4 border-t border-dark-border/30"
                >
                  <ol className="mt-4 space-y-2">
                    {sop.steps.map((step, i) => (
                      <li key={i} className="flex items-start gap-3 text-sm">
                        <span className="w-6 h-6 rounded-full bg-slyk-primary/20 text-slyk-primary flex items-center justify-center flex-shrink-0 text-xs font-bold">
                          {i + 1}
                        </span>
                        <span className="text-dark-text pt-0.5">{step}</span>
                      </li>
                    ))}
                  </ol>
                </motion.div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Quick Reference */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-dark-text mb-4 flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-slyk-primary" />
          Quick Reference
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium text-dark-muted mb-2">Key URLs</h4>
            <ul className="space-y-1 text-sm">
              <li className="flex justify-between">
                <span className="text-dark-muted">Dashboard:</span>
                <span className="font-mono text-slyk-primary">dymaxfdlmvkiy.cloudfront.net</span>
              </li>
              <li className="flex justify-between">
                <span className="text-dark-muted">API:</span>
                <span className="font-mono text-slyk-primary">zc06lwmk4j.execute-api...</span>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-medium text-dark-muted mb-2">Response Times</h4>
            <ul className="space-y-1 text-sm">
              <li className="flex justify-between">
                <span className="text-dark-muted">CRITICAL findings:</span>
                <span className="text-slyk-danger">24 hours</span>
              </li>
              <li className="flex justify-between">
                <span className="text-dark-muted">HIGH findings:</span>
                <span className="text-slyk-warning">72 hours</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

function ResourcesTab() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [showStarredOnly, setShowStarredOnly] = useState(false)

  const filteredResources = resources.filter(resource => {
    const matchesSearch = 
      resource.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      resource.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      resource.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
    
    const matchesCategory = selectedCategory === 'All' || resource.category === selectedCategory
    const matchesStarred = !showStarredOnly || resource.starred
    
    return matchesSearch && matchesCategory && matchesStarred
  })

  const getCategoryIcon = (category: string) => {
    const cat = categories.find(c => c.name === category)
    return cat?.icon || FolderOpen
  }

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dark-muted" />
          <input
            type="text"
            placeholder="Search resources, tags, or descriptions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-dark-card/50 border border-dark-border/50 rounded-xl text-dark-text placeholder-dark-muted focus:outline-none focus:border-slyk-primary"
          />
        </div>
        <button
          onClick={() => setShowStarredOnly(!showStarredOnly)}
          className={`flex items-center gap-2 px-4 py-3 rounded-xl transition-colors ${
            showStarredOnly 
              ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/50' 
              : 'bg-dark-card/50 text-dark-muted border border-dark-border/50 hover:border-dark-border'
          }`}
        >
          <Star className={`w-5 h-5 ${showStarredOnly ? 'fill-yellow-400' : ''}`} />
          Starred
        </button>
      </div>

      {/* Category Tabs */}
      <div className="flex flex-wrap gap-2">
        {categories.map((category) => {
          const Icon = category.icon
          return (
            <button
              key={category.name}
              onClick={() => setSelectedCategory(category.name)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-colors ${
                selectedCategory === category.name
                  ? 'bg-slyk-primary/20 text-slyk-primary border border-slyk-primary/50'
                  : 'bg-dark-card/50 text-dark-muted border border-dark-border/50 hover:border-dark-border'
              }`}
            >
              <Icon className="w-4 h-4" />
              {category.name}
            </button>
          )
        })}
      </div>

      {/* Results Count */}
      <p className="text-dark-muted text-sm">
        Showing {filteredResources.length} of {resources.length} resources
      </p>

      {/* Resources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredResources.map((resource, index) => {
          const CategoryIcon = getCategoryIcon(resource.category)
          return (
            <motion.a
              key={resource.id}
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.03 }}
              className="group bg-dark-card/50 backdrop-blur-sm rounded-2xl border border-dark-border/50 p-5 hover:border-slyk-primary/50 transition-all hover:shadow-glow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-slyk-primary/20 flex items-center justify-center">
                  <CategoryIcon className="w-5 h-5 text-slyk-primary" />
                </div>
                <div className="flex items-center gap-2">
                  {resource.starred && (
                    <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                  )}
                  <ExternalLink className="w-4 h-4 text-dark-muted group-hover:text-slyk-primary transition-colors" />
                </div>
              </div>
              
              <h3 className="font-semibold text-dark-text group-hover:text-slyk-primary transition-colors mb-2">
                {resource.title}
              </h3>
              
              <p className="text-sm text-dark-muted mb-3 line-clamp-2">
                {resource.description}
              </p>
              
              <div className="flex flex-wrap gap-1">
                {resource.tags.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 bg-dark-border/50 rounded text-xs text-dark-muted"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </motion.a>
          )
        })}
      </div>

      {/* Empty State */}
      {filteredResources.length === 0 && (
        <div className="text-center py-12">
          <Bookmark className="w-16 h-16 text-dark-muted mx-auto mb-4 opacity-50" />
          <h3 className="text-xl font-semibold text-dark-text mb-2">No resources found</h3>
          <p className="text-dark-muted">Try adjusting your search or filters</p>
        </div>
      )}

      {/* Quick Links Footer */}
      <div className="bg-dark-card/50 backdrop-blur-sm rounded-2xl border border-dark-border/50 p-6">
        <h3 className="font-semibold text-dark-text mb-4">Quick Access</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <a
            href="https://console.aws.amazon.com/securityhub"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-dark-muted hover:text-slyk-primary transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            AWS Security Hub
          </a>
          <a
            href="https://console.aws.amazon.com/bedrock"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-dark-muted hover:text-slyk-primary transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            Amazon Bedrock
          </a>
          <a
            href="https://console.aws.amazon.com/config"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-dark-muted hover:text-slyk-primary transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            AWS Config
          </a>
          <a
            href="https://console.aws.amazon.com/cloudtrail"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-dark-muted hover:text-slyk-primary transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            CloudTrail
          </a>
        </div>
      </div>
    </div>
  )
}

export default function KnowledgeBase() {
  const [activeTab, setActiveTab] = useState<'requirements' | 'architecture' | 'resources'>('requirements')

  return (
    <div className="min-h-screen bg-dark-bg p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto space-y-6"
      >
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-dark-text flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-slyk-primary" />
            Knowledge Base
          </h1>
          <p className="text-dark-muted mt-1">
            Security resources, documentation, and project requirements
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 border-b border-dark-border/50 pb-2">
          <button
            onClick={() => setActiveTab('requirements')}
            className={`flex items-center gap-2 px-6 py-3 rounded-t-xl transition-colors ${
              activeTab === 'requirements'
                ? 'bg-slyk-primary/20 text-slyk-primary border-b-2 border-slyk-primary'
                : 'text-dark-muted hover:text-dark-text'
            }`}
          >
            <ClipboardList className="w-5 h-5" />
            Requirements
          </button>
          <button
            onClick={() => setActiveTab('architecture')}
            className={`flex items-center gap-2 px-6 py-3 rounded-t-xl transition-colors ${
              activeTab === 'architecture'
                ? 'bg-slyk-primary/20 text-slyk-primary border-b-2 border-slyk-primary'
                : 'text-dark-muted hover:text-dark-text'
            }`}
          >
            <Network className="w-5 h-5" />
            Architecture & SOP
          </button>
          <button
            onClick={() => setActiveTab('resources')}
            className={`flex items-center gap-2 px-6 py-3 rounded-t-xl transition-colors ${
              activeTab === 'resources'
                ? 'bg-slyk-primary/20 text-slyk-primary border-b-2 border-slyk-primary'
                : 'text-dark-muted hover:text-dark-text'
            }`}
          >
            <BookOpen className="w-5 h-5" />
            Resources
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'requirements' && <RequirementsTab />}
        {activeTab === 'architecture' && <ArchitectureTab />}
        {activeTab === 'resources' && <ResourcesTab />}
      </motion.div>
    </div>
  )
}
