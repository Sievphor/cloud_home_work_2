import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import os

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def create_report():
    doc = docx.Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Title / Header
    p_uni = doc.add_paragraph()
    p_uni.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_uni = p_uni.add_run("សាកលវិទ្យាល័យ សៅស៍អុីសថ៍អេយេសៀ\nUNIVERSITY OF SOUTH-EAST ASIA\n")
    r_uni.font.name = 'Khmer OS Battambang'
    r_uni.font.size = Pt(14)
    r_uni.bold = True
    r_uni.font.color.rgb = RGBColor(16, 44, 87)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("Homework 2\nCI/CD WITH JENKINS, GITHUB, DOCKER, AMAZON ECR AND DOCKER SWARM ON AWS EC2\n")
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(16)
    r_title.bold = True
    r_title.font.color.rgb = RGBColor(37, 99, 235)

    # Info Box Table
    info_table = doc.add_table(rows=6, cols=2)
    info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_data = [
        ("Course:", "Advanced Cloud Technology"),
        ("Lecturer:", "Mr. Krol Noeurn"),
        ("Student Name:", "TONN Sievphor"),
        ("GitHub Repository:", "https://github.com/Sievphor/cloud_home_work_2.git"),
        ("Amazon ECR URI:", "908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework2"),
        ("Academic Year:", "2026 - 2027")
    ]
    for i, (k, v) in enumerate(info_data):
        row = info_table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.text = k
        c1.text = v
        c0.paragraphs[0].runs[0].font.bold = True
        c0.paragraphs[0].runs[0].font.name = 'Calibri'
        c1.paragraphs[0].runs[0].font.name = 'Calibri'
        c0.width = Inches(2.2)
        c1.width = Inches(4.2)
        set_cell_background(c0, "F1F5F9")
        set_cell_background(c1, "F8FAFC")

    doc.add_page_break()

    def add_section_h1(text):
        h = doc.add_paragraph()
        r = h.add_run(text)
        r.font.name = 'Khmer OS Battambang'
        r.font.size = Pt(13)
        r.bold = True
        r.font.color.rgb = RGBColor(30, 58, 138)
        return h

    def add_body_p(text):
        p = doc.add_paragraph()
        r = p.add_run(text)
        r.font.name = 'Khmer OS Battambang'
        r.font.size = Pt(10.5)
        p.paragraph_format.line_spacing = 1.15
        return p

    # 1. Introduction
    add_section_h1("១. សេចក្តីផ្តើម (Introduction)")
    add_body_p(
        "គម្រោងនេះមានគោលបំណងបង្កើតប្រព័ន្ធ Continuous Integration និង Continuous Deployment (CI/CD) "
        "ដោយប្រើប្រាស់ GitHub, Jenkins, Docker, Amazon ECR និង Docker Swarm នៅលើ Amazon EC2។ "
        "នៅពេលអ្នកអភិវឌ្ឍន៍ (Developer) Push Code ថ្មីទៅកាន់ GitHub Repository (https://github.com/Sievphor/cloud_home_work_2.git) នោះ Jenkins នឹងធ្វើការទាញយកកូដ "
        "សាងសង់ Docker Image, បញ្ជូន Image ទៅកាន់ Amazon ECR ហើយធ្វើការ Deploy ទៅកាន់ Docker Swarm Cluster ដោយស្វ័យប្រវត្តិ។"
    )

    # 2. Architecture
    add_section_h1("២. ស្ថាបត្យកម្មប្រព័ន្ធ (System Architecture)")
    add_body_p(
        "ប្រព័ន្ធត្រូវបានរៀបចំឡើងជាលំហូរស្វ័យប្រវត្តិកម្មដូចខាងក្រោម៖\n"
        "• Developer Push Source Code ទៅកាន់ GitHub Repository (cloud_home_work_2)\n"
        "• GitHub Webhook ផ្ញើសញ្ញា Trigger ទៅកាន់ Jenkins Pipeline\n"
        "• Jenkins Login ទៅកាន់ AWS ECR តាមរយៈ aws ecr get-login-password\n"
        "• Jenkins Build Docker Image ជាមួយទង់ --platform linux/amd64 និងបំពាក់ Tag តាមលេខ Build និង Git Commit SHA\n"
        "• Jenkins Push Image ទៅកាន់ Amazon Elastic Container Registry (ECR URI: 908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework2)\n"
        "• Jenkins ភ្ជាប់តាម SSH ទៅកាន់ Swarm Manager (13.220.98.249) នៅលើ Amazon EC2\n"
        "• Swarm Manager ដំណើរការ docker stack deploy --with-registry-auth និងធ្វើ Rolling Update នៅលើ Replicas ទាំង ៣ "
        "(Manager: 13.220.98.249:8898, Worker 1: 34.229.219.41:8898, Worker 2: 54.90.208.206:8898)។"
    )

    # 3. Implementation Steps
    add_section_h1("៣. ការអនុវត្តការងារជាក់ស្តែង (Implementation Steps)")
    add_body_p(
        "ជំហានទី ១៖ បង្កើត GitHub Repository\n"
        "បានបង្កើត Repository ឈ្មោះ 'cloud_home_work_2' សម្រាប់ផ្ទុក Application Source Code, Dockerfile, Jenkinsfile, docker-stack.yml និង README.md "
        "ព្រមទាំងកំណត់ .gitignore មិនឱ្យរុញ Credentials ឬ Secrets ចូលទៅក្នុង Git ឡើយ។"
    )
    add_body_p(
        "ជំហានទី ២៖ បង្កើត Dockerfile និងសាកល្បងនៅលើ Local Machine\n"
        "បានជ្រើសរើស Base Image 'nginx:alpine' ដែលមានទំហំតូច និងដំណើរការលឿន។ "
        "បានសាកល្បង docker build និង docker run នៅលើ Local ឃើញថាកម្មវិធីដំណើរការបានយ៉ាងត្រឹមត្រូវនៅលើ Port 8898។"
    )
    add_body_p(
        "ជំហានទី ៣៖ បង្កើត Amazon ECR Private Repository\n"
        "បានបង្កើត Private Repository នៅលើ Amazon ECR ក្នុង Region us-east-1 ឈ្មោះ 'sievphor-homework2' "
        "(URI: 908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework2) សម្រាប់ផ្ទុក Docker Images ដែលបាន Build ចេញពី Jenkins។"
    )
    add_body_p(
        "ជំហានទី ៤៖ កំណត់រចនាសម្ព័ន្ធ Jenkins Pipeline & Webhook\n"
        "បានដំឡើង Jenkins Pipeline Job ដោយប្រើ Jenkinsfile (Pipeline as Code)។ "
        "បានកំណត់ GitHub Webhook ដើម្បីឱ្យ Jenkins ចាប់ផ្តើម Build ដោយស្វ័យប្រវត្តិរាល់ពេលមាន Commit ថ្មីនៅលើ Branch main។"
    )
    add_body_p(
        "ជំហានទី ៥៖ បង្កើត Docker Swarm Cluster នៅលើ AWS EC2\n"
        "បានបង្កើត EC2 Instances ចំនួន ៣ រួមមាន 1 Manager Node (13.220.98.249) និង 2 Worker Nodes (34.229.219.41, 54.90.208.206)។ "
        "នៅលើ Manager បានដំណើរការ 'docker swarm init' ហើយនៅលើ Workers បានដំណើរការ 'docker swarm join'។ "
        "ការត្រួតពិនិត្យតាមរយៈ 'docker node ls' បង្ហាញថាក្នាំង Node ទាំងបីស្ថិតក្នុងស្ថានភាព Ready។"
    )
    add_body_p(
        "ជំហានទី ៦៖ Deploy Application ទៅកាន់ Docker Swarm\n"
        "Jenkins បានចម្លងឯកសារ docker-stack-deploy.yml ទៅកាន់ Manager Node ហើយដំណើរការ:\n"
        "sudo docker stack deploy --with-registry-auth -c /tmp/docker-stack-deploy.yml homework2\n"
        "សេវាកម្មត្រូវបានបង្កើតឡើងដោយជោគជ័យជាមួយ Replicas ចំនួន ៣ រត់ចែកគ្នានៅលើគ្រប់ Nodes។"
    )
    add_body_p(
        "ជំហានទី ៧៖ ផ្ទៀងផ្ទាត់ Service និង Rolling Update\n"
        "បានត្រួតពិនិត្យតាមរយៈ 'docker service ls' និង 'docker service ps homework2_web'។ "
        "នៅពេលធ្វើការ Push កូដថ្មី Swarm បានធ្វើបច្ចុប្បន្នភាពតាម rolling update (update_config: parallelism 1, delay 10s) "
        "ដោយមិនមានការធ្លាក់ចុះនៃសេវាកម្ម (Zero Downtime) ឡើយ។"
    )
    add_body_p(
        "ជំហានទី ៨៖ ការចូលប្រើប្រាស់ផ្ទាល់ (Live Verification)\n"
        "កម្មវិធីអាចចូលប្រើប្រាស់បានតាមរយៈ Public IP របស់ Manager និង Workers លើ Port 8898៖\n"
        "• Manager: http://13.220.98.249:8898\n"
        "• Worker 1: http://34.229.219.41:8898\n"
        "• Worker 2: http://54.90.208.206:8898\n"
        "តាមរយៈ Ingress Routing Mesh របស់ Docker Swarm។"
    )

    # 4. Results
    add_section_h1("៤. លទ្ធផលទទួលបាន (Results)")
    add_body_p(
        "លទ្ធផលបង្ហាញថា Jenkins CI/CD Pipeline ដំណើរការដោយរលូនទាំងស្រុង ចាប់តាំងពីការទាញយកកូដ, "
        "ការ Build/Push Image ទៅកាន់ Amazon ECR រហូតដល់ការ Deploy ដោយស្វ័យប្រវត្តិលើ Docker Swarm Cluster។ "
        "កម្មវិធីឆ្លើយតបយ៉ាងត្រឹមត្រូវលើ Browser តាមរយៈ Port 8898 ហើយ Replicas ទាំង ៣ រត់ចែកគ្នានៅលើ Manager និង Worker Nodes។"
    )

    # 5. Conclusion
    add_section_h1("៥. សេចក្តីសន្និដ្ឋាន (Conclusion)")
    add_body_p(
        "ការអនុវត្ត Homework 2 នេះបានផ្តល់នូវការយល់ដឹងស៊ីជម្រៅលើការរៀបចំ CI/CD Pipeline ក្នុងកម្រិត Production "
        "ដោយរួមបញ្ចូលគ្នារវាង GitHub Webhook, Jenkinsfile, Amazon ECR និង Docker Swarm Orchestration។ "
        "បច្ចេកវិទ្យាទាំងនេះជួយកាត់បន្ថយកំហុសរបស់មនុស្ស (Human Errors), បង្កើនល្បឿនក្នុងការបញ្ចេញកម្មវិធី "
        "និងធានានូវ High Availability សម្រាប់សេវាកម្មនៅលើ Cloud។"
    )

    output_path = os.path.join(os.path.dirname(__file__), "TONN-Sievphor-Documentation_homework2.docx")
    doc.save(output_path)
    print(f"Successfully generated: {output_path}")

if __name__ == "__main__":
    create_report()
