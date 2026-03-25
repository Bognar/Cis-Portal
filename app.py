import streamlit as st
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import tempfile
import os
import json
import re
from datetime import date

# --- HELPER FUNCTIONS ---

def clean_text(text):
    """Sanitizes text to prevent FPDF Unicode errors."""
    if not text: return ""
    replacements = {
        '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
        '\u2013': "-", '\u2014': "-", '\u2022': "*", '\u2122': "TM",
        '\u00ae': "(R)", '\u00a9': "(C)",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode('latin-1', 'replace').decode('latin-1').replace('?', '')

def save_uploaded_file(uploaded_file):
    """Saves streamlit upload to a temp path for FPDF."""
    if uploaded_file is not None:
        if hasattr(uploaded_file, 'getvalue'):
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                return tmp.name
        elif isinstance(uploaded_file, str) and os.path.exists(uploaded_file):
            return uploaded_file
    return None

# --- PDF CLASS ---

class CIS_Report(FPDF):
    def __init__(self, background_path=None, logo_path=None, client_name="", 
                 description="", consultant="", company="", report_date=""):
        super().__init__()
        self.background_path = background_path
        self.logo_path = logo_path
        self.client_name = clean_text(client_name)
        self.description = clean_text(description)
        self.consultant = clean_text(consultant)
        self.company = clean_text(company)
        self.report_date = str(report_date)

    def header(self):
        if self.page_no() > 1:
            self.set_font("helvetica", "I", 8)
            self.set_text_color(150)
            self.cell(0, 10, f"{self.client_name} - CIS Assessment", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def write_html_style(self, text, font_size=10):
        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                self.set_font("helvetica", "B", font_size)
                self.write(5, part.strip('**'))
            else:
                self.set_font("helvetica", "", font_size)
                self.write(5, part)

    def create_cover_page(self):
        self.add_page()
        if self.background_path: self.image(self.background_path, x=0, y=0, w=210, h=297)
        if self.logo_path: self.image(self.logo_path, x=80, y=40, w=50)
        self.set_y(120)
        self.set_font("helvetica", "B", 36)
        self.multi_cell(190, 15, self.client_name, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)
        self.set_font("helvetica", "", 16)
        self.multi_cell(190, 10, self.description, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_y(240)
        self.set_font("helvetica", "B", 12)
        self.cell(190, 7, f"Prepared by: {self.consultant}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("helvetica", "", 11)
        self.cell(190, 7, self.company, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(190, 7, f"Date: {self.report_date}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# --- MAIN APP ---

def main():
    st.set_page_config(page_title="CIS Report Generator", layout="wide")

    # 1. INITIALIZE SESSION STATE
    keys_to_init = {
        "meth_elements": [],
        "exec_elements": [],
        "history": [{"version": "1.0", "date": str(date.today()), "author": "", "desc": "Initial Draft"}],
        "contacts": [{"name": "", "role": "", "email": ""}],
        "customs": []
    }
    for key, val in keys_to_init.items():
        if key not in st.session_state: st.session_state[key] = val

    cis_info = {
        "Inventory and Control of Enterprise Assets": "Actively manage (inventory, track, and correct) all enterprise assets (end-user devices, including portable and mobile; network devices; non-computing/Internet of Things (IoT) devices; and servers) connected to the infrastructure physically, virtually, remotely, and those within cloud environments, to accurately know the totality of assets that need to be monitored and protected within the enterprise. This will also support identifying unauthorized and unmanaged assets to remove or remediate.",
        "Inventory and Control of Software Assets": "Actively manage (inventory, track, and correct) all software (operating systems and applications) on the network so that only authorized software is installed and can execute, and that unauthorized and unmanaged software is found and prevented from installation or execution.",
        "Data Protection": "Develop processes and technical controls to identify, classify, securely handle, retain, and dispose of data.",
        "Secure Configuration of Enterprise Assets and Software": "Establish and maintain the secure configuration of enterprise assets (end-user devices, including portable and mobile; network devices; non-computing/IoT devices; and servers) and software (operating systems and applications).",
        "Account Management": "Use processes and tools to assign and manage authorization to credentials for user accounts, including administrator accounts, as well as service accounts, to enterprise assets and software.",
        "Access Control Management": "Use processes and tools to create, assign, manage, and revoke access credentials and privileges for user, administrator, and service accounts for enterprise assets and software.",
        "Continuous Vulnerability Management": "Develop a plan to continuously assess and track vulnerabilities on all enterprise assets within the enterprise’s infrastructure, in order to remediate, and minimize, the window of opportunity for attackers. Monitor public and private industry sources for new threat and vulnerability information.",
        "Audit Log Management": "Collect, alert, review, and retain audit logs of events that could help detect, understand, or recover from an attack.",
        "Email and Web Browser Protections": "Improve protections and detections of threats from email and web vectors, as these are opportunities for attackers to manipulate human behavior through direct engagement.",
        "Malware Defenses": "Prevent or control the installation, spread, and execution of malicious applications, code, or scripts on enterprise assets.",
        "Data Recovery": "Establish and maintain data recovery practices sufficient to restore in-scope enterprise assets to a pre-incident and trusted state.",
        "Network Infrastructure Management": "Establish, implement, and actively manage (track, report, correct) network devices, in order to prevent attackers from exploiting vulnerable network services and access points.",
        "Network Monitoring and Defense": "Operate processes and tooling to establish and maintain comprehensive network monitoring and defense against security threats across the enterprise’s network infrastructure and user base.",
        "Security Awareness and Skill Training": "Establish and maintain a security awareness program to influence behavior among the workforce to be security conscious and properly skilled to reduce cybersecurity risks to the enterprise.",
        "Service Provider Management": "Develop a process to evaluate service providers who hold sensitive data, or are responsible for an enterprise’s critical IT platforms or processes, to ensure these providers are protecting those platforms and data appropriately.",
        "Application Software Security": "Manage the security life cycle of in-house developed, hosted, or acquired software to prevent, detect, and remediate security weaknesses before they can impact the enterprise.",
        "Incident Response Management": "Establish a program to develop and maintain an incident response capability (e.g., policies, plans, procedures, defined roles, training, and communications) to prepare, detect, and quickly respond to an attack.",
        "Penetration Testing": "Test the effectiveness and resiliency of enterprise assets through identifying and exploiting weaknesses in controls (people, processes, and technology), and simulating the objectives and actions of an attacker."
    }

    # 2. SIDEBAR - PROJECT MANAGEMENT
    st.sidebar.header("💾 Project Management")
    
    # Import
    uploaded_json = st.sidebar.file_uploader("Import Project (.json)", type=["json"])
    if uploaded_json and st.sidebar.button("Load Project"):
        data = json.load(uploaded_json)
        for k, v in data.items(): st.session_state[k] = v
        st.rerun()

    # Export (THE ADDED FEATURE)
    if st.sidebar.button("Prepare Export File"):
        # Filter session state to only include project data (exclude streamlit internal keys)
        export_data = {k: v for k, v in st.session_state.items() if not k.startswith("FormSubmitter") and k != "h_edit" and k != "c_edit"}
        # Note: Image bytes cannot be JSON serialized easily, so we notify user or skip them
        json_str = json.dumps(export_data, default=lambda x: None) 
        st.sidebar.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"{st.session_state.get('client_name', 'Project')}_config.json",
            mime="application/json"
        )

    st.sidebar.markdown("---")
    client_name = st.sidebar.text_input("Client Name", value=st.session_state.get("client_name", "Client name"), key="client_name")
    description = st.sidebar.text_area("Description", "CIS Controls Assessment")
    consultant = st.sidebar.text_input("Consultant", "John Doe")
    company = st.sidebar.text_input("Company", "My comapny name")
    report_date = st.sidebar.date_input("Date", date.today())
    logo = st.sidebar.file_uploader("Logo")
    bg = st.sidebar.file_uploader("Background")

    # 3. TABS
    tabs = st.tabs(["History & Contacts", "Methodology", "Executive Summary", "CIS Assessment", "Custom Sections"])

    with tabs[0]:
        st.subheader("Document Control")
        st.session_state.history = st.data_editor(st.session_state.history, num_rows="dynamic", key="h_edit")
        st.subheader("Contact List")
        st.session_state.contacts = st.data_editor(st.session_state.contacts, num_rows="dynamic", key="c_edit")

    # Methodology & Exec Summary
    for idx, (label, key) in enumerate([("Methodology", "meth_elements"), ("Executive Summary", "exec_elements")]):
        with tabs[idx+1]:
            c1, c2 = st.columns(2)
            if c1.button(f"+ Text ({label})"): st.session_state[key].append({"type": "text", "content": ""})
            if c2.button(f"+ Image ({label})"): st.session_state[key].append({"type": "image", "content": None})
            for i, el in enumerate(st.session_state[key]):
                if el["type"] == "text":
                    el["content"] = st.text_area(f"{label} Block {i+1}", value=el["content"], key=f"{key}_t_{i}")
                else:
                    el["content"] = st.file_uploader(f"{label} Img {i+1}", key=f"{key}_i_{i}")
                if st.button(f"Delete Block {i+1}", key=f"{key}_d_{i}"):
                    st.session_state[key].pop(i); st.rerun()

    with tabs[3]:
        for ctrl in cis_info.keys():
            with st.expander(f"Control: {ctrl}"):
                c1, c2 = st.columns(2)
                st.session_state[f"avg_{ctrl}"] = c1.number_input("Score", 0, 100, value=int(st.session_state.get(f"avg_{ctrl}", 0)), key=f"s_{ctrl}")
                st.session_state[f"ind_{ctrl}"] = c2.number_input("Industry Avg", 0, 100, value=int(st.session_state.get(f"ind_{ctrl}", 0)), key=f"ia_{ctrl}")
                st.session_state[f"find_{ctrl}"] = st.text_area("Findings", value=st.session_state.get(f"find_{ctrl}", ""), key=f"f_{ctrl}")
                st.session_state[f"recom_{ctrl}"] = st.text_area("Recommendations", value=st.session_state.get(f"recom_{ctrl}", ""), key=f"r_{ctrl}")

    with tabs[4]:
        st.subheader("Additional Custom Sections")
        if st.button("+ Add New Custom Section"):
            st.session_state.customs.append({"title": "New Section", "elements": []})
            st.rerun()

        for s_idx, section in enumerate(st.session_state.customs):
            with st.expander(f"Section: {section['title']}", expanded=True):
                section["title"] = st.text_input(f"Section Title {s_idx}", value=section["title"], key=f"cust_title_{s_idx}")
                
                col1, col2, col3 = st.columns([1,1,1])
                if col1.button(f"+ Text (Section {s_idx})"): section["elements"].append({"type": "text", "content": ""})
                if col2.button(f"+ Image (Section {s_idx})"): section["elements"].append({"type": "image", "content": None})
                if col3.button(f"🗑️ Delete Full Section", key=f"del_sec_{s_idx}"):
                    st.session_state.customs.pop(s_idx); st.rerun()

                for e_idx, el in enumerate(section["elements"]):
                    if el["type"] == "text":
                        el["content"] = st.text_area(f"Text Block {s_idx}_{e_idx}", value=el["content"], key=f"cust_{s_idx}_t_{e_idx}")
                    else:
                        el["content"] = st.file_uploader(f"Image Block {s_idx}_{e_idx}", key=f"cust_{s_idx}_i_{e_idx}")
                    
                    if st.button(f"Delete Block {e_idx+1}", key=f"cust_{s_idx}_del_{e_idx}"):
                        section["elements"].pop(e_idx); st.rerun()

    # 4. GENERATION
    if st.button("🚀 Generate Final Report", type="primary"):
        bg_p, logo_p = save_uploaded_file(bg), save_uploaded_file(logo)
        pdf = CIS_Report(bg_p, logo_p, client_name, description, consultant, company, report_date)
        pdf.create_cover_page()
        temp_paths = []

        # Document Control Table
        pdf.add_page()
        pdf.set_font("helvetica", "B", 18); pdf.cell(0, 10, "Document Control", new_x=XPos.LMARGIN, new_y=YPos.NEXT); pdf.ln(5)
        pdf.set_fill_color(229, 174, 34); pdf.set_font("helvetica", "B", 10)
        pdf.cell(30, 10, "Version", 1, 0, "C", True); pdf.cell(40, 10, "Date", 1, 0, "C", True)
        pdf.cell(50, 10, "Author", 1, 0, "C", True); pdf.cell(70, 10, "Description", 1, 1, "C", True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", "", 10)
        for row in st.session_state.history:
            pdf.cell(30, 10, clean_text(str(row.get('version', ''))), 1, 0, "C")
            pdf.cell(40, 10, clean_text(str(row.get('date', ''))), 1, 0, "C")
            pdf.cell(50, 10, clean_text(str(row.get('author', ''))), 1, 0, "L")
            pdf.cell(70, 10, clean_text(str(row.get('desc', ''))), 1, 1, "L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Contact List Table
        pdf.ln(10); pdf.set_font("helvetica", "B", 18); pdf.cell(0, 10, "Contact List", new_x=XPos.LMARGIN, new_y=YPos.NEXT); pdf.ln(5)
        pdf.set_fill_color(229, 174, 34); pdf.set_font("helvetica", "B", 10)
        pdf.cell(60, 10, "Name", 1, 0, "C", True); pdf.cell(60, 10, "Role", 1, 0, "C", True)
        pdf.cell(70, 10, "Email", 1, 1, "C", True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", "", 10)
        for con in st.session_state.contacts:
            pdf.cell(60, 10, clean_text(str(con.get('name', ''))), 1, 0, "L")
            pdf.cell(60, 10, clean_text(str(con.get('role', ''))), 1, 0, "L")
            pdf.cell(70, 10, clean_text(str(con.get('email', ''))), 1, 1, "L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        section_num = 1
        # Methodology & Exec Summary
        for title, key in [("Methodology", "meth_elements"), ("Executive Summary", "exec_elements")]:
            pdf.add_page(); pdf.set_font("helvetica", "B", 20); pdf.cell(0, 15, f"{section_num}. {title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            for el in st.session_state[key]:
                if el["type"] == "text" and el["content"]: pdf.write_html_style(clean_text(el["content"]), 11); pdf.ln(8)
                elif el["type"] == "image" and el["content"]:
                    p = save_uploaded_file(el["content"]); temp_paths.append(p); pdf.image(p, w=170); pdf.ln(5)
            section_num += 1

        # CIS Assessment
        pdf.add_page(); pdf.set_font("helvetica", "B", 20); pdf.cell(0, 15, f"{section_num}. CIS Control Assessments", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        for ctrl, d_text in cis_info.items():
            if pdf.get_y() > 200: pdf.add_page()
            pdf.set_fill_color(229, 174, 34); pdf.set_font("helvetica", "B", 12); pdf.cell(0, 10, f" {ctrl}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_fill_color(245, 245, 245); pdf.set_font("helvetica", "B", 10); pdf.cell(95, 8, f" Client Score: {st.session_state.get(f'avg_{ctrl}',0)}/100", border="B", fill=True)
            pdf.cell(95, 8, f" Industry Avg: {st.session_state.get(f'ind_{ctrl}',0)}/100", border="B", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2); pdf.set_font("helvetica", "I", 9); pdf.set_text_color(80); pdf.multi_cell(190, 5, f"Description: {clean_text(d_text)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(0); pdf.ln(2); pdf.set_font("helvetica", "B", 10); pdf.cell(0, 8, "Findings:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.write_html_style(clean_text(st.session_state.get(f"find_{ctrl}", "No findings.")), 10); pdf.ln(8)
            pdf.set_font("helvetica", "B", 10); pdf.cell(0, 8, "Recommendations:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.write_html_style(clean_text(st.session_state.get(f"recom_{ctrl}", "No recommendations.")), 10); pdf.ln(12)
        section_num += 1

        # Custom Sections
        for custom_sec in st.session_state.customs:
            pdf.add_page(); pdf.set_font("helvetica", "B", 20); pdf.cell(0, 15, f"{section_num}. {clean_text(custom_sec['title'])}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            for el in custom_sec["elements"]:
                if el["type"] == "text" and el["content"]: pdf.write_html_style(clean_text(el["content"]), 11); pdf.ln(8)
                elif el["type"] == "image" and el["content"]:
                    p = save_uploaded_file(el["content"]); temp_paths.append(p); pdf.image(p, w=170); pdf.ln(5)
            section_num += 1

        pdf_bytes = pdf.output()
        for p in [bg_p, logo_p] + temp_paths: 
            if p and os.path.exists(p): os.remove(p)
        st.download_button("Download PDF", bytes(pdf_bytes), f"{client_name}_Report.pdf")

if __name__ == "__main__":
    main()