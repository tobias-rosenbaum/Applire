# Sample CV Generation Instructions

This document describes how the sample CV for testing was created.

## Persona: Marcus Chen

### Personal Details
- **Full Name**: Marcus Chen
- **Email**: marcus.chen.example@email.com
- **Phone**: +49 30 12345678
- **Location**: Berlin, Germany
- **LinkedIn**: linkedin.com/in/marcus-chen-example

### Professional Summary
Senior Software Engineer with 8+ years of experience building scalable web applications. Expert in Python, React, and cloud infrastructure. Passionate about clean code, mentoring teams, and delivering high-impact products.

### Work Experience

1. **Senior Software Engineer** | TechVentures GmbH, Berlin (2021 - Present)
   - Led development of microservices architecture serving 1M+ users
   - Reduced deployment time by 60% through CI/CD improvements
   - Mentored team of 5 junior developers

2. **Software Engineer** | DataFlow AG, Munich (2018 - 2021)
   - Built real-time data processing pipelines using Python and Apache Kafka
   - Implemented REST APIs handling 100K+ daily requests
   - Improved database performance by 40% through query optimization

3. **Junior Developer** | StartupX, Berlin (2016 - 2018)
   - Developed features for e-commerce platform using React and Node.js
   - Wrote unit and integration tests achieving 85% code coverage

### Education
- **M.S. Computer Science** | TU Berlin (2014 - 2016)
  - Focus: Distributed Systems
- **B.S. Computer Science** | University of Hamburg (2010 - 2014)

### Skills
- **Languages**: Python, JavaScript/TypeScript, Go, SQL
- **Frameworks**: Django, FastAPI, React, Next.js
- **Cloud**: AWS (EC2, S3, Lambda, RDS), Kubernetes, Docker
- **Databases**: PostgreSQL, MongoDB, Redis
- **Tools**: Git, CI/CD (GitHub Actions, Jenkins), Terraform

## CV Generation

The CV was generated using ReportLab Python library to create a PDF that:
- Has realistic content and structure
- Is machine-readable for profile extraction
- Contains diverse skills and experiences for gap analysis testing

## Usage in Tests

This CV is used to test:
1. CV upload functionality
2. Profile extraction and parsing
3. Gap analysis against job descriptions
4. Download of processed profiles

## Notes

- This is a **fictional persona** - no real person's information is used
- The email and phone are obviously fake for testing purposes
- Skills and experience are designed to partially match the sample JD
