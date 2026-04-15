// ==============================================================================
// cekwajar.id — Seed Job Categories
// Seeds 50 common Indonesian job categories into job_categories table
// ==============================================================================

import { createClient } from '../src/lib/supabase/server'

const JOB_CATEGORIES = [
  // Technology
  'Software Engineer',
  'Backend Developer',
  'Frontend Developer',
  'Full Stack Developer',
  'Data Analyst',
  'Data Scientist',
  'IT Support',
  'Network Engineer',
  'System Administrator',

  // Product & Project
  'Product Manager',
  'Project Manager',

  // Design
  'UI/UX Designer',
  'Graphic Designer',
  'Interior Designer',
  'Architect',

  // HR & Admin
  'HRD Officer',
  'HR Manager',
  'Recruitment Specialist',
  'General Affairs',
  'Office Manager',

  // Finance & Accounting
  'Finance Staff',
  'Accounting Staff',
  'Tax Consultant',
  'Financial Analyst',

  // Marketing & Sales
  'Marketing Staff',
  'Digital Marketing',
  'Content Creator',
  'SEO Specialist',
  'Sales Executive',
  'Business Development',
  'Account Manager',
  'Copywriter',
  'Content Writer',
  'Journalist',

  // Customer Service
  'Customer Service',
  'Customer Success',

  // Operations & Supply Chain
  'Operations Manager',
  'Supply Chain Staff',
  'Logistics Coordinator',
  'Procurement Staff',
  'Purchasing Staff',

  // Legal & Compliance
  'Legal Officer',
  'Compliance Officer',

  // Education
  'Teacher',
  'Lecturer',
  'Education Staff',

  // Healthcare
  'Nurse',
  'Pharmacist',
  'Medical Staff',

  // Engineering
  'Civil Engineer',
  'Mechanical Engineer',
  'Electrical Engineer',
]

function deriveIndustry(title: string): string {
  const techKeywords = ['software', 'backend', 'frontend', 'full stack', 'data', 'it ', 'network', 'system']
  const designKeywords = ['design', 'graphic', 'interior', 'architect']
  const hrKeywords = ['hrd', 'hr ', 'recruitment', 'general affairs', 'office manager']
  const financeKeywords = ['finance', 'accounting', 'tax', 'financial']
  const marketingKeywords = ['marketing', 'digital', 'content', 'seo', 'sales', 'business', 'account', 'copywriter', 'writer', 'journalist']
  const customerKeywords = ['customer', 'service', 'success']
  const opsKeywords = ['operations', 'supply chain', 'logistics', 'procurement', 'purchasing']
  const legalKeywords = ['legal', 'compliance']
  const educationKeywords = ['teacher', 'lecturer', 'education']
  const healthKeywords = ['nurse', 'pharmacist', 'medical']
  const engineerKeywords = ['engineer', 'civil', 'mechanical', 'electrical']

  const lower = title.toLowerCase()

  if (techKeywords.some(k => lower.includes(k))) return 'Technology'
  if (designKeywords.some(k => lower.includes(k))) return 'Design'
  if (hrKeywords.some(k => lower.includes(k))) return 'Human Resources'
  if (financeKeywords.some(k => lower.includes(k))) return 'Finance & Accounting'
  if (marketingKeywords.some(k => lower.includes(k))) return 'Marketing & Sales'
  if (customerKeywords.some(k => lower.includes(k))) return 'Customer Service'
  if (opsKeywords.some(k => lower.includes(k))) return 'Operations & Supply Chain'
  if (legalKeywords.some(k => lower.includes(k))) return 'Legal & Compliance'
  if (educationKeywords.some(k => lower.includes(k))) return 'Education'
  if (healthKeywords.some(k => lower.includes(k))) return 'Healthcare'
  if (engineerKeywords.some(k => lower.includes(k))) return 'Engineering'

  return 'General'
}

async function seed() {
  const supabase = await createClient()

  console.log('Seeding job categories...')

  const records = JOB_CATEGORIES.map(title => ({
    title,
    title_normalized: title.toLowerCase().trim(),
    industry: deriveIndustry(title),
    is_active: true,
  }))

  // Upsert to handle re-runs gracefully
  const { error } = await supabase
    .from('job_categories')
    .upsert(records, { onConflict: 'title' })

  if (error) {
    console.error('Error seeding job categories:', error)
    process.exit(1)
  }

  console.log(`Successfully seeded ${records.length} job categories`)

  // Verify
  const { count } = await supabase
    .from('job_categories')
    .select('*', { count: 'exact', head: true })

  console.log(`Total job categories in database: ${count}`)
}

seed()
  .then(() => process.exit(0))
  .catch(err => {
    console.error('Seed failed:', err)
    process.exit(1)
  })
