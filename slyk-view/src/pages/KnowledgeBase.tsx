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
  FolderOpen
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

export default function KnowledgeBase() {
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
            Security resources, documentation, and reference materials for ISSOs
          </p>
        </div>

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
      </motion.div>
    </div>
  )
}
