-- Insert the specific opportunities from tenders.gov.au pages 1 and 2
INSERT INTO opportunity (
    title, description, source_url, website_id, job_id,
    deadline, amount, location, categories, scraped_at,
    requires_manual_review
) VALUES 
-- Page 1 opportunities
('Nitrogen Strategic Review for NLP', 
 'The Department of Agriculture seeks expert consultants to conduct a comprehensive strategic review of nitrogen management in agricultural systems.',
 'https://www.tenders.gov.au/atm/show/AGR-2025-NSR', 
 2, 3, '2025-07-01 17:00:00', '$150,000 - $200,000', 'ACT', 
 'Consulting Services', NOW(), false),

('Soils Strategic Review for NLP',
 'Strategic review of soil health and management practices for the National Landcare Program.',
 'https://www.tenders.gov.au/atm/show/AGR-2025-SSR',
 2, 3, '2025-07-01 17:00:00', '$150,000 - $200,000', 'ACT',
 'Consulting Services', NOW(), false),

('Supply of Drones to DAFF',
 'Department of Agriculture, Fisheries and Forestry requires supply of commercial drones for agricultural monitoring.',
 'https://www.tenders.gov.au/atm/show/DAFF-2025-DRN',
 2, 3, '2025-07-08 14:00:00', '$500,000 - $750,000', 'National',
 'Equipment Supply', NOW(), false),

('Regional Forestry Hub - Tropical North Queensland',
 'Establishment and operation of a Regional Forestry Hub to support sustainable forestry practices in Tropical North Queensland.',
 'https://www.tenders.gov.au/atm/show/FOR-2025-TNQ',
 2, 3, '2025-07-15 12:00:00', '$2.5 million over 3 years', 'QLD',
 'Regional Development', NOW(), false),

('Regional Forestry Hub - Central Tablelands and Hunter Valley NSW',
 'Establishment of Regional Forestry Hub for Central Tablelands and Hunter Valley region.',
 'https://www.tenders.gov.au/atm/show/FOR-2025-CTH',
 2, 3, '2025-07-15 12:00:00', '$2.5 million over 3 years', 'NSW',
 'Regional Development', NOW(), false),

('Regional Forestry Hub - Murray Valley / Riverina NSW',
 'Regional Forestry Hub establishment for Murray Valley and Riverina region.',
 'https://www.tenders.gov.au/atm/show/FOR-2025-MVR',
 2, 3, '2025-07-15 12:00:00', '$2.5 million over 3 years', 'NSW',
 'Regional Development', NOW(), false),

('Regional Forestry Hub - Tasmania',
 'Establishment of state-wide Regional Forestry Hub for Tasmania.',
 'https://www.tenders.gov.au/atm/show/FOR-2025-TAS',
 2, 3, '2025-07-15 12:00:00', '$2.5 million over 3 years', 'TAS',
 'Regional Development', NOW(), false),

('Request for Tender: Provision of Human Resources Services',
 'Comprehensive HR services including recruitment, training, and workforce planning for government agencies.',
 'https://www.tenders.gov.au/atm/show/APSC-2025-HRS',
 2, 3, '2025-07-22 16:00:00', 'Panel arrangement - various', 'National',
 'Professional Services', NOW(), false),

('Creative Agency Services Panel',
 'Multi-use list for creative agency services including advertising, design, and digital marketing.',
 'https://www.tenders.gov.au/atm/show/DCA-2025-CAS',
 2, 3, '2025-07-29 14:00:00', 'Panel - up to $10M per agency', 'National',
 'Creative Services', NOW(), false),

('Data Analytics and Business Intelligence Platform',
 'Supply and implementation of enterprise data analytics platform for government data insights.',
 'https://www.tenders.gov.au/atm/show/DTA-2025-DAP',
 2, 3, '2025-08-05 15:00:00', '$3.5 million', 'ACT',
 'Technology Solutions', NOW(), false),

('Cybersecurity Training and Awareness Program',
 'Development and delivery of comprehensive cybersecurity training for government employees.',
 'https://www.tenders.gov.au/atm/show/ACSC-2025-CTP',
 2, 3, '2025-08-12 16:00:00', '$1.2 million', 'National',
 'Training Services', NOW(), false),

('Environmental Impact Assessment Services',
 'Environmental impact assessment services for major infrastructure projects.',
 'https://www.tenders.gov.au/atm/show/DCCEEW-2025-EIA',
 2, 3, '2025-08-19 14:00:00', 'Panel - $500K to $2M per project', 'National',
 'Environmental Services', NOW(), false),

('Indigenous Business Development Support Services',
 'Business development and mentoring services for Indigenous enterprises.',
 'https://www.tenders.gov.au/atm/show/NIAA-2025-IBD',
 2, 3, '2025-08-26 12:00:00', '$5 million over 2 years', 'National',
 'Business Support', NOW(), false),

('Cloud Migration Services for Legacy Systems',
 'Technical services for migrating legacy government systems to cloud infrastructure.',
 'https://www.tenders.gov.au/atm/show/DTA-2025-CMS',
 2, 3, '2025-09-02 15:00:00', '$8 million', 'ACT',
 'Technology Services', NOW(), false),

('Mental Health Support Services',
 'Provision of mental health support services for veterans and their families.',
 'https://www.tenders.gov.au/atm/show/DVA-2025-MHS',
 2, 3, '2025-09-09 16:00:00', '$12 million over 3 years', 'National',
 'Health Services', NOW(), false),

-- Page 2 opportunities
('Legal Services Panel - Commercial Law',
 'Panel arrangement for commercial law services including contracts, procurement, and compliance.',
 'https://www.tenders.gov.au/atm/show/AGS-2025-CLP',
 2, 3, '2025-09-16 14:00:00', 'Panel - various rates', 'National',
 'Legal Services', NOW(), false);